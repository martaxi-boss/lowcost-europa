import fcntl
import os
import multiprocessing
import tempfile
import threading
import time
from email.message import Message
from pathlib import Path
from unittest.mock import Mock, patch
from urllib import error

from django.test import SimpleTestCase

from apps.integrations.aliexpress.client import (
    DEFAULT_CADENCE_PATH,
    DEFAULT_LOCK_PATH,
    AliExpressClient,
    _LocalOperationLock,
)
from apps.integrations.aliexpress.config import AliExpressConfig
from apps.integrations.aliexpress.exceptions import (
    AliExpressAuthenticationError,
    AliExpressConfigurationError,
    AliExpressRateLimitError,
    AliExpressResponseError,
    AliExpressRuntimeStateError,
    AliExpressTransportError,
)


class FakeResponse:
    def __init__(self, body='{"demo_method_response":{"result":{"ok":true}}}'):
        self.body = body.encode()

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self.body


def _hold_operation_lock(lock_path, ready, release):
    with _LocalOperationLock(lock_path, 1.0, time.monotonic, time.sleep):
        ready.set()
        release.wait(5)


def _try_operation_lock(lock_path, result):
    try:
        with _LocalOperationLock(lock_path, 0.15, time.monotonic, time.sleep):
            result.put("acquired")
    except AliExpressTransportError:
        result.put("blocked")


def _write_cadence_state(cadence_path, now_value):
    cfg = AliExpressConfig(
        app_key="k",
        app_secret="s",
        tracking_id="t",
        min_interval_seconds=1.0,
    )
    client = AliExpressClient(
        cfg,
        opener=lambda *_a, **_k: FakeResponse(),
        sleeper=lambda _s: None,
        wall_clock=lambda: now_value,
        cadence_path=cadence_path,
        lock_path=cadence_path + ".lock",
    )
    client._pace()


def _read_shared_cadence_state(cadence_path, now_value, result):
    clock = {"now": now_value}

    def wall_clock():
        return clock["now"]

    def sleeper(seconds):
        result.put(seconds)
        clock["now"] += seconds

    cfg = AliExpressConfig(
        app_key="k",
        app_secret="s",
        tracking_id="t",
        min_interval_seconds=1.0,
    )
    client = AliExpressClient(
        cfg,
        opener=lambda *_a, **_k: FakeResponse(),
        sleeper=sleeper,
        wall_clock=wall_clock,
        cadence_path=cadence_path,
        lock_path=cadence_path + ".lock",
    )
    client._pace()


def http_error(code, retry_after=None):
    headers = Message()
    if retry_after is not None:
        headers["Retry-After"] = str(retry_after)
    return error.HTTPError("https://example.test", code, "error", headers, None)


class SafetyClientTests(SimpleTestCase):
    def make_client(self, opener, **overrides):
        cfg = AliExpressConfig(
            app_key="fake-key",
            app_secret="fake-secret",
            tracking_id="fake-tracking",
            timeout_seconds=1,
            max_retries=overrides.pop("max_retries", 2),
            min_interval_seconds=overrides.pop("min_interval_seconds", 0),
            backoff_base_seconds=overrides.pop("backoff_base_seconds", 1),
            backoff_max_seconds=overrides.pop("backoff_max_seconds", 30),
            jitter_max_seconds=overrides.pop("jitter_max_seconds", 0),
            max_retry_after_seconds=overrides.pop("max_retry_after_seconds", 60),
            max_consecutive_429=overrides.pop("max_consecutive_429", 3),
            lock_timeout_seconds=overrides.pop("lock_timeout_seconds", 1),
        )
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        return AliExpressClient(
            cfg,
            opener=opener,
            sleeper=overrides.pop("sleeper", lambda _s: None),
            wall_clock=overrides.pop("wall_clock", lambda: 1000.0),
            jitter_source=overrides.pop("jitter_source", lambda _a, _b: 0.0),
            lock_path=str(base / "lock"),
            cadence_path=str(base / "cadence"),
            **overrides,
        )

    def test_429_retry_after_is_respected_then_success(self):
        sleeps = []
        calls = 0

        def opener(*_a, **_k):
            nonlocal calls
            calls += 1
            if calls == 1:
                raise http_error(429, 7)
            return FakeResponse()

        c = self.make_client(opener, sleeper=sleeps.append)
        c._call("demo.method")
        self.assertEqual(calls, 2)
        self.assertEqual(sleeps, [7.0])
        self.assertEqual(c.last_call_metrics.retries, 1)

    def test_429_without_retry_after_uses_backoff_and_jitter(self):
        sleeps = []
        calls = 0

        def opener(*_a, **_k):
            nonlocal calls
            calls += 1
            if calls == 1:
                raise http_error(429)
            return FakeResponse()

        c = self.make_client(opener, sleeper=sleeps.append, jitter_source=lambda _a, _b: 0.25)
        c._call("demo.method")
        self.assertEqual(sleeps, [1.25])

    def test_repeated_429_aborts_at_cooldown_limit(self):
        c = self.make_client(
            lambda *_a, **_k: (_ for _ in ()).throw(http_error(429)),
            max_retries=5,
            max_consecutive_429=3,
        )
        with self.assertRaises(AliExpressRateLimitError):
            c._call("demo.method")
        self.assertEqual(c.last_call_metrics.attempts, 3)
        self.assertTrue(c.last_call_metrics.rate_limit_abort)

    def test_retry_after_is_capped(self):
        sleeps = []
        calls = 0

        def opener(*_a, **_k):
            nonlocal calls
            calls += 1
            if calls == 1:
                raise http_error(429, 999)
            return FakeResponse()

        self.make_client(opener, sleeper=sleeps.append, max_retry_after_seconds=5)._call(
            "demo.method"
        )
        self.assertEqual(sleeps, [5.0])

    def test_5xx_retries_are_limited(self):
        for status in (500, 502, 503, 504):
            calls = 0

            def opener(*_a, **_k):
                nonlocal calls
                calls += 1
                raise http_error(status)

            c = self.make_client(opener, max_retries=1)
            with self.assertRaises(AliExpressTransportError):
                c._call("demo.method")
            self.assertEqual(calls, 2)

    def test_transport_and_timeout_retry_are_limited(self):
        for exc in (error.URLError("down"), TimeoutError("slow")):
            calls = 0

            def opener(*_a, **_k):
                nonlocal calls
                calls += 1
                raise exc

            c = self.make_client(opener, max_retries=1)
            with self.assertRaises(AliExpressTransportError):
                c._call("demo.method")
            self.assertEqual(calls, 2)

    def test_4xx_do_not_retry(self):
        for status in (400, 401, 403, 404):
            calls = 0

            def opener(*_a, **_k):
                nonlocal calls
                calls += 1
                raise http_error(status)

            with self.assertRaises(AliExpressTransportError):
                self.make_client(opener)._call("demo.method")
            self.assertEqual(calls, 1)

    def test_auth_payload_and_invalid_json_fail_fast(self):
        auth = FakeResponse(
            '{"error_response":{"code":29,"msg":"bad","sub_code":"isv.appkey-not-exists"}}'
        )
        with self.assertRaises(AliExpressAuthenticationError):
            self.make_client(lambda *_a, **_k: auth)._call("demo.method")
        calls = 0

        def invalid(*_a, **_k):
            nonlocal calls
            calls += 1
            return FakeResponse("not-json")

        with self.assertRaises(AliExpressResponseError):
            self.make_client(invalid)._call("demo.method")
        self.assertEqual(calls, 1)

    def test_min_interval_between_attempt_starts(self):
        sleeps = []
        clock = {"now": 1000.0}

        def now():
            return clock["now"]

        def sleep(seconds):
            sleeps.append(seconds)
            clock["now"] += seconds

        c = self.make_client(
            lambda *_a, **_k: FakeResponse(),
            min_interval_seconds=1.0,
            sleeper=sleep,
            wall_clock=now,
        )
        c._call("demo.method")
        clock["now"] = 1000.2
        c._call("demo.method")
        self.assertEqual(len(sleeps), 1)
        self.assertAlmostEqual(sleeps[0], 0.8, places=6)

    def test_lock_timeout_is_controlled(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        lock_path = str(Path(temp.name) / "lock")
        holder = open(lock_path, "a+")
        self.addCleanup(holder.close)
        fcntl.flock(holder.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        tick = {"value": -0.2}

        def monotonic():
            tick["value"] += 0.2
            return tick["value"]

        cfg = AliExpressConfig(
            app_key="k",
            app_secret="s",
            tracking_id="t",
            lock_timeout_seconds=0.3,
            min_interval_seconds=0,
            backoff_base_seconds=0,
            backoff_max_seconds=0,
            jitter_max_seconds=0,
        )
        c = AliExpressClient(
            cfg,
            opener=lambda *_a, **_k: FakeResponse(),
            sleeper=lambda _s: None,
            monotonic=monotonic,
            lock_path=lock_path,
            cadence_path=str(Path(temp.name) / "cadence"),
        )
        with self.assertRaises(AliExpressRuntimeStateError):
            c._call("demo.method")

    def test_retry_rebuilds_timestamp_and_signature(self):
        bodies = []
        calls = 0
        clock = iter([1000.0, 1000.0, 1001.0, 1001.0, 1002.0, 1002.0])

        def opener(req, **_k):
            nonlocal calls
            calls += 1
            bodies.append(req.data.decode())
            if calls == 1:
                raise error.URLError("temporary")
            return FakeResponse()

        c = self.make_client(
            opener,
            wall_clock=lambda: next(clock),
            backoff_base_seconds=0,
            backoff_max_seconds=0,
        )
        c._call("demo.method")
        first = dict(x.split("=", 1) for x in bodies[0].split("&"))
        second = dict(x.split("=", 1) for x in bodies[1].split("&"))
        self.assertNotEqual(first["timestamp"], second["timestamp"])
        self.assertNotEqual(first["sign"], second["sign"])

    def test_secret_values_not_in_exception_or_logs(self):
        c = self.make_client(
            lambda *_a, **_k: (_ for _ in ()).throw(error.URLError("fake-secret fake-tracking")),
            max_retries=0,
        )
        with self.assertRaises(AliExpressTransportError) as ctx:
            c._call("demo.method")
        self.assertNotIn("fake-secret", str(ctx.exception))
        self.assertNotIn("fake-tracking", str(ctx.exception))

    def test_two_clients_do_not_call_upstream_in_parallel(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        base = Path(temp.name)
        state = {"active": 0, "max_active": 0}
        guard = threading.Lock()
        barrier = threading.Barrier(2)
        cfg = AliExpressConfig(
            app_key="k",
            app_secret="s",
            tracking_id="t",
            min_interval_seconds=0,
            backoff_base_seconds=0,
            backoff_max_seconds=0,
            jitter_max_seconds=0,
            lock_timeout_seconds=2,
        )

        def opener(*_a, **_k):
            with guard:
                state["active"] += 1
                state["max_active"] = max(state["max_active"], state["active"])
            time.sleep(0.05)
            with guard:
                state["active"] -= 1
            return FakeResponse()

        clients = [
            AliExpressClient(
                cfg, opener=opener, lock_path=str(base / "lock"), cadence_path=str(base / "cadence")
            )
            for _ in range(2)
        ]
        failures = []

        def run(client):
            try:
                barrier.wait()
                client._call("demo.method")
            except Exception as exc:  # noqa: BLE001 - test captures thread failures
                failures.append(exc)

        threads = [threading.Thread(target=run, args=(client,)) for client in clients]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(failures, [])
        self.assertEqual(state["max_active"], 1)


class SharedRuntimeStateTests(SimpleTestCase):
    def test_default_runtime_paths_use_shared_run_directory(self):
        self.assertEqual(DEFAULT_LOCK_PATH, "/run/lowcost-europa/aliexpress.lock")
        self.assertEqual(
            DEFAULT_CADENCE_PATH,
            "/run/lowcost-europa/aliexpress.last-start",
        )

    def test_separate_processes_cannot_acquire_same_operation_lock(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        lock_path = str(Path(temp.name) / "shared.lock")
        ctx = multiprocessing.get_context("fork")
        ready = ctx.Event()
        release = ctx.Event()
        result = ctx.Queue()
        holder = ctx.Process(target=_hold_operation_lock, args=(lock_path, ready, release))
        contender = None
        holder.start()
        try:
            self.assertTrue(ready.wait(2))
            contender = ctx.Process(target=_try_operation_lock, args=(lock_path, result))
            contender.start()
            contender.join(3)
            self.assertEqual(contender.exitcode, 0)
            self.assertEqual(result.get(timeout=1), "blocked")
        finally:
            release.set()
            holder.join(3)
            if contender is not None and contender.is_alive():
                contender.terminate()
            if holder.is_alive():
                holder.terminate()
        self.assertEqual(holder.exitcode, 0)

    def test_separate_processes_share_cadence_state(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        cadence_path = str(Path(temp.name) / "shared.last-start")
        ctx = multiprocessing.get_context("fork")
        writer = ctx.Process(target=_write_cadence_state, args=(cadence_path, 1000.0))
        writer.start()
        writer.join(3)
        self.assertEqual(writer.exitcode, 0)
        self.assertEqual(Path(cadence_path).read_text(), "1000.000000")

        result = ctx.Queue()
        reader = ctx.Process(
            target=_read_shared_cadence_state,
            args=(cadence_path, 1000.25, result),
        )
        reader.start()
        reader.join(3)
        self.assertEqual(reader.exitcode, 0)
        self.assertAlmostEqual(result.get(timeout=1), 0.75, places=6)
        self.assertEqual(Path(cadence_path).read_text(), "1001.000000")


class SafetyConfigTests(SimpleTestCase):
    @patch.dict(
        "os.environ",
        {
            "ALIEXPRESS_APP_KEY": "k",
            "ALIEXPRESS_APP_SECRET": "s",
            "ALIEXPRESS_TRACKING_ID": "t",
            "ALIEXPRESS_TIMEOUT_SECONDS": "0",
        },
        clear=True,
    )
    def test_invalid_config_fails(self):
        with self.assertRaises(AliExpressConfigurationError):
            AliExpressConfig.from_env()


class RuntimeStateSecurityTests(SimpleTestCase):
    def test_lock_symlink_is_rejected_before_upstream_call(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        base = Path(temp.name)
        target = base / "target"
        target.write_text("protected")
        lock_path = base / "lock"
        lock_path.symlink_to(target)
        calls = []
        client = AliExpressClient(
            AliExpressConfig(
                app_key="k",
                app_secret="s",
                tracking_id="t",
                min_interval_seconds=0,
            ),
            opener=lambda *_a, **_k: calls.append(True),
            lock_path=str(lock_path),
            cadence_path=str(base / "cadence"),
        )
        with self.assertRaises(AliExpressRuntimeStateError):
            client._call("demo.method")
        self.assertEqual(calls, [])
        self.assertEqual(client.execution_metrics.logical_operations, 1)
        self.assertEqual(client.execution_metrics.attempts, 0)
        self.assertEqual(target.read_text(), "protected")

    def test_missing_lock_parent_is_runtime_state_failure_before_upstream(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        base = Path(temp.name)
        opener = Mock()
        client = AliExpressClient(
            AliExpressConfig(
                app_key="k",
                app_secret="s",
                tracking_id="t",
                min_interval_seconds=0,
            ),
            opener=opener,
            lock_path=str(base / "missing" / "lock"),
            cadence_path=str(base / "cadence"),
        )

        with self.assertRaises(AliExpressRuntimeStateError):
            client._call("demo.method")

        opener.assert_not_called()
        self.assertEqual(client.execution_metrics.logical_operations, 1)
        self.assertEqual(client.execution_metrics.attempts, 0)

    def test_runtime_state_ownership_mismatch_is_typed_and_pre_http(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        base = Path(temp.name)
        lock_path = base / "lock"
        lock_path.write_text("")
        opener = Mock()
        client = AliExpressClient(
            AliExpressConfig(
                app_key="k",
                app_secret="s",
                tracking_id="t",
                min_interval_seconds=0,
            ),
            opener=opener,
            lock_path=str(lock_path),
            cadence_path=str(base / "cadence"),
        )
        wrong_euid = os.geteuid() + 1

        with patch("apps.integrations.aliexpress.client.os.geteuid", return_value=wrong_euid):
            with self.assertRaises(AliExpressRuntimeStateError):
                client._call("demo.method")

        opener.assert_not_called()
        self.assertEqual(client.execution_metrics.attempts, 0)

    def test_invalid_cadence_path_is_runtime_state_failure_before_upstream(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        base = Path(temp.name)
        cadence_path = base / "cadence"
        cadence_path.mkdir()
        opener = Mock()
        client = AliExpressClient(
            AliExpressConfig(
                app_key="k",
                app_secret="s",
                tracking_id="t",
                min_interval_seconds=0,
            ),
            opener=opener,
            lock_path=str(base / "lock"),
            cadence_path=str(cadence_path),
        )

        with self.assertRaises(AliExpressRuntimeStateError):
            client._call("demo.method")

        opener.assert_not_called()
        self.assertEqual(client.execution_metrics.logical_operations, 1)
        self.assertEqual(client.execution_metrics.attempts, 0)

    def test_execution_metrics_distinguish_logical_operation_and_attempts(self):
        calls = 0

        def opener(*_a, **_k):
            nonlocal calls
            calls += 1
            if calls == 1:
                raise error.URLError("temporary")
            return FakeResponse()

        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        base = Path(temp.name)
        client = AliExpressClient(
            AliExpressConfig(
                app_key="k",
                app_secret="s",
                tracking_id="t",
                max_retries=1,
                min_interval_seconds=0,
                backoff_base_seconds=0,
                backoff_max_seconds=0,
                jitter_max_seconds=0,
            ),
            opener=opener,
            sleeper=lambda _s: None,
            lock_path=str(base / "lock"),
            cadence_path=str(base / "cadence"),
        )
        client._call("demo.method")
        metrics = client.execution_metrics
        self.assertEqual(metrics.logical_operations, 1)
        self.assertEqual(metrics.attempts, 2)
        self.assertEqual(metrics.retries, 1)

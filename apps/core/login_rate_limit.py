import fcntl
import hashlib
import ipaddress
import json
import math
import os
import stat
import tempfile
import time
from pathlib import Path

from django.conf import settings


def normalized_client_ip(request) -> str:
    """Return the trusted client IP for the current Nginx -> loopback topology."""
    remote = _parse_ip(request.META.get("REMOTE_ADDR", ""))
    if remote is None:
        return "unknown"
    if remote.is_loopback:
        forwarded = _parse_ip(request.META.get("HTTP_X_REAL_IP", ""))
        if forwarded is not None:
            return forwarded.compressed
    return remote.compressed


def source_token(request) -> str:
    normalized = normalized_client_ip(request)
    return hashlib.sha256(normalized.encode("ascii")).hexdigest()


def _parse_ip(value):
    try:
        return ipaddress.ip_address(str(value).strip())
    except ValueError:
        return None


class FileLoginRateLimiter:
    def __init__(self):
        self.state_path = Path(settings.PRIVATE_LOGIN_RATE_LIMIT_STATE_PATH)
        self.lock_path = Path(settings.PRIVATE_LOGIN_RATE_LIMIT_LOCK_PATH)
        self.attempt_limit = settings.PRIVATE_LOGIN_RATE_LIMIT_ATTEMPTS
        self.window_seconds = settings.PRIVATE_LOGIN_RATE_LIMIT_WINDOW_SECONDS
        self.throttle_seconds = settings.PRIVATE_LOGIN_RATE_LIMIT_THROTTLE_SECONDS
        self.max_entries = settings.PRIVATE_LOGIN_RATE_LIMIT_MAX_ENTRIES

    def retry_after(self, token: str, *, now=None) -> int:
        now = time.time() if now is None else now
        with self._locked_state() as state:
            self._prune(state, now)
            entry = state["entries"].get(token)
            retry = 0
            if entry and entry["throttle_until"] > now:
                retry = max(1, math.ceil(entry["throttle_until"] - now))
            # Verify durable write access before any password is checked.
            # A read-only state file must not silently disable throttling.
            self._write_state(state)
            return retry

    def record_failure(self, token: str, *, now=None) -> None:
        now = time.time() if now is None else now
        with self._locked_state() as state:
            self._prune(state, now)
            entries = state["entries"]
            entry = entries.get(token, {"attempts": [], "throttle_until": 0.0, "last_seen": now})
            attempts = [stamp for stamp in entry["attempts"] if stamp > now - self.window_seconds]
            attempts.append(now)
            attempts = attempts[-self.attempt_limit :]
            throttle_until = float(entry.get("throttle_until", 0.0))
            if len(attempts) >= self.attempt_limit:
                throttle_until = max(throttle_until, now + self.throttle_seconds)
            entries[token] = {
                "attempts": attempts,
                "throttle_until": throttle_until,
                "last_seen": now,
            }
            self._cap_entries(entries)
            self._write_state(state)

    def clear(self, token: str) -> None:
        with self._locked_state() as state:
            if state["entries"].pop(token, None) is not None:
                self._write_state(state)

    def _locked_state(self):
        return _LockedState(self)

    def _read_state(self):
        if not self.state_path.exists():
            return {"version": 1, "entries": {}}
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(self.state_path, flags)
        try:
            info = os.fstat(fd)
            self._validate_file(info, self.state_path)
            with os.fdopen(fd, "r", encoding="utf-8") as handle:
                fd = -1
                data = json.load(handle)
        finally:
            if fd >= 0:
                os.close(fd)
        if data.get("version") != 1 or not isinstance(data.get("entries"), dict):
            raise ValueError("invalid login rate-limit state")
        return data

    def _write_state(self, state) -> None:
        self.state_path.parent.mkdir(parents=False, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(
            prefix=f".{self.state_path.name}.",
            dir=self.state_path.parent,
        )
        try:
            os.fchmod(fd, 0o600)
            payload = json.dumps(state, separators=(",", ":"), sort_keys=True).encode("utf-8")
            os.write(fd, payload)
            os.fsync(fd)
            os.close(fd)
            fd = -1
            os.replace(tmp_name, self.state_path)
            dir_fd = os.open(self.state_path.parent, os.O_RDONLY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
        finally:
            if fd >= 0:
                os.close(fd)
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)

    def _prune(self, state, now) -> bool:
        changed = False
        cutoff = now - self.window_seconds
        for token, entry in list(state["entries"].items()):
            if not isinstance(entry, dict):
                raise ValueError("invalid login rate-limit entry")
            attempts = entry.get("attempts")
            throttle_until = entry.get("throttle_until")
            last_seen = entry.get("last_seen")
            if (
                not isinstance(attempts, list)
                or not all(isinstance(stamp, (int, float)) for stamp in attempts)
                or not isinstance(throttle_until, (int, float))
                or not isinstance(last_seen, (int, float))
            ):
                raise ValueError("invalid login rate-limit entry")
            fresh = [float(stamp) for stamp in attempts if float(stamp) > cutoff]
            if fresh != attempts:
                entry["attempts"] = fresh
                changed = True
            if not fresh and float(throttle_until) <= now:
                del state["entries"][token]
                changed = True
        return changed

    def _cap_entries(self, entries) -> None:
        overflow = len(entries) - self.max_entries
        if overflow <= 0:
            return
        oldest = sorted(entries, key=lambda key: float(entries[key]["last_seen"]))[:overflow]
        for key in oldest:
            del entries[key]

    @staticmethod
    def _validate_file(info, path) -> None:
        if not stat.S_ISREG(info.st_mode):
            raise ValueError(f"unsafe login rate-limit file: {path}")
        if info.st_uid != os.geteuid():
            raise ValueError(f"login rate-limit file ownership mismatch: {path}")
        if stat.S_IMODE(info.st_mode) != 0o600:
            raise ValueError(f"login rate-limit file mode mismatch: {path}")


class _LockedState:
    def __init__(self, limiter):
        self.limiter = limiter
        self.handle = None
        self.state = None

    def __enter__(self):
        flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(self.limiter.lock_path, flags, 0o600)
        info = os.fstat(fd)
        self.limiter._validate_file(info, self.limiter.lock_path)
        self.handle = os.fdopen(fd, "r+")
        fcntl.flock(self.handle.fileno(), fcntl.LOCK_EX)
        self.state = self.limiter._read_state()
        return self.state

    def __exit__(self, exc_type, exc, tb):
        if self.handle is not None:
            fcntl.flock(self.handle.fileno(), fcntl.LOCK_UN)
            self.handle.close()
        return False

import logging
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client, RequestFactory, TestCase, override_settings
from django.urls import reverse

from apps.core.login_rate_limit import FileLoginRateLimiter, normalized_client_ip, source_token

PASSWORD = "private-login-test-password"
RATE_LIMIT_ATTEMPTS = 5
WINDOW_SECONDS = 300
THROTTLE_SECONDS = 300


class RateLimitTestMixin:
    def setUp(self):
        super().setUp()
        self.tempdir = tempfile.TemporaryDirectory()
        base = Path(self.tempdir.name)
        self.settings_override = override_settings(
            PRIVATE_LOGIN_RATE_LIMIT_ATTEMPTS=RATE_LIMIT_ATTEMPTS,
            PRIVATE_LOGIN_RATE_LIMIT_WINDOW_SECONDS=WINDOW_SECONDS,
            PRIVATE_LOGIN_RATE_LIMIT_THROTTLE_SECONDS=THROTTLE_SECONDS,
            PRIVATE_LOGIN_RATE_LIMIT_MAX_ENTRIES=16,
            PRIVATE_LOGIN_RATE_LIMIT_STATE_PATH=str(base / "state.json"),
            PRIVATE_LOGIN_RATE_LIMIT_LOCK_PATH=str(base / "state.lock"),
        )
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        self.addCleanup(self.tempdir.cleanup)

    def owner(self, **overrides):
        values = {"is_staff": True, "is_active": True}
        values.update(overrides)
        return get_user_model().objects.create_user(
            username="lowcost-owner",
            password=PASSWORD,
            **values,
        )

    def admin(self):
        return get_user_model().objects.create_superuser(
            username="admin-user",
            email="admin@example.test",
            password=PASSWORD,
        )


@override_settings(OWNER_PANEL_USERNAME="lowcost-owner")
class OwnerLoginRateLimitTests(RateLimitTestMixin, TestCase):
    def test_get_login_remains_accessible_and_private(self):
        response = self.client.get(reverse("owner-panel:login"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Cache-Control"], "private, no-store")
        self.assertEqual(response["X-Robots-Tag"], "noindex, nofollow")

    def test_valid_owner_login_succeeds_and_clears_source_state(self):
        self.owner()
        login_url = reverse("owner-panel:login")
        for _ in range(2):
            self.client.post(login_url, {"password": "wrong"}, REMOTE_ADDR="203.0.113.10")
        response = self.client.post(
            login_url,
            {"password": PASSWORD},
            REMOTE_ADDR="203.0.113.10",
        )
        self.assertRedirects(response, reverse("storefront:home"))
        limiter = FileLoginRateLimiter()
        request = RequestFactory().post(login_url, REMOTE_ADDR="203.0.113.10")
        self.assertEqual(limiter.retry_after(source_token(request)), 0)
        self.assertNotIn(source_token(request), limiter._read_state()["entries"])

    def test_invalid_owner_login_is_generic_and_below_threshold_is_processed(self):
        self.owner()
        login_url = reverse("owner-panel:login")
        for attempt in range(RATE_LIMIT_ATTEMPTS):
            secret = f"wrong-secret-{attempt}"
            response = self.client.post(
                login_url,
                {"password": secret, "username": f"ignored-{attempt}"},
                REMOTE_ADDR="203.0.113.11",
            )
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "Palavra-passe incorreta.")
            self.assertNotContains(response, secret)
            self.assertNotContains(response, f"ignored-{attempt}")

    def test_owner_threshold_exceeded_returns_429_with_retry_after(self):
        self.owner()
        login_url = reverse("owner-panel:login")
        for _ in range(RATE_LIMIT_ATTEMPTS):
            self.client.post(login_url, {"password": "wrong"}, REMOTE_ADDR="203.0.113.12")
        response = self.client.post(
            login_url,
            {"password": "another-wrong"},
            REMOTE_ADDR="203.0.113.12",
        )
        self.assertEqual(response.status_code, 429)
        self.assertGreaterEqual(int(response["Retry-After"]), 1)
        self.assertNotContains(response, "another-wrong", status_code=429)
        self.assertEqual(response["Cache-Control"], "private, no-store")
        self.assertEqual(response["X-Robots-Tag"], "noindex, nofollow")

    def test_owner_csrf_is_still_enforced_and_not_counted(self):
        self.owner()
        client = Client(enforce_csrf_checks=True)
        login_url = reverse("owner-panel:login")
        response = client.post(
            login_url,
            {"password": "wrong"},
            REMOTE_ADDR="203.0.113.13",
        )
        self.assertEqual(response.status_code, 403)
        limiter = FileLoginRateLimiter()
        request = RequestFactory().post(login_url, REMOTE_ADDR="203.0.113.13")
        self.assertNotIn(source_token(request), limiter._read_state()["entries"])

    def test_authenticated_private_page_keeps_no_store_and_noindex(self):
        owner = self.owner()
        self.client.force_login(owner)
        response = self.client.get(reverse("owner-panel:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Cache-Control"], "private, no-store")
        self.assertEqual(response["X-Robots-Tag"], "noindex, nofollow")


class AdminLoginRateLimitTests(RateLimitTestMixin, TestCase):
    def test_get_admin_login_remains_accessible_and_never_cached(self):
        response = self.client.get(reverse("admin:login"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("no-store", response["Cache-Control"])

    def test_valid_admin_login_succeeds(self):
        self.admin()
        response = self.client.post(
            reverse("admin:login"),
            {"username": "admin-user", "password": PASSWORD, "next": "/admin/"},
            REMOTE_ADDR="198.51.100.20",
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/admin/")

    def test_admin_known_and_unknown_invalid_logins_are_generic(self):
        self.admin()
        login_url = reverse("admin:login")
        known = self.client.post(
            login_url,
            {"username": "admin-user", "password": "wrong"},
            REMOTE_ADDR="198.51.100.21",
        )
        unknown = self.client.post(
            login_url,
            {"username": "does-not-exist", "password": "wrong"},
            REMOTE_ADDR="198.51.100.22",
        )
        self.assertEqual(known.status_code, 200)
        self.assertEqual(unknown.status_code, 200)
        known_errors = list(known.context["form"].non_field_errors())
        unknown_errors = list(unknown.context["form"].non_field_errors())
        self.assertEqual(known_errors, unknown_errors)
        self.assertTrue(known_errors)
        self.assertNotContains(known, "wrong")
        self.assertNotContains(unknown, "wrong")

    def test_username_variation_does_not_bypass_source_throttle(self):
        self.admin()
        login_url = reverse("admin:login")
        for attempt in range(RATE_LIMIT_ATTEMPTS):
            response = self.client.post(
                login_url,
                {"username": f"varied-{attempt}", "password": "wrong"},
                REMOTE_ADDR="198.51.100.23",
            )
            self.assertEqual(response.status_code, 200)
        response = self.client.post(
            login_url,
            {"username": "another-user", "password": "wrong"},
            REMOTE_ADDR="198.51.100.23",
        )
        self.assertEqual(response.status_code, 429)

    def test_owner_and_admin_share_the_same_source_limit(self):
        owner_url = reverse("owner-panel:login")
        admin_url = reverse("admin:login")
        source = "198.51.100.24"
        for _ in range(3):
            self.client.post(owner_url, {"password": "wrong"}, REMOTE_ADDR=source)
        for _ in range(2):
            self.client.post(
                admin_url,
                {"username": "anything", "password": "wrong"},
                REMOTE_ADDR=source,
            )
        response = self.client.post(
            admin_url,
            {"username": "new-name", "password": "wrong"},
            REMOTE_ADDR=source,
        )
        self.assertEqual(response.status_code, 429)


    def test_failed_login_logging_contains_no_username_or_password(self):
        self.admin()
        submitted_user = "sensitive-submitted-user"
        submitted_password = "sensitive-submitted-password"
        with self.assertLogs("apps.core.middleware", level=logging.INFO) as captured:
            response = self.client.post(
                reverse("admin:login"),
                {"username": submitted_user, "password": submitted_password},
                REMOTE_ADDR="198.51.100.26",
            )
        self.assertEqual(response.status_code, 200)
        log_text = " ".join(captured.output)
        self.assertNotIn(submitted_user, log_text)
        self.assertNotIn(submitted_password, log_text)

    def test_admin_csrf_is_still_enforced(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post(
            reverse("admin:login"),
            {"username": "anything", "password": "wrong"},
            REMOTE_ADDR="198.51.100.25",
        )
        self.assertEqual(response.status_code, 403)


class RateLimitStateTests(RateLimitTestMixin, TestCase):
    def test_throttle_expires_automatically(self):
        limiter = FileLoginRateLimiter()
        token = "a" * 64
        for _ in range(RATE_LIMIT_ATTEMPTS):
            limiter.record_failure(token, now=1000.0)
        self.assertEqual(limiter.retry_after(token, now=1001.0), 299)
        self.assertEqual(limiter.retry_after(token, now=1301.0), 0)
        self.assertNotIn(token, limiter._read_state()["entries"])

    def test_state_is_shared_across_limiter_instances(self):
        token = "b" * 64
        first = FileLoginRateLimiter()
        second = FileLoginRateLimiter()
        for _ in range(RATE_LIMIT_ATTEMPTS):
            first.record_failure(token, now=1000.0)
        self.assertGreater(second.retry_after(token, now=1001.0), 0)

    @override_settings(PRIVATE_LOGIN_RATE_LIMIT_MAX_ENTRIES=3)
    def test_state_growth_is_bounded(self):
        limiter = FileLoginRateLimiter()
        for index in range(6):
            limiter.record_failure(f"{index:064d}", now=1000.0 + index)
        self.assertLessEqual(len(limiter._read_state()["entries"]), 3)

    def test_state_file_contains_only_hashed_source_and_timestamps(self):
        request = RequestFactory().post("/", REMOTE_ADDR="192.0.2.44")
        token = source_token(request)
        FileLoginRateLimiter().record_failure(token, now=1000.0)
        state_path = Path(self.settings_override.options["PRIVATE_LOGIN_RATE_LIMIT_STATE_PATH"])
        raw = state_path.read_text()
        self.assertIn(token, raw)
        self.assertNotIn("192.0.2.44", raw)
        self.assertNotIn("password", raw.lower())
        self.assertEqual(oct(state_path.stat().st_mode & 0o777), "0o600")

    def test_limiter_failure_fails_closed_and_does_not_expose_secret(self):
        from django.http import HttpResponse

        from apps.core.middleware import PrivateLoginRateLimitMiddleware

        def get_response(request):
            return HttpResponse("normal")

        middleware = PrivateLoginRateLimitMiddleware(get_response)
        request = RequestFactory().post(
            "/painel/entrar/",
            {"password": "super-secret-value"},
            REMOTE_ADDR="192.0.2.45",
        )
        with patch(
            "apps.core.middleware.FileLoginRateLimiter.retry_after",
            side_effect=OSError("state unavailable"),
        ):
            with self.assertLogs("apps.core.middleware", level=logging.ERROR) as captured:
                response = middleware.process_view(request, None, (), {})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response["Cache-Control"], "private, no-store")
        self.assertEqual(response["X-Robots-Tag"], "noindex, nofollow")
        self.assertEqual(response["Retry-After"], "60")
        log_text = " ".join(captured.output)
        self.assertNotIn("super-secret-value", log_text)
        self.assertNotIn("state unavailable", log_text)


    def test_limiter_write_failure_returns_503_without_leaking_password(self):
        from django.contrib.auth.models import AnonymousUser
        from django.http import HttpResponse

        from apps.core.middleware import PrivateLoginRateLimitMiddleware

        middleware = PrivateLoginRateLimitMiddleware(lambda request: HttpResponse("normal"))
        request = RequestFactory().post(
            "/painel/entrar/",
            {"password": "sensitive-password"},
            REMOTE_ADDR="192.0.2.46",
        )
        request.user = AnonymousUser()
        with patch("apps.core.middleware.FileLoginRateLimiter.record_failure", side_effect=OSError):
            with self.assertLogs("apps.core.middleware", level=logging.ERROR) as captured:
                check = middleware.process_view(request, None, (), {})
                self.assertIsNone(check)
                response = middleware.process_response(request, HttpResponse("Palavra-passe incorreta."))
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response["X-Robots-Tag"], "noindex, nofollow")
        self.assertNotIn("sensitive-password", response.content.decode())
        self.assertNotIn("sensitive-password", " ".join(captured.output))


class ClientSourcePolicyTests(TestCase):
    def request(self, remote_addr, *, real_ip=None, forwarded_for=None):
        meta = {"REMOTE_ADDR": remote_addr}
        if real_ip is not None:
            meta["HTTP_X_REAL_IP"] = real_ip
        if forwarded_for is not None:
            meta["HTTP_X_FORWARDED_FOR"] = forwarded_for
        return RequestFactory().post("/", **meta)

    def test_direct_source_ignores_attacker_headers(self):
        request = self.request(
            "203.0.113.50",
            real_ip="198.51.100.200",
            forwarded_for="198.51.100.201, 198.51.100.202",
        )
        self.assertEqual(normalized_client_ip(request), "203.0.113.50")

    def test_loopback_proxy_trusts_nginx_overwritten_x_real_ip(self):
        request = self.request(
            "127.0.0.1",
            real_ip="203.0.113.51",
            forwarded_for="198.51.100.201",
        )
        self.assertEqual(normalized_client_ip(request), "203.0.113.51")

    def test_x_forwarded_for_is_never_used_as_source(self):
        request = self.request(
            "127.0.0.1",
            real_ip="203.0.113.52",
            forwarded_for="1.1.1.1, 2.2.2.2",
        )
        self.assertEqual(normalized_client_ip(request), "203.0.113.52")

    def test_malformed_x_real_ip_falls_back_to_loopback_peer(self):
        request = self.request("127.0.0.1", real_ip="not-an-ip")
        self.assertEqual(normalized_client_ip(request), "127.0.0.1")


    def test_malformed_direct_peer_uses_bounded_unknown_source(self):
        request = self.request("not-an-ip", real_ip="203.0.113.200")
        self.assertEqual(normalized_client_ip(request), "unknown")

    def test_missing_proxy_headers_uses_direct_peer(self):
        request = self.request("192.0.2.53")
        self.assertEqual(normalized_client_ip(request), "192.0.2.53")

    def test_ipv6_is_normalized(self):
        request = self.request("127.0.0.1", real_ip="2001:0db8:0:0:0:0:0:1")
        self.assertEqual(normalized_client_ip(request), "2001:db8::1")

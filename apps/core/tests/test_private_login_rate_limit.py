import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client, RequestFactory, TestCase, override_settings
from django.urls import reverse

from apps.core.login_rate_limit import (
    FileLoginRateLimiter,
    normalized_client_ip,
    source_token,
)

OWNER_PASSWORD = "owner-private-login-test"
ADMIN_PASSWORD = "admin-private-login-test"


class PrivateLoginRateLimitTestMixin:
    def setUp(self):
        super().setUp()
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.override = override_settings(
            PRIVATE_LOGIN_RATE_LIMIT_ATTEMPTS=5,
            PRIVATE_LOGIN_RATE_LIMIT_WINDOW_SECONDS=300,
            PRIVATE_LOGIN_RATE_LIMIT_THROTTLE_SECONDS=300,
            PRIVATE_LOGIN_RATE_LIMIT_MAX_ENTRIES=64,
            PRIVATE_LOGIN_RATE_LIMIT_STATE_PATH=str(root / "state.json"),
            PRIVATE_LOGIN_RATE_LIMIT_LOCK_PATH=str(root / "state.lock"),
            OWNER_PANEL_USERNAME="lowcost-owner",
        )
        self.override.enable()

    def tearDown(self):
        self.override.disable()
        self.temp.cleanup()
        super().tearDown()

    def make_owner(self):
        return get_user_model().objects.create_user(
            username="lowcost-owner",
            password=OWNER_PASSWORD,
            is_staff=True,
            is_active=True,
        )

    def make_admin(self):
        return get_user_model().objects.create_superuser(
            username="admin-user",
            email="admin@example.test",
            password=ADMIN_PASSWORD,
        )


class OwnerLoginRateLimitTests(PrivateLoginRateLimitTestMixin, TestCase):
    def test_get_login_remains_accessible_and_private(self):
        response = self.client.get(reverse("owner-panel:login"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Cache-Control"], "private, no-store")
        self.assertEqual(response["X-Robots-Tag"], "noindex, nofollow")

    def test_valid_owner_login_still_succeeds(self):
        self.make_owner()
        response = self.client.post(
            reverse("owner-panel:login"),
            {"password": OWNER_PASSWORD},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("_auth_user_id", self.client.session)

    def test_invalid_owner_login_remains_generic(self):
        self.make_owner()
        submitted = "wrong-owner-secret"
        response = self.client.post(reverse("owner-panel:login"), {"password": submitted})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Palavra-passe incorreta.")
        self.assertNotContains(response, submitted)
        self.assertNotContains(response, "lowcost-owner")

    def test_five_attempts_are_processed_and_sixth_is_throttled(self):
        self.make_owner()
        for index in range(5):
            response = self.client.post(
                reverse("owner-panel:login"),
                {"password": f"wrong-{index}"},
            )
            self.assertEqual(response.status_code, 200)
        response = self.client.post(
            reverse("owner-panel:login"),
            {"password": "wrong-sixth"},
        )
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response["Retry-After"], "300")
        self.assertEqual(response["Cache-Control"], "private, no-store")
        self.assertEqual(response["X-Robots-Tag"], "noindex, nofollow")

    def test_throttle_expires_automatically(self):
        self.make_owner()
        with patch("apps.core.login_rate_limit.time.time", return_value=1000.0):
            for index in range(5):
                self.client.post(
                    reverse("owner-panel:login"),
                    {"password": f"wrong-{index}"},
                )
            self.assertEqual(
                self.client.post(
                    reverse("owner-panel:login"),
                    {"password": "blocked"},
                ).status_code,
                429,
            )
        with patch("apps.core.login_rate_limit.time.time", return_value=1301.0):
            response = self.client.post(
                reverse("owner-panel:login"),
                {"password": "processed-again"},
            )
        self.assertEqual(response.status_code, 200)

    def test_username_variation_does_not_bypass_source_throttle(self):
        self.make_owner()
        for index in range(5):
            response = self.client.post(
                reverse("owner-panel:login"),
                {"username": f"made-up-{index}", "password": "wrong"},
            )
            self.assertEqual(response.status_code, 200)
        response = self.client.post(
            reverse("owner-panel:login"),
            {"username": "another-name", "password": "wrong"},
        )
        self.assertEqual(response.status_code, 429)

    def test_success_before_threshold_clears_source_state(self):
        self.make_owner()
        for index in range(4):
            self.client.post(
                reverse("owner-panel:login"),
                {"password": f"wrong-{index}"},
            )
        self.assertEqual(
            self.client.post(
                reverse("owner-panel:login"),
                {"password": OWNER_PASSWORD},
            ).status_code,
            302,
        )
        self.client.post(reverse("owner-panel:logout"))
        for index in range(5):
            self.assertEqual(
                self.client.post(
                    reverse("owner-panel:login"),
                    {"password": f"new-wrong-{index}"},
                ).status_code,
                200,
            )

    def test_csrf_is_enforced_and_rejection_is_not_counted(self):
        self.make_owner()
        csrf_client = Client(enforce_csrf_checks=True)
        for _ in range(7):
            response = csrf_client.post(
                reverse("owner-panel:login"),
                {"password": "wrong"},
            )
            self.assertEqual(response.status_code, 403)

    def test_private_authenticated_page_headers_are_preserved(self):
        owner = self.make_owner()
        self.client.force_login(owner)
        response = self.client.get(reverse("owner-panel:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Cache-Control"], "private, no-store")
        self.assertEqual(response["X-Robots-Tag"], "noindex, nofollow")

    def test_password_is_not_logged(self):
        self.make_owner()
        secret = "never-log-this-owner-password"
        with self.assertLogs("apps.core.middleware", level="INFO") as captured:
            self.client.post(reverse("owner-panel:login"), {"password": secret})
        joined = "\n".join(captured.output)
        self.assertNotIn(secret, joined)
        self.assertNotIn("lowcost-owner", joined)


class AdminLoginRateLimitTests(PrivateLoginRateLimitTestMixin, TestCase):
    def test_get_admin_login_remains_accessible_and_uncached(self):
        response = self.client.get(reverse("admin:login"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("no-store", response["Cache-Control"])

    def test_valid_admin_login_still_succeeds(self):
        self.make_admin()
        response = self.client.post(
            reverse("admin:login"),
            {"username": "admin-user", "password": ADMIN_PASSWORD},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("_auth_user_id", self.client.session)

    def test_known_and_unknown_admin_users_have_generic_invalid_result(self):
        self.make_admin()
        known = self.client.post(
            reverse("admin:login"),
            {"username": "admin-user", "password": "wrong"},
        )
        unknown = self.client.post(
            reverse("admin:login"),
            {"username": "does-not-exist", "password": "wrong"},
        )
        self.assertEqual(known.status_code, 200)
        self.assertEqual(unknown.status_code, 200)
        self.assertEqual(
            list(known.context["form"].errors["__all__"]),
            list(unknown.context["form"].errors["__all__"]),
        )

    def test_admin_five_attempts_processed_and_sixth_throttled(self):
        self.make_admin()
        for index in range(5):
            response = self.client.post(
                reverse("admin:login"),
                {"username": f"varied-{index}", "password": "wrong"},
            )
            self.assertEqual(response.status_code, 200)
        response = self.client.post(
            reverse("admin:login"),
            {"username": "another", "password": "wrong"},
        )
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response["Retry-After"], "300")

    def test_admin_throttle_expires(self):
        self.make_admin()
        with patch("apps.core.login_rate_limit.time.time", return_value=2000.0):
            for index in range(5):
                self.client.post(
                    reverse("admin:login"),
                    {"username": f"user-{index}", "password": "wrong"},
                )
            self.assertEqual(
                self.client.post(
                    reverse("admin:login"),
                    {"username": "blocked", "password": "wrong"},
                ).status_code,
                429,
            )
        with patch("apps.core.login_rate_limit.time.time", return_value=2301.0):
            response = self.client.post(
                reverse("admin:login"),
                {"username": "again", "password": "wrong"},
            )
        self.assertEqual(response.status_code, 200)

    def test_admin_csrf_is_enforced(self):
        self.make_admin()
        csrf_client = Client(enforce_csrf_checks=True)
        response = csrf_client.post(
            reverse("admin:login"),
            {"username": "admin-user", "password": ADMIN_PASSWORD},
        )
        self.assertEqual(response.status_code, 403)

    def test_admin_credentials_are_not_logged(self):
        self.make_admin()
        username = "sensitive-submitted-admin"
        secret = "never-log-this-admin-password"
        with self.assertLogs("apps.core.middleware", level="INFO") as captured:
            self.client.post(
                reverse("admin:login"),
                {"username": username, "password": secret},
            )
        joined = "\n".join(captured.output)
        self.assertNotIn(username, joined)
        self.assertNotIn(secret, joined)


class ClientSourcePolicyTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_direct_ipv4_ignores_attacker_forwarding_headers(self):
        request = self.factory.get(
            "/admin/login/",
            REMOTE_ADDR="198.51.100.20",
            HTTP_X_REAL_IP="203.0.113.99",
            HTTP_X_FORWARDED_FOR="203.0.113.88",
        )
        self.assertEqual(normalized_client_ip(request), "198.51.100.20")

    def test_trusted_loopback_uses_nginx_real_ip_and_ignores_xff(self):
        request = self.factory.get(
            "/admin/login/",
            REMOTE_ADDR="127.0.0.1",
            HTTP_X_REAL_IP="203.0.113.25",
            HTTP_X_FORWARDED_FOR="198.51.100.44, 203.0.113.25",
        )
        self.assertEqual(normalized_client_ip(request), "203.0.113.25")

    def test_malformed_real_ip_falls_back_to_loopback_source(self):
        request = self.factory.get(
            "/admin/login/",
            REMOTE_ADDR="127.0.0.1",
            HTTP_X_REAL_IP="not-an-ip",
        )
        self.assertEqual(normalized_client_ip(request), "127.0.0.1")

    def test_missing_and_malformed_remote_address_collapse_to_unknown(self):
        request = self.factory.get("/admin/login/", REMOTE_ADDR="invalid")
        self.assertEqual(normalized_client_ip(request), "unknown")

    def test_ipv6_is_normalized(self):
        request = self.factory.get(
            "/admin/login/",
            REMOTE_ADDR="2001:0db8:0000:0000:0000:0000:0000:0001",
        )
        self.assertEqual(normalized_client_ip(request), "2001:db8::1")

    def test_source_token_does_not_store_raw_ip(self):
        request = self.factory.get("/admin/login/", REMOTE_ADDR="198.51.100.20")
        token = source_token(request)
        self.assertEqual(len(token), 64)
        self.assertNotIn("198.51.100.20", token)


class RateLimitStateTests(PrivateLoginRateLimitTestMixin, TestCase):
    def test_two_limiter_instances_share_state(self):
        request = RequestFactory().post("/admin/login/", REMOTE_ADDR="198.51.100.30")
        token = source_token(request)
        first = FileLoginRateLimiter()
        second = FileLoginRateLimiter()
        for _ in range(5):
            first.record_failure(token, now=1000.0)
        self.assertEqual(second.retry_after(token, now=1000.0), 300)

    def test_state_growth_is_bounded(self):
        with self.settings(PRIVATE_LOGIN_RATE_LIMIT_MAX_ENTRIES=2):
            limiter = FileLoginRateLimiter()
            factory = RequestFactory()
            for index in range(3):
                request = factory.post(
                    "/admin/login/",
                    REMOTE_ADDR=f"198.51.100.{index + 1}",
                )
                limiter.record_failure(source_token(request), now=1000.0 + index)
            state = json.loads(Path(limiter.state_path).read_text())
            self.assertEqual(len(state["entries"]), 2)

    def test_storage_failure_fails_open_without_login_crash(self):
        self.make_owner()
        missing = Path(self.temp.name) / "missing" / "state.json"
        lock = Path(self.temp.name) / "missing" / "state.lock"
        with self.settings(
            PRIVATE_LOGIN_RATE_LIMIT_STATE_PATH=str(missing),
            PRIVATE_LOGIN_RATE_LIMIT_LOCK_PATH=str(lock),
        ):
            with self.assertLogs("apps.core.middleware", level="ERROR") as captured:
                response = self.client.post(
                    reverse("owner-panel:login"),
                    {"password": "wrong"},
                )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Private login limiter unavailable", "\n".join(captured.output))

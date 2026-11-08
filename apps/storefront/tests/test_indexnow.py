import json
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from urllib.error import HTTPError

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, override_settings

from apps.storefront.management.commands.notify_indexnow import (
    ENDPOINT,
    snapshot,
    valid_url,
)

BASE = "https://www.example.test"
KEY = "a" * 32
OPERATOR = {"name": "Example", "address": "Test address", "tax_id": "TEST"}
MODULE = "apps.storefront.management.commands.notify_indexnow"


@override_settings(
    PUBLIC_SITE_URL=BASE, PUBLIC_INDEXING_ENABLED=True, PUBLIC_OPERATOR=OPERATOR,
    INDEXNOW_KEY=KEY, ALLOWED_HOSTS=["www.example.test", "other.example.test"],
)
class IndexNowTests(SimpleTestCase):
    def test_proof_only_on_public_host_and_exact_key(self):
        response = self.client.get(f"/indexnow-{KEY}.txt", HTTP_HOST="www.example.test")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, KEY.encode())
        self.assertIn("noindex", response["X-Robots-Tag"])
        self.assertEqual(self.client.get(
            f"/indexnow-{KEY}.txt", HTTP_HOST="other.example.test").status_code, 404)
        self.assertEqual(self.client.get(
            f"/indexnow-{'b' * 32}.txt", HTTP_HOST="www.example.test").status_code, 404)

    def test_private_foreign_query_and_legacy_urls_rejected(self):
        for path in ("/painel/", "/admin/", "/go/1/", "/?q=a", "/#x", "/products/a/?x=1"):
            self.assertFalse(valid_url(BASE + path, BASE))
        self.assertFalse(valid_url("https://evil.test/", BASE))
        self.assertTrue(valid_url(BASE + "/products/hifu/", BASE))

    @patch(MODULE + ".fetch")
    def test_snapshot_ignores_csrf_randomness_and_detects_content_change(self, fetch):
        xml = (f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
               f'<url><loc>{BASE}/</loc></url></urlset>').encode()
        def response(token, content="Equipment"):
            return (f'<link rel="canonical" href="{BASE}/"><meta name="robots" '
                    f'content="index, follow"><input type="hidden" name="csrfmiddlewaretoken" '
                    f'value="{token}"><main>{content}</main>').encode()
        fetch.side_effect = [(200, {}, xml), (200, {}, response("one")),
                             (200, {}, xml), (200, {}, response("two")),
                             (200, {}, xml), (200, {}, response("three", "Updated"))]
        first = snapshot(BASE)
        self.assertEqual(first, snapshot(BASE))
        self.assertNotEqual(first, snapshot(BASE))

    @patch(MODULE + ".fetch")
    def test_snapshot_refuses_noindex_and_private_sitemap(self, fetch):
        for path in ("/", "/admin/"):
            xml = (f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                   f'<url><loc>{BASE}{path}</loc></url></urlset>').encode()
            html = (f'<link rel="canonical" href="{BASE}/">'
                    '<meta name="robots" content="noindex">').encode()
            fetch.side_effect = [(200, {}, xml), (200, {}, html)]
            with self.assertRaises(CommandError):
                snapshot(BASE)

    def run_notify(self, current, previous=None, status=200, dry_run=False):
        with TemporaryDirectory() as directory, override_settings(BASE_DIR=Path(directory)):
            state = Path(directory) / ".indexnow" / "accepted.json"
            state.parent.mkdir()
            if previous is not None:
                state.write_text(json.dumps(previous))
            output = StringIO()
            with patch(MODULE + ".snapshot", return_value=current), patch(
                MODULE + ".fetch", side_effect=[(200, {}, KEY.encode()), (status, {}, b"")]
            ) as fetch:
                call_command("notify_indexnow", dry_run=dry_run, stdout=output)
                stored = json.loads(state.read_text()) if state.exists() else None
                return stored, fetch.call_args_list, output.getvalue()

    def test_accepted_only_changed_and_formerly_public_removed_pages(self):
        current = {BASE + "/": "new"}
        previous = {BASE + "/": "old", BASE + "/products/hifu/": "old"}
        stored, calls, output = self.run_notify(current, previous)
        self.assertEqual(stored, current)
        self.assertEqual(calls[-1].args[0], ENDPOINT)
        payload = json.loads(calls[-1].args[1])
        self.assertEqual(payload["urlList"], [BASE + "/", BASE + "/products/hifu/"])
        self.assertIn("index_inclusion=unconfirmed", output)

    def test_unchanged_does_not_repeat_submission(self):
        current = {BASE + "/": "same"}
        stored, calls, output = self.run_notify(current, current)
        self.assertEqual(stored, current)
        self.assertEqual(calls, [])
        self.assertIn("UNCHANGED", output)

    def test_202_keeps_state_pending_key_verification(self):
        previous = {BASE + "/": "old"}
        stored, _, output = self.run_notify({BASE + "/": "new"}, previous, status=202)
        self.assertEqual(stored, previous)
        self.assertIn("key_verification=pending", output)

    def test_dry_run_does_not_submit_or_persist(self):
        stored, calls, _ = self.run_notify({BASE + "/": "new"}, dry_run=True)
        self.assertIsNone(stored)
        self.assertEqual(calls, [])

    @patch(MODULE + ".snapshot", return_value={BASE + "/": "new"})
    @patch(MODULE + ".fetch")
    def test_failed_submission_keeps_state_and_does_not_log_key(self, fetch, snapshot_mock):
        fetch.side_effect = [(200, {}, KEY.encode()),
                             HTTPError(ENDPOINT + "?key=" + KEY, 429, "limited", {}, None)]
        with TemporaryDirectory() as directory, override_settings(BASE_DIR=Path(directory)):
            with self.assertRaises(CommandError) as caught:
                call_command("notify_indexnow")
            self.assertNotIn(KEY, str(caught.exception))
            self.assertFalse((Path(directory) / ".indexnow/accepted.json").exists())

    @override_settings(PUBLIC_INDEXING_ENABLED=False)
    def test_disabled_site_cannot_notify_or_expose_key(self):
        with self.assertRaises(CommandError):
            call_command("notify_indexnow")
        self.assertEqual(self.client.get(
            f"/indexnow-{KEY}.txt", HTTP_HOST="www.example.test").status_code, 404)

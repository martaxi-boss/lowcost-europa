"""The Google-visible storefront favicon is present, square and crawlable."""
import struct

from django.conf import settings
from django.test import SimpleTestCase


class PublicFaviconTests(SimpleTestCase):
    def test_base_template_declares_google_compatible_favicon(self):
        template = (
            settings.BASE_DIR / "apps/storefront/templates/storefront/base.html"
        ).read_text(encoding="utf-8")
        self.assertIn('rel="icon" type="image/png" sizes="96x96"', template)
        self.assertIn(
            "{% static 'storefront/lowcost-europa-favicon.png' %}",
            template,
        )

    def test_favicon_asset_is_valid_square_96px_png(self):
        favicon = (
            settings.BASE_DIR
            / "apps/storefront/static/storefront/lowcost-europa-favicon.png"
        ).read_bytes()
        self.assertEqual(favicon[:8], bytes.fromhex("89504e470d0a1a0a"))
        self.assertEqual(struct.unpack(">II", favicon[16:24]), (96, 96))

    def test_root_favicon_responds_directly_with_existing_branded_png(self):
        result = self.client.get("/favicon.ico")
        expected = (
            settings.BASE_DIR
            / "apps/storefront/static/storefront/lowcost-europa-favicon.png"
        ).read_bytes()
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result["Content-Type"], "image/png")
        self.assertEqual(result["Cache-Control"], "public, max-age=86400")
        self.assertEqual(result.content, expected)

    def test_root_favicon_supports_head_but_never_accepts_post(self):
        self.assertEqual(self.client.head("/favicon.ico").status_code, 200)
        self.assertEqual(self.client.post("/favicon.ico").status_code, 405)

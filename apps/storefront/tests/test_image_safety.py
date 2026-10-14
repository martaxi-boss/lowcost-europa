from django.conf import settings
from django.test import SimpleTestCase


class StorefrontImageSafetyTests(SimpleTestCase):
    def test_image_fallback_is_same_origin_and_non_tracking(self):
        base = (
            settings.BASE_DIR / "apps/storefront/templates/storefront/base.html"
        ).read_text()
        script = (
            settings.BASE_DIR / "apps/storefront/static/storefront/product-images.js"
        ).read_text()
        self.assertIn("storefront/product-images.js", base)
        self.assertIn("data-product-image", script)
        self.assertIn('image.addEventListener("error", showFallback)', script)
        self.assertIn("image.naturalWidth", script)
        self.assertNotIn("fetch(", script)
        self.assertNotIn("XMLHttpRequest", script)

    def test_public_image_markup_has_real_source_and_recovery(self):
        directory = settings.BASE_DIR / "apps/storefront/templates/storefront/components"
        for filename in ("offer_card.html", "product_family_card.html"):
            with self.subTest(filename=filename):
                template = (directory / filename).read_text()
                self.assertIn('image_url|slice:":8" == "https://"', template)
                self.assertNotIn('image_url|slice:":7" == "http://"', template)
                self.assertIn("data-product-image", template)
                self.assertIn("data-image-fallback hidden", template)
                self.assertIn("data-image-quality hidden", template)

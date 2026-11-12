"""Exclude fallback image notices from Google snippets without changing UI."""
import re

from django.conf import settings
from django.test import SimpleTestCase


class SearchSnippetImageNoticeTests(SimpleTestCase):
    TEMPLATE_PATHS = (
        "apps/storefront/templates/storefront/home.html",
        "apps/storefront/templates/storefront/components/product_family_card.html",
        "apps/storefront/templates/storefront/components/offer_card.html",
    )

    def test_fallback_notices_are_excluded_from_search_snippets(self):
        for path in self.TEMPLATE_PATHS:
            with self.subTest(path=path):
                template = (settings.BASE_DIR / path).read_text(encoding="utf-8")
                notices = re.findall(
                    r'<span\\b[^>]*class="image-(?:fallback|quality-note)"[^>]*>',
                    template,
                )
                self.assertTrue(notices, "Expected image notice elements")
                for notice in notices:
                    self.assertIn("data-nosnippet", notice)
                    self.assertIn("hidden", notice)

    def test_placeholder_notices_are_excluded_from_search_snippets(self):
        path = self.TEMPLATE_PATHS[1]
        template = (settings.BASE_DIR / path).read_text(encoding="utf-8")
        placeholders = re.findall(
            r'<div\\b[^>]*class="product-card__media product-card__media--placeholder"[^>]*>',
            template,
        )
        self.assertEqual(len(placeholders), 2)
        self.assertTrue(all("data-nosnippet" in tag for tag in placeholders))

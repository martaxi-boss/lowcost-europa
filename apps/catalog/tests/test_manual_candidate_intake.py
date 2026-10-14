from decimal import Decimal
from unittest.mock import Mock, patch
from urllib import request

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.catalog.models import CandidateDecision, Offer, OfferCandidate, ProductFamily
from apps.catalog.services.manual_candidate_intake import (
    ManualCandidateIntakeError,
    ManualCandidateIntakeResult,
    _AliExpressOnlyRedirectHandler,
    intake_manual_aliexpress_candidate,
    resolve_aliexpress_product_url,
)
from apps.integrations.aliexpress.types import AliExpressProduct


class FakeResponse:
    def __init__(self, url):
        self.url = url

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def geturl(self):
        return self.url


class ManualCandidateIntakeServiceTests(TestCase):
    def setUp(self):
        self.family = ProductFamily.objects.create(
            name="Pressoterapia / RF Tecar",
            slug="pressoterapia-vacuum-drenagem",
        )
        self.other_family = ProductFamily.objects.create(
            name="HIFU",
            slug="hifu-manual",
        )
        self.product_id = "1005001234567890"
        self.canonical = f"https://www.aliexpress.com/item/{self.product_id}.html"

    def detail(self):
        return AliExpressProduct(
            product_id=self.product_id,
            title="Professional TECAR Therapy Machine",
            image_url="https://ae01.alicdn.com/kf/example.jpg",
            product_url="https://www.aliexpress.com/item/1005001234567890.html?tracking=third",
            price=Decimal("1299.50"),
            original_price=Decimal("1499.00"),
            currency="EUR",
            evaluation_rate_percent=Decimal("98.70"),
            sales_count=44,
            commission_rate=Decimal("7.5000"),
            ship_to_days_raw="Ship to PT in 5 Days",
            delivery_days=5,
            destination_country="PT",
        )

    def resolver(self, _url):
        return self.product_id, self.canonical

    def fake_client(self):
        client = Mock()
        client.get_product_detail.return_value = self.detail()
        client.generate_affiliate_link.return_value = "https://s.click.aliexpress.com/ours"
        return client

    def test_short_link_resolves_to_canonical_product_without_tracking(self):
        opener = Mock(
            return_value=FakeResponse(
                "https://www.aliexpress.com/item/1005001234567890.html"
                "?aff_fcid=third-party"
            )
        )
        product_id, canonical = resolve_aliexpress_product_url(
            "https://s.click.aliexpress.com/e/_Example",
            opener=opener,
        )
        self.assertEqual(product_id, self.product_id)
        self.assertEqual(canonical, self.canonical)
        self.assertNotIn("aff_", canonical)

    def test_rejects_non_aliexpress_url_before_network(self):
        opener = Mock()
        with self.assertRaises(ManualCandidateIntakeError):
            resolve_aliexpress_product_url(
                "https://example.com/item/1005001234567890.html", opener=opener
            )
        opener.assert_not_called()

    def test_http_short_link_does_not_make_network_request(self):
        opener = Mock()
        with self.assertRaises(ManualCandidateIntakeError):
            resolve_aliexpress_product_url(
                "http://s.click.aliexpress.com/e/_Example", opener=opener
            )
        opener.assert_not_called()

    def test_direct_product_id_is_canonicalized_without_opening_http(self):
        opener = Mock()
        result = resolve_aliexpress_product_url(
            f"http://www.aliexpress.com/item/{self.product_id}.html",
            opener=opener,
        )
        self.assertEqual(result, (self.product_id, self.canonical))
        opener.assert_not_called()

    def test_redirects_reject_other_hosts_non_https_and_credentials(self):
        handler = _AliExpressOnlyRedirectHandler()
        original = request.Request("https://s.click.aliexpress.com/e/_Example")
        for redirected in (
            "https://127.0.0.1/admin",
            "http://www.aliexpress.com/item/123.html",
            "https://www.aliexpress.com:8080/item/123.html",
            "https://user:secret@www.aliexpress.com/item/123.html",
            "https://evil-aliexpress.com/item/123.html",
        ):
            with self.subTest(redirected=redirected):
                with self.assertRaises(ManualCandidateIntakeError):
                    handler.redirect_request(
                        original, None, 302, "Found", {}, redirected
                    )

    def test_redirects_accept_https_aliexpress_product_destinations(self):
        handler = _AliExpressOnlyRedirectHandler()
        original = request.Request("https://s.click.aliexpress.com/e/_Example")
        resolved = handler.redirect_request(
            original, None, 302, "Found", {}, self.canonical
        )
        self.assertEqual(resolved.full_url, self.canonical)

    def test_default_short_link_uses_safe_redirect_handler(self):
        with patch(
            "apps.catalog.services.manual_candidate_intake.request.build_opener"
        ) as builder:
            builder.return_value.open.return_value = FakeResponse(self.canonical)
            product_id, canonical = resolve_aliexpress_product_url(
                "https://s.click.aliexpress.com/e/_Example"
            )
        self.assertEqual((product_id, canonical), (self.product_id, self.canonical))
        handler = builder.call_args.args[0]
        self.assertIsInstance(handler, _AliExpressOnlyRedirectHandler)

    def test_malformed_urls_fail_cleanly_without_network(self):
        opener = Mock()
        for bad in (
            "https://[::1",
            "https://[www.aliexpress.com/e/_short",
            "https://s.click.aliexpress.com:invalid/e/_short",
            "https://s.click.aliexpress.com:0/e/_short",
        ):
            with self.subTest(url=bad):
                with self.assertRaises(ManualCandidateIntakeError):
                    resolve_aliexpress_product_url(bad, opener=opener)
        opener.assert_not_called()

    def test_creates_pending_candidate_from_official_detail_without_affiliate_generation(self):
        client = self.fake_client()

        result = intake_manual_aliexpress_candidate(
            url="https://s.click.aliexpress.com/e/_Example",
            family=self.family,
            client=client,
            resolver=self.resolver,
        )

        self.assertEqual(result.outcome, "CREATED")
        candidate = result.candidate
        self.assertEqual(candidate.status, OfferCandidate.Status.PENDING)
        self.assertEqual(candidate.product_family, self.family)
        self.assertEqual(candidate.source, Offer.Source.ALIEXPRESS)
        self.assertEqual(candidate.external_product_id, self.product_id)
        self.assertEqual(candidate.product_url, self.canonical)
        self.assertEqual(candidate.title, "Professional TECAR Therapy Machine")
        self.assertEqual(candidate.price, Decimal("1299.50"))
        self.assertEqual(candidate.currency, "EUR")
        self.assertEqual(candidate.evaluation_rate_percent, Decimal("98.70"))
        self.assertEqual(candidate.sales_count, 44)
        self.assertEqual(candidate.commission_rate, Decimal("7.5000"))
        self.assertEqual(candidate.detail_delivery_days, 5)
        self.assertIsNone(candidate.search_delivery_days)
        client.get_product_detail.assert_called_once_with(self.product_id, "PT", "EUR")
        client.generate_affiliate_link.assert_not_called()
        self.assertEqual(Offer.objects.count(), 0)
        self.assertEqual(CandidateDecision.objects.count(), 0)

    def test_affiliate_generation_is_never_attempted_during_manual_intake(self):
        client = self.fake_client()
        client.generate_affiliate_link.side_effect = AssertionError(
            "manual intake must not generate affiliate links"
        )

        result = intake_manual_aliexpress_candidate(
            url=self.canonical,
            family=self.family,
            client=client,
            resolver=self.resolver,
        )

        self.assertEqual(result.candidate.status, OfferCandidate.Status.PENDING)
        client.generate_affiliate_link.assert_not_called()
        self.assertEqual(Offer.objects.count(), 0)
        self.assertEqual(CandidateDecision.objects.count(), 0)

    def test_existing_pending_candidate_is_not_duplicated(self):
        existing = OfferCandidate.objects.create(
            product_family=self.family,
            source=Offer.Source.ALIEXPRESS,
            external_product_id=self.product_id,
            status=OfferCandidate.Status.PENDING,
        )
        client = self.fake_client()

        result = intake_manual_aliexpress_candidate(
            url=self.canonical,
            family=self.family,
            client=client,
            resolver=self.resolver,
        )

        self.assertEqual(result.outcome, "ALREADY_PENDING")
        self.assertEqual(result.candidate, existing)
        self.assertEqual(OfferCandidate.objects.count(), 1)
        client.get_product_detail.assert_not_called()

    def test_existing_candidate_in_other_family_is_reported_not_moved(self):
        existing = OfferCandidate.objects.create(
            product_family=self.other_family,
            source=Offer.Source.ALIEXPRESS,
            external_product_id=self.product_id,
            status=OfferCandidate.Status.REJECTED,
        )

        result = intake_manual_aliexpress_candidate(
            url=self.canonical,
            family=self.family,
            client=self.fake_client(),
            resolver=self.resolver,
        )

        self.assertEqual(result.outcome, "ALREADY_REJECTED_OTHER_FAMILY")
        existing.refresh_from_db()
        self.assertEqual(existing.product_family, self.other_family)

    def test_existing_offer_blocks_candidate_creation(self):
        offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id=self.product_id,
            product_url=self.canonical,
        )

        result = intake_manual_aliexpress_candidate(
            url=self.canonical,
            family=self.family,
            client=self.fake_client(),
            resolver=self.resolver,
        )

        self.assertEqual(result.outcome, "OFFER_EXISTS")
        self.assertEqual(result.offer, offer)
        self.assertEqual(OfferCandidate.objects.count(), 0)


class ManualCandidateIntakeOwnerPanelTests(TestCase):
    def setUp(self):
        self.family = ProductFamily.objects.create(
            name="Pressoterapia / RF Tecar",
            slug="pressoterapia-vacuum-drenagem",
        )
        self.staff = get_user_model().objects.create_user(
            username="owner-manual-intake",
            password="x",
            is_staff=True,
        )
        self.client.force_login(self.staff)

    def test_family_review_page_shows_manual_intake_form(self):
        response = self.client.get(
            reverse("owner-panel:family", args=[self.family.slug]) + "?vista=rever"
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Adicionar produto manual")
        self.assertContains(response, "ADICIONAR A REVER")

    @patch("apps.catalog.owner_panel_views.intake_manual_aliexpress_candidate")
    def test_post_created_candidate_redirects_to_review(self, intake):
        candidate = OfferCandidate.objects.create(
            product_family=self.family,
            source=Offer.Source.ALIEXPRESS,
            external_product_id="manual-ui",
            status=OfferCandidate.Status.PENDING,
        )
        intake.return_value = ManualCandidateIntakeResult(
            outcome="CREATED",
            external_product_id="manual-ui",
            candidate=candidate,
        )

        response = self.client.post(
            reverse("owner-panel:manual-candidate-intake", args=[self.family.slug]),
            {"product_url": "https://s.click.aliexpress.com/e/_Example"},
        )

        self.assertRedirects(
            response,
            reverse("owner-panel:family", args=[self.family.slug]) + "?vista=rever",
            fetch_redirect_response=False,
        )
        intake.assert_called_once_with(
            url="https://s.click.aliexpress.com/e/_Example",
            family=self.family,
        )

    def test_non_staff_cannot_submit_manual_product(self):
        user = get_user_model().objects.create_user(username="plain-user", password="x")
        self.client.force_login(user)
        response = self.client.post(
            reverse("owner-panel:manual-candidate-intake", args=[self.family.slug]),
            {"product_url": "https://www.aliexpress.com/item/1005001234567890.html"},
        )
        self.assertEqual(response.status_code, 403)

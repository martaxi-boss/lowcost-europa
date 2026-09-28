from datetime import timedelta
from unittest.mock import Mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import (
    Offer,
    OfferCandidate,
    OfferClick,
    OfferFamilyPlacement,
    ProductFamily,
)
from apps.catalog.services.candidate_approval import approve_candidate, revalidate_candidate
from apps.catalog.services.offer_maintenance import maintain_catalog_offers
from apps.catalog.services.public_eligibility import public_eligibility_q
from apps.integrations.aliexpress.exceptions import AliExpressAPIError, AliExpressTransportError
from apps.integrations.aliexpress.types import AliExpressProduct


class AffiliatePromotionGateTests(TestCase):
    def setUp(self):
        created_at = timezone.now()
        self.family = ProductFamily.objects.create(name="HIFU", slug="promo-hifu")
        self.offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="promo-1",
            title="Promotion test",
            product_url="https://www.aliexpress.com/item/1005000000000001.html",
            affiliate_url="https://affiliate.example/old",
            affiliate_promotion_status=Offer.AffiliatePromotionStatus.ELIGIBLE,
            affiliate_promotion_verified_at=created_at,
            ship_from_country="PL",
            ship_from_verified_at=created_at,
            protocol_verified_at=created_at,
            is_active=True,
            owner_hidden=False,
        )
        OfferFamilyPlacement.objects.create(offer=self.offer, product_family=self.family)
        self.now = timezone.now() + timedelta(seconds=1)

    def detail(self):
        return AliExpressProduct(
            product_id=self.offer.external_product_id,
            title=self.offer.title,
            product_url=self.offer.product_url,
            currency="EUR",
        )

    def test_eligible_with_remaining_conditions_is_public(self):
        self.assertTrue(
            Offer.objects.filter(pk=self.offer.pk).filter(public_eligibility_q(self.now)).exists()
        )

    def test_ineligible_is_not_public_and_go_is_404_without_click(self):
        self.offer.affiliate_promotion_status = Offer.AffiliatePromotionStatus.INELIGIBLE
        self.offer.affiliate_promotion_verified_at = self.now
        self.offer.save(
            update_fields=[
                "affiliate_promotion_status",
                "affiliate_promotion_verified_at",
            ]
        )
        self.assertFalse(
            Offer.objects.filter(pk=self.offer.pk).filter(public_eligibility_q(self.now)).exists()
        )
        response = self.client.get(reverse("storefront:offer-go", args=[self.offer.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(OfferClick.objects.filter(offer=self.offer).count(), 0)

    def test_unknown_is_fail_closed(self):
        self.offer.affiliate_promotion_status = Offer.AffiliatePromotionStatus.UNKNOWN
        self.offer.affiliate_promotion_verified_at = None
        self.offer.save(
            update_fields=[
                "affiliate_promotion_status",
                "affiliate_promotion_verified_at",
            ]
        )
        self.assertFalse(
            Offer.objects.filter(pk=self.offer.pk).filter(public_eligibility_q(self.now)).exists()
        )

    def test_maintenance_eligible_to_ineligible_preserves_editorial_state(self):
        client = Mock()
        client.generate_affiliate_link.side_effect = AliExpressAPIError(
            "AliExpress API error 100: "
            "This item cannot be sold or promoted in the selected country."
        )
        client.get_product_detail.return_value = self.detail()

        result = maintain_catalog_offers(batch_size=1, client=client, now=self.now)

        self.offer.refresh_from_db()
        self.assertEqual(
            self.offer.affiliate_promotion_status,
            Offer.AffiliatePromotionStatus.INELIGIBLE,
        )
        self.assertEqual(self.offer.affiliate_promotion_verified_at, self.now)
        self.assertFalse(self.offer.owner_hidden)
        self.assertEqual(result.promotion_ineligible, 1)
        self.assertEqual(result.promotion_transient_failures, 0)

    def test_transient_promotion_error_preserves_last_confirmed_state(self):
        verified_at = self.offer.affiliate_promotion_verified_at
        client = Mock()
        client.generate_affiliate_link.side_effect = AliExpressTransportError("temporary")
        client.get_product_detail.return_value = self.detail()

        result = maintain_catalog_offers(batch_size=1, client=client, now=self.now)

        self.offer.refresh_from_db()
        self.assertEqual(
            self.offer.affiliate_promotion_status,
            Offer.AffiliatePromotionStatus.ELIGIBLE,
        )
        self.assertEqual(self.offer.affiliate_promotion_verified_at, verified_at)
        self.assertEqual(result.promotion_transient_failures, 1)

    def test_future_recovery_does_not_auto_unhide_editorially_hidden_offer(self):
        self.offer.affiliate_promotion_status = Offer.AffiliatePromotionStatus.INELIGIBLE
        self.offer.owner_hidden = True
        self.offer.save(update_fields=["affiliate_promotion_status", "owner_hidden"])
        client = Mock()
        client.generate_affiliate_link.return_value = "https://affiliate.example/refreshed"
        client.get_product_detail.return_value = self.detail()

        result = maintain_catalog_offers(batch_size=1, client=client, now=self.now)

        self.offer.refresh_from_db()
        self.assertEqual(
            self.offer.affiliate_promotion_status,
            Offer.AffiliatePromotionStatus.ELIGIBLE,
        )
        self.assertTrue(self.offer.owner_hidden)
        self.assertEqual(self.offer.affiliate_url, "https://affiliate.example/refreshed")
        self.assertEqual(result.promotion_eligible, 1)

    def test_exact_product_url_and_identity_are_preserved(self):
        original_id = self.offer.external_product_id
        original_url = self.offer.product_url
        client = Mock()
        client.generate_affiliate_link.return_value = "https://affiliate.example/refreshed"
        client.get_product_detail.return_value = self.detail()

        maintain_catalog_offers(batch_size=1, client=client, now=self.now)

        self.offer.refresh_from_db()
        client.generate_affiliate_link.assert_called_once_with(original_url)
        self.assertEqual(self.offer.external_product_id, original_id)
        self.assertEqual(self.offer.product_url, original_url)

    def test_approval_refreshes_existing_ineligible_then_revalidation_preserves_promotion(self):
        user = get_user_model().objects.create_user(
            username="promotion-staff", password="x", is_staff=True
        )
        self.offer.affiliate_promotion_status = Offer.AffiliatePromotionStatus.INELIGIBLE
        self.offer.affiliate_promotion_verified_at = self.now - timedelta(days=1)
        self.offer.owner_hidden = True
        self.offer.save(
            update_fields=[
                "affiliate_promotion_status",
                "affiliate_promotion_verified_at",
                "owner_hidden",
            ]
        )
        candidate = OfferCandidate.objects.create(
            product_family=self.family,
            source=Offer.Source.ALIEXPRESS,
            external_product_id=self.offer.external_product_id,
            product_url=self.offer.product_url,
            status=OfferCandidate.Status.PENDING,
        )
        client = Mock()
        client.generate_affiliate_link.return_value = "https://affiliate.example/approval-fresh"

        result = approve_candidate(
            candidate,
            user=user,
            ship_from_country="PL",
            client=client,
            now=self.now,
        )
        client.generate_affiliate_link.assert_called_once_with(candidate.product_url)
        revalidate_candidate(result.candidate, user=user, now=self.now + timedelta(seconds=1))

        self.offer.refresh_from_db()
        self.assertEqual(self.offer.affiliate_url, "https://affiliate.example/approval-fresh")
        self.assertEqual(
            self.offer.affiliate_promotion_status,
            Offer.AffiliatePromotionStatus.ELIGIBLE,
        )
        self.assertEqual(self.offer.affiliate_promotion_verified_at, self.now)
        self.assertTrue(self.offer.owner_hidden)

    def test_owner_panel_distinguishes_promotion_ineligible(self):
        user = get_user_model().objects.create_user(
            username="panel-staff", password="x", is_staff=True
        )
        self.offer.affiliate_promotion_status = Offer.AffiliatePromotionStatus.INELIGIBLE
        self.offer.save(update_fields=["affiliate_promotion_status"])
        self.client.force_login(user)
        response = self.client.get(
            reverse("owner-panel:family", args=[self.family.slug]) + "?vista=nao-promovivel"
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Não elegível para promoção / afiliado")

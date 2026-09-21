from datetime import timedelta
from unittest.mock import Mock

from django.test import TestCase
from django.utils import timezone

from apps.catalog.models import Offer, OfferFamilyPlacement, OfferObservation, ProductFamily
from apps.catalog.services.offer_maintenance import (
    is_factually_unavailable,
    maintain_catalog_offers,
    select_maintenance_batch,
)
from apps.catalog.services.public_eligibility import public_eligibility_q
from apps.integrations.aliexpress.exceptions import (
    AliExpressAPIError,
    AliExpressRateLimitError,
    AliExpressTransportError,
)
from apps.integrations.aliexpress.types import AliExpressProduct


class OfferMaintenanceTests(TestCase):
    def make_offer(self, external_id, *, checked_at=None, protocol_at=None, is_active=True):
        offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id=external_id,
            title=f"Offer {external_id}",
            product_url=f"https://example.com/{external_id}",
            affiliate_url=f"https://affiliate.example/{external_id}",
            affiliate_promotion_status=Offer.AffiliatePromotionStatus.ELIGIBLE,
            affiliate_promotion_verified_at=checked_at or timezone.now(),
            ship_from_country="PL",
            ship_from_verified_at=protocol_at,
            protocol_verified_at=protocol_at,
            is_active=is_active,
        )
        if checked_at:
            OfferObservation.objects.create(offer=offer, observed_at=checked_at)
        return offer

    def detail(self, product_id, *, status=None):
        return AliExpressProduct(
            product_id=product_id,
            title=f"Updated {product_id}",
            product_url=f"https://example.com/{product_id}",
            image_url=f"https://img.example/{product_id}.jpg",
            currency="EUR",
            availability_raw=status,
        )

    def test_oldest_factual_check_is_selected_first_and_batch_is_bounded(self):
        now = timezone.now()
        never = self.make_offer("never")
        old = self.make_offer("old", checked_at=now - timedelta(days=5))
        self.make_offer("new", checked_at=now - timedelta(hours=1))
        selected = select_maintenance_batch(2)
        self.assertEqual([offer.pk for offer in selected], [never.pk, old.pk])

    def test_inactive_offer_is_not_selected_for_normal_maintenance(self):
        inactive = self.make_offer("inactive", is_active=False)
        active = self.make_offer("active")

        selected = select_maintenance_batch(10)

        self.assertIn(active, selected)
        self.assertNotIn(inactive, selected)

    def test_inactive_offer_is_never_auto_reactivated(self):
        inactive = self.make_offer("inactive", is_active=False)
        active = self.make_offer("active")
        client = Mock()
        client.generate_affiliate_link.return_value = "https://affiliate.example/refreshed"
        client.get_product_detail.return_value = self.detail("active")

        maintain_catalog_offers(batch_size=1, client=client)

        inactive.refresh_from_db()
        active.refresh_from_db()
        self.assertFalse(inactive.is_active)
        self.assertTrue(active.is_active)
        client.get_product_detail.assert_called_once_with("active", "PT", "EUR")

    def test_available_stays_active_and_protocol_timestamp_is_not_renewed(self):
        protocol_at = timezone.now() - timedelta(days=3)
        offer = self.make_offer("available", protocol_at=protocol_at)
        client = Mock()
        client.generate_affiliate_link.return_value = "https://affiliate.example/refreshed"
        client.get_product_detail.return_value = self.detail("available")
        result = maintain_catalog_offers(batch_size=1, client=client, now=timezone.now())
        offer.refresh_from_db()
        self.assertTrue(offer.is_active)
        self.assertEqual(offer.protocol_verified_at, protocol_at)
        self.assertEqual(result.available_confirmed, 1)
        self.assertEqual(offer.observations.latest("observed_at").availability, "AVAILABLE")

    def test_factual_unavailable_deactivates_and_records_unavailable(self):
        offer = self.make_offer("gone", protocol_at=timezone.now())
        client = Mock()
        client.generate_affiliate_link.return_value = "https://affiliate.example/refreshed"
        client.get_product_detail.return_value = self.detail("gone", status="unavailable")
        result = maintain_catalog_offers(batch_size=1, client=client)
        offer.refresh_from_db()
        self.assertFalse(offer.is_active)
        self.assertEqual(result.unavailable_confirmed, 1)
        self.assertEqual(result.offers_deactivated, 1)
        self.assertEqual(offer.observations.latest("observed_at").availability, "UNAVAILABLE")

    def test_generic_api_and_transport_errors_are_transient(self):
        for index, error_type in enumerate((AliExpressAPIError, AliExpressTransportError)):
            with self.subTest(error_type=error_type.__name__):
                offer = self.make_offer(f"transient-{index}", protocol_at=timezone.now())
                client = Mock()
                client.generate_affiliate_link.return_value = (
                    "https://affiliate.example/refreshed"
                )
                client.get_product_detail.side_effect = error_type("temporary")

                result = maintain_catalog_offers(batch_size=1, client=client)

                offer.refresh_from_db()
                self.assertTrue(offer.is_active)
                self.assertEqual(result.transient_failures, 1)
                self.assertEqual(result.offers_deactivated, 0)
                self.assertEqual(
                    offer.observations.latest("observed_at").availability,
                    "UNKNOWN",
                )

    def test_rate_limit_breaker_aborts_batch_without_deactivation(self):
        first = self.make_offer("rate-first", protocol_at=timezone.now())
        second = self.make_offer("rate-second", protocol_at=timezone.now())
        client = Mock()
        client.generate_affiliate_link.return_value = "https://affiliate.example/refreshed"
        client.get_product_detail.side_effect = AliExpressRateLimitError("429")

        with self.assertRaises(AliExpressRateLimitError):
            maintain_catalog_offers(batch_size=2, client=client)

        first.refresh_from_db()
        second.refresh_from_db()
        self.assertTrue(first.is_active)
        self.assertTrue(second.is_active)
        client.get_product_detail.assert_called_once_with("rate-first", "PT", "EUR")
        self.assertFalse(first.observations.exists())
        self.assertFalse(second.observations.exists())

    def test_all_factual_unavailable_values_are_recognized(self):
        statuses = (
            "unavailable",
            "not available",
            "no longer available",
            "offline",
            "removed",
            "deleted",
            "invalid",
        )
        for status in statuses:
            with self.subTest(status=status):
                self.assertTrue(is_factually_unavailable(self.detail("x", status=status)))

    def test_non_factual_values_are_not_treated_as_unavailable(self):
        for status in (None, "active", "available", "unknown"):
            with self.subTest(status=status):
                self.assertFalse(is_factually_unavailable(self.detail("x", status=status)))

    def test_maintenance_cannot_turn_family_cap_20_into_21(self):
        now = timezone.now()
        family = ProductFamily.objects.create(name="Cap family", slug="cap-family")
        for index in range(20):
            offer = self.make_offer(f"eligible-{index}", protocol_at=now)
            OfferFamilyPlacement.objects.create(offer=offer, product_family=family)
            OfferObservation.objects.create(offer=offer, observed_at=now)
        inactive = self.make_offer("inactive-old", protocol_at=now, is_active=False)
        OfferFamilyPlacement.objects.create(offer=inactive, product_family=family)

        maintenance_now = timezone.now() + timedelta(seconds=1)
        client = Mock()
        client.generate_affiliate_link.return_value = "https://affiliate.example/refreshed"
        client.get_product_detail.return_value = self.detail("eligible-0")
        maintain_catalog_offers(batch_size=1, client=client, now=maintenance_now)

        inactive.refresh_from_db()
        eligible = OfferFamilyPlacement.objects.filter(
            product_family=family,
            offer__in=Offer.objects.filter(public_eligibility_q(maintenance_now)),
        ).count()
        self.assertFalse(inactive.is_active)
        self.assertEqual(eligible, 20)

from datetime import timedelta
from unittest.mock import Mock

from django.test import TestCase
from django.utils import timezone

from apps.catalog.models import Offer, OfferObservation
from apps.catalog.services.offer_maintenance import (
    is_factually_unavailable,
    maintain_catalog_offers,
    select_maintenance_batch,
)
from apps.integrations.aliexpress.exceptions import AliExpressAPIError, AliExpressRateLimitError
from apps.integrations.aliexpress.types import AliExpressProduct


class OfferMaintenanceTests(TestCase):
    def make_offer(self, external_id, *, checked_at=None, protocol_at=None):
        offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id=external_id,
            title=f"Offer {external_id}",
            product_url=f"https://example.com/{external_id}",
            protocol_verified_at=protocol_at,
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

    def test_available_stays_active_and_protocol_timestamp_is_not_renewed(self):
        protocol_at = timezone.now() - timedelta(days=3)
        offer = self.make_offer("available", protocol_at=protocol_at)
        client = Mock()
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
        client.get_product_detail.return_value = self.detail("gone", status="unavailable")
        result = maintain_catalog_offers(batch_size=1, client=client)
        offer.refresh_from_db()
        self.assertFalse(offer.is_active)
        self.assertEqual(result.unavailable_confirmed, 1)
        self.assertEqual(result.offers_deactivated, 1)
        self.assertEqual(offer.observations.latest("observed_at").availability, "UNAVAILABLE")

    def test_generic_api_error_is_transient_and_never_deactivates(self):
        offer = self.make_offer("transient", protocol_at=timezone.now())
        client = Mock()
        client.get_product_detail.side_effect = AliExpressAPIError("temporary")
        result = maintain_catalog_offers(batch_size=1, client=client)
        offer.refresh_from_db()
        self.assertTrue(offer.is_active)
        self.assertEqual(result.transient_failures, 1)
        self.assertEqual(result.offers_deactivated, 0)
        self.assertEqual(offer.observations.latest("observed_at").availability, "UNKNOWN")

    def test_rate_limit_breaker_aborts_batch_without_deactivation(self):
        offer = self.make_offer("rate", protocol_at=timezone.now())
        client = Mock()
        client.get_product_detail.side_effect = AliExpressRateLimitError("429")
        with self.assertRaises(AliExpressRateLimitError):
            maintain_catalog_offers(batch_size=1, client=client)
        offer.refresh_from_db()
        self.assertTrue(offer.is_active)

    def test_unavailable_helper_is_conservative(self):
        self.assertTrue(is_factually_unavailable(self.detail("x", status="removed")))
        self.assertFalse(is_factually_unavailable(self.detail("x", status=None)))
        self.assertFalse(is_factually_unavailable(self.detail("x", status="active")))

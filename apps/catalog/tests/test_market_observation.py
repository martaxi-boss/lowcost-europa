from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
from unittest.mock import Mock

from django.test import TestCase, override_settings
from django.utils import timezone

from apps.catalog.models import Offer, OfferObservation
from apps.catalog.services.market_observation import observe_market_offers
from apps.catalog.services.observation_display import (
    build_observation_display,
    observation_history_queryset,
)
from apps.catalog.services.offer_maintenance import select_maintenance_batch
from apps.catalog.services.public_eligibility import public_eligibility_q
from apps.integrations.aliexpress.exceptions import (
    AliExpressError,
    AliExpressRateLimitError,
    AliExpressResponseError,
)
from apps.integrations.aliexpress.types import AliExpressProduct


@override_settings(PUBLIC_RECENT_PRICE_REQUIRED=True)
class MarketObservationTests(TestCase):
    def setUp(self):
        self.offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS, external_product_id="market-test",
            title="Editorial title", product_url="https://www.aliexpress.com/item/test.html",
            affiliate_url="https://s.click.aliexpress.com/e/_Test",
            affiliate_promotion_status=Offer.AffiliatePromotionStatus.ELIGIBLE,
            affiliate_promotion_verified_at=timezone.now(),
            protocol_verified_at=timezone.now(), is_active=True, owner_hidden=False,
        )
        self.client_api = Mock()
        self.client_api.get_product_detail.return_value = AliExpressProduct(
            product_id="market-test", title="Supplier title",
            destination_country="ES", price=Decimal("95.00"), currency="EUR",
        )

    def test_no_provider_requests_or_writes_without_explicit_persist(self):
        result = observe_market_offers(country="ES", client=self.client_api)
        self.assertEqual(result["selected"], 1)
        self.assertEqual(result["attempts"], 0)
        self.client_api.assert_not_called()
        self.client_api.get_product_detail.assert_not_called()
        self.assertEqual(OfferObservation.objects.count(), 0)

    def test_spanish_price_is_persisted_without_editorial_or_link_mutation(self):
        before = Offer.objects.values().get(pk=self.offer.pk)
        result = observe_market_offers(country="ES", persist=True, client=self.client_api)
        self.assertEqual(result["eur_prices"], 1)
        self.assertEqual(result["listing_signals"], 0)
        obs = OfferObservation.objects.get()
        self.assertEqual(obs.destination_country, "ES")
        self.assertEqual(obs.availability, OfferObservation.Availability.UNKNOWN)
        self.assertIsNone(obs.delivery_days)
        self.assertEqual(Offer.objects.values().get(pk=self.offer.pk), before)
        self.client_api.generate_affiliate_link.assert_not_called()
        self.assertFalse(Offer.objects.filter(public_eligibility_q()).exists())

    def test_spanish_observation_cannot_replace_portuguese_public_price(self):
        pt = OfferObservation.objects.create(
            offer=self.offer, destination_country="PT", price=Decimal("120.00"),
            currency="EUR", observed_at=timezone.now() - timedelta(minutes=5),
        )
        observe_market_offers(country="ES", persist=True, client=self.client_api)
        display = build_observation_display(self.offer.observations.all())
        self.assertEqual(display.price_observation.pk, pt.pk)
        self.assertEqual(list(observation_history_queryset()), [pt])
        self.assertTrue(Offer.objects.filter(public_eligibility_q()).exists())

    def test_market_response_mismatch_does_not_write(self):
        self.client_api.get_product_detail.return_value = replace(
            self.client_api.get_product_detail.return_value, destination_country="PT"
        )
        with self.assertRaises(AliExpressError):
            observe_market_offers(country="ES", persist=True, client=self.client_api)
        self.assertEqual(OfferObservation.objects.count(), 0)

    def test_rate_limit_aborts_without_fallback_or_fabricated_observation(self):
        self.client_api.get_product_detail.side_effect = AliExpressRateLimitError("stop")
        with self.assertRaises(AliExpressRateLimitError):
            observe_market_offers(country="ES", persist=True, client=self.client_api)
        self.assertEqual(self.client_api.get_product_detail.call_count, 1)
        self.assertEqual(OfferObservation.objects.count(), 0)

    def test_es_probe_does_not_postpone_portuguese_maintenance(self):
        old = timezone.now() - timedelta(days=3)
        OfferObservation.objects.create(offer=self.offer, destination_country="PT", observed_at=old)
        second = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS, external_product_id="second", is_active=True,
        )
        OfferObservation.objects.create(
            offer=second, destination_country="PT", observed_at=old + timedelta(days=1),
        )
        observe_market_offers(country="ES", persist=True, client=self.client_api)
        self.assertEqual(select_maintenance_batch(1)[0].pk, self.offer.pk)

    def test_bounds_and_market_rejected_before_calls(self):
        for country, limit in [("FR", 5), ("ES", 6), ("PT", 0)]:
            with self.assertRaises(ValueError):
                observe_market_offers(country=country, limit=limit, client=self.client_api)
        self.client_api.get_product_detail.assert_not_called()

    def test_unusable_supplier_response_is_unknown_without_starving_next_offer(self):
        second = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS, external_product_id="market-second",
            affiliate_url=self.offer.affiliate_url,
            affiliate_promotion_status=Offer.AffiliatePromotionStatus.ELIGIBLE,
            affiliate_promotion_verified_at=timezone.now(),
            protocol_verified_at=timezone.now(), is_active=True, owner_hidden=False,
        )
        self.client_api.get_product_detail.side_effect = [
            AliExpressResponseError("Missing required product identifier"),
            replace(self.client_api.get_product_detail.return_value, product_id="market-second"),
        ]
        result = observe_market_offers(country="ES", limit=2, persist=True, client=self.client_api)
        self.assertEqual(result["attempts"], 2)
        self.assertEqual(result["response_unconfirmed"], 1)
        self.assertEqual(result["eur_prices"], 1)
        unknown = OfferObservation.objects.get(offer=self.offer, destination_country="ES")
        self.assertIsNone(unknown.price)
        self.assertIsNone(unknown.delivery_days)
        self.assertEqual(unknown.availability, OfferObservation.Availability.UNKNOWN)
        self.assertEqual(OfferObservation.objects.get(offer=second).price, Decimal("95.00"))
        self.client_api.generate_affiliate_link.assert_not_called()

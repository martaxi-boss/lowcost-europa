from datetime import timedelta
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.utils import timezone

from apps.catalog.models import Offer, OfferObservation, ProductFamily


class ProductFamilyTests(TestCase):
    def test_slug_is_unique(self):
        ProductFamily.objects.create(name="HIFU", slug="hifu")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ProductFamily.objects.create(name="HIFU 2", slug="hifu")

    def test_invalid_lifecycle_status_is_rejected_by_database(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ProductFamily.objects.create(name="HIFU", slug="hifu", status="INVALID")

    def test_slug_cannot_be_blank(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ProductFamily.objects.create(name="HIFU", slug="")

    def test_family_can_exist_without_offers(self):
        family = ProductFamily.objects.create(name="HIFU", slug="hifu")
        self.assertEqual(family.offers.count(), 0)


class OfferTests(TestCase):
    def test_source_external_id_is_unique(self):
        Offer.objects.create(source=Offer.Source.ALIEXPRESS, external_product_id="123")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Offer.objects.create(source=Offer.Source.ALIEXPRESS, external_product_id="123")

    def test_external_id_cannot_be_blank(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Offer.objects.create(source=Offer.Source.ALIEXPRESS, external_product_id="")

    def test_invalid_source_is_rejected_by_database(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Offer.objects.create(source="INVALID", external_product_id="123")

    def test_last_seen_cannot_precede_first_seen(self):
        first_seen = timezone.now()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Offer.objects.create(
                    source=Offer.Source.ALIEXPRESS,
                    external_product_id="timeline-invalid",
                    first_seen_at=first_seen,
                    last_seen_at=first_seen - timedelta(days=1),
                )

    def test_offer_can_exist_without_family_and_be_linked_later(self):
        offer = Offer.objects.create(source=Offer.Source.ALIEXPRESS, external_product_id="123")
        self.assertIsNone(offer.product_family)
        family = ProductFamily.objects.create(name="HIFU", slug="hifu")
        offer.product_family = family
        offer.save(update_fields=["product_family"])
        offer.refresh_from_db()
        self.assertEqual(offer.product_family, family)

    def test_inactive_offer_is_preserved(self):
        offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS, external_product_id="123", is_active=False
        )
        self.assertFalse(Offer.objects.get(pk=offer.pk).is_active)

    def test_family_with_offer_is_protected_from_delete(self):
        family = ProductFamily.objects.create(name="HIFU", slug="hifu")
        Offer.objects.create(
            source=Offer.Source.ALIEXPRESS, external_product_id="123", product_family=family
        )
        with self.assertRaises(ProtectedError):
            family.delete()


class OfferObservationTests(TestCase):
    def setUp(self):
        self.offer = Offer.objects.create(source=Offer.Source.ALIEXPRESS, external_product_id="123")

    def test_unknown_fields_remain_none(self):
        obs = OfferObservation.objects.create(offer=self.offer)
        self.assertIsNone(obs.destination_country)
        self.assertIsNone(obs.price)
        self.assertIsNone(obs.evaluation_rate_percent)
        self.assertIsNone(obs.sales_count)
        self.assertIsNone(obs.currency)
        self.assertIsNone(obs.ship_to_days_raw)
        self.assertIsNone(obs.delivery_days)

    def test_percent_shipping_and_decimal_price_are_preserved(self):
        obs = OfferObservation.objects.create(
            offer=self.offer,
            price=Decimal("99.90"),
            evaluation_rate_percent=Decimal("96.50"),
            ship_to_days_raw="Ship to PT in 3 Days",
            delivery_days=3,
        )
        obs.refresh_from_db()
        self.assertEqual(obs.price, Decimal("99.90"))
        self.assertEqual(obs.evaluation_rate_percent, Decimal("96.50"))
        self.assertEqual(obs.ship_to_days_raw, "Ship to PT in 3 Days")
        self.assertEqual(obs.delivery_days, 3)

    def test_raw_shipping_can_exist_without_delivery_days(self):
        obs = OfferObservation.objects.create(
            offer=self.offer,
            ship_to_days_raw="Delivery estimate unavailable",
            delivery_days=None,
        )
        self.assertEqual(obs.ship_to_days_raw, "Delivery estimate unavailable")
        self.assertIsNone(obs.delivery_days)

    def test_unknown_and_unavailable_are_distinct(self):
        unknown = OfferObservation.objects.create(offer=self.offer)
        unavailable = OfferObservation.objects.create(
            offer=self.offer,
            availability=OfferObservation.Availability.UNAVAILABLE,
        )
        self.assertEqual(unknown.availability, OfferObservation.Availability.UNKNOWN)
        self.assertEqual(unavailable.availability, OfferObservation.Availability.UNAVAILABLE)

    def test_invalid_availability_is_rejected_by_database(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                OfferObservation.objects.create(offer=self.offer, availability="INVALID")

    def test_evaluation_rate_database_range(self):
        for invalid in (Decimal("-1"), Decimal("100.01")):
            with self.assertRaises(IntegrityError):
                with transaction.atomic():
                    OfferObservation.objects.create(
                        offer=self.offer, evaluation_rate_percent=invalid
                    )
        valid = OfferObservation.objects.create(
            offer=self.offer, evaluation_rate_percent=Decimal("96.5")
        )
        unknown = OfferObservation.objects.create(offer=self.offer, evaluation_rate_percent=None)
        self.assertEqual(valid.evaluation_rate_percent, Decimal("96.5"))
        self.assertIsNone(unknown.evaluation_rate_percent)

    def test_commission_rate_database_range(self):
        for invalid in (Decimal("-0.01"), Decimal("100.0001")):
            with self.assertRaises(IntegrityError):
                with transaction.atomic():
                    OfferObservation.objects.create(offer=self.offer, commission_rate=invalid)
        valid = OfferObservation.objects.create(offer=self.offer, commission_rate=Decimal("7.5"))
        unknown = OfferObservation.objects.create(offer=self.offer, commission_rate=None)
        self.assertEqual(valid.commission_rate, Decimal("7.5"))
        self.assertIsNone(unknown.commission_rate)

    def test_prices_cannot_be_negative_but_may_be_unknown(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                OfferObservation.objects.create(offer=self.offer, price=Decimal("-0.01"))
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                OfferObservation.objects.create(offer=self.offer, original_price=Decimal("-0.01"))
        unknown = OfferObservation.objects.create(offer=self.offer, price=None, original_price=None)
        self.assertIsNone(unknown.price)
        self.assertIsNone(unknown.original_price)

    def test_offer_with_observation_is_protected_from_delete(self):
        OfferObservation.objects.create(offer=self.offer)
        with self.assertRaises(ProtectedError):
            self.offer.delete()

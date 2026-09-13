from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase

from apps.catalog.models import Offer, OfferObservation, ProductFamily


class ProductFamilyTests(TestCase):
    def test_slug_is_unique(self):
        ProductFamily.objects.create(name="HIFU", slug="hifu")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ProductFamily.objects.create(name="HIFU 2", slug="hifu")

    def test_lifecycle_status_validation(self):
        family = ProductFamily(name="HIFU", slug="hifu", status="INVALID")
        with self.assertRaises(ValidationError):
            family.full_clean()

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

    def test_offer_with_observation_is_protected_from_delete(self):
        OfferObservation.objects.create(offer=self.offer)
        with self.assertRaises(ProtectedError):
            self.offer.delete()

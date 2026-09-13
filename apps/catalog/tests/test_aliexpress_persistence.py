from datetime import timedelta
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from django.db import IntegrityError, connection
from django.test import TransactionTestCase
from django.utils import timezone

from apps.catalog.models import Offer, OfferObservation, ProductFamily
from apps.catalog.services.aliexpress_persistence import import_aliexpress_product
from apps.integrations.aliexpress.exceptions import AliExpressAPIError, AliExpressResponseError
from apps.integrations.aliexpress.types import AliExpressProduct


class FakeClient:
    def __init__(self, products, affiliate_url="https://affiliate.example/item"):
        self.products = iter(products)
        self.affiliate_url = affiliate_url
        self.atomic_states = []
        self.link_calls = []

    def get_product_detail(self, product_id, country, currency):
        self.atomic_states.append(connection.in_atomic_block)
        return next(self.products)

    def generate_affiliate_link(self, source_url):
        self.atomic_states.append(connection.in_atomic_block)
        self.link_calls.append(source_url)
        return self.affiliate_url


def product(**overrides):
    values = {
        "product_id": "42",
        "title": "HIFU Device",
        "image_url": "https://images.example/hifu.jpg",
        "product_url": "https://source.example/item/42",
        "price": Decimal("99.90"),
        "currency": "EUR",
        "original_price": Decimal("120.00"),
        "evaluation_rate_percent": Decimal("96.5"),
        "sales_count": 21,
        "commission_rate": Decimal("7.5"),
        "ship_to_days_raw": "Ship to PT in 3 Days",
        "delivery_days": 3,
        "destination_country": "PT",
    }
    values.update(overrides)
    return AliExpressProduct(**values)


class AliExpressPersistenceTests(TransactionTestCase):
    def test_initial_import_creates_offer_and_factual_observation(self):
        client = FakeClient([product()])
        result = import_aliexpress_product("42", client=client)

        self.assertTrue(result.offer_created)
        self.assertEqual(Offer.objects.count(), 1)
        self.assertEqual(OfferObservation.objects.count(), 1)
        offer = Offer.objects.get()
        obs = OfferObservation.objects.get()
        self.assertEqual(offer.external_product_id, "42")
        self.assertEqual(offer.first_seen_at, offer.last_seen_at)
        self.assertTrue(offer.is_active)
        self.assertIsNone(offer.product_family)
        self.assertEqual(offer.affiliate_url, "https://affiliate.example/item")
        self.assertEqual(obs.observed_at, offer.first_seen_at)
        self.assertEqual(obs.price, Decimal("99.90"))
        self.assertEqual(obs.evaluation_rate_percent, Decimal("96.50"))
        self.assertEqual(obs.ship_to_days_raw, "Ship to PT in 3 Days")
        self.assertEqual(obs.delivery_days, 3)
        self.assertEqual(obs.availability, OfferObservation.Availability.UNKNOWN)
        self.assertEqual(client.atomic_states, [False, False])

    def test_reimport_reuses_offer_appends_history_and_preserves_first_seen(self):
        first_time = timezone.now()
        second_time = first_time + timedelta(minutes=5)
        client = FakeClient([product(), product(title="Updated HIFU")])
        clock = SimpleNamespace(now=lambda: next(times))
        times = iter([first_time, second_time])
        with patch("apps.catalog.services.aliexpress_persistence.timezone", clock):
            first = import_aliexpress_product("42", client=client)
            second = import_aliexpress_product("42", client=client)

        self.assertEqual(first.offer.pk, second.offer.pk)
        self.assertEqual(Offer.objects.count(), 1)
        self.assertEqual(OfferObservation.objects.count(), 2)
        offer = Offer.objects.get()
        self.assertEqual(offer.first_seen_at, first_time)
        self.assertEqual(offer.last_seen_at, second_time)
        self.assertEqual(offer.title, "Updated HIFU")

    def test_omitted_metadata_does_not_erase_offer_or_copy_old_observation_facts(self):
        client = FakeClient(
            [
                product(),
                product(
                    title=None,
                    image_url=None,
                    product_url=None,
                    price=None,
                    currency=None,
                    original_price=None,
                    evaluation_rate_percent=None,
                    sales_count=None,
                    commission_rate=None,
                    ship_to_days_raw=None,
                    delivery_days=None,
                    destination_country=None,
                ),
            ]
        )
        import_aliexpress_product("42", client=client)
        import_aliexpress_product("42", client=client)

        offer = Offer.objects.get()
        latest = OfferObservation.objects.order_by("-observed_at", "-pk").first()
        self.assertEqual(offer.title, "HIFU Device")
        self.assertEqual(offer.image_url, "https://images.example/hifu.jpg")
        self.assertEqual(offer.product_url, "https://source.example/item/42")
        self.assertEqual(offer.affiliate_url, "https://affiliate.example/item")
        self.assertIsNone(latest.price)
        self.assertIsNone(latest.currency)
        self.assertIsNone(latest.ship_to_days_raw)
        self.assertIsNone(latest.delivery_days)
        self.assertIsNone(latest.destination_country)

    def test_existing_product_family_is_preserved(self):
        family = ProductFamily.objects.create(name="HIFU", slug="hifu")
        Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="42",
            product_family=family,
        )
        import_aliexpress_product("42", client=FakeClient([product()]))
        self.assertEqual(Offer.objects.get().product_family, family)

    def test_product_without_source_url_does_not_invent_affiliate_link(self):
        client = FakeClient([product(product_url=None)])
        import_aliexpress_product("42", client=client)
        self.assertEqual(client.link_calls, [])
        self.assertEqual(Offer.objects.get().affiliate_url, "")

    def test_detail_failure_leaves_database_unchanged(self):
        class FailingClient:
            def get_product_detail(self, product_id, country, currency):
                raise AliExpressAPIError("detail failed")

        with self.assertRaises(AliExpressAPIError):
            import_aliexpress_product("42", client=FailingClient())
        self.assertEqual(Offer.objects.count(), 0)
        self.assertEqual(OfferObservation.objects.count(), 0)

    def test_affiliate_failure_leaves_database_unchanged(self):
        class FailingLinkClient(FakeClient):
            def generate_affiliate_link(self, source_url):
                raise AliExpressAPIError("link failed")

        with self.assertRaises(AliExpressAPIError):
            import_aliexpress_product("42", client=FailingLinkClient([product()]))
        self.assertEqual(Offer.objects.count(), 0)
        self.assertEqual(OfferObservation.objects.count(), 0)

    def test_database_error_rolls_back_offer_update(self):
        existing = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="42",
            title="Old title",
        )
        original_last_seen = existing.last_seen_at
        with patch(
            "apps.catalog.services.aliexpress_persistence.OfferObservation.objects.create",
            side_effect=IntegrityError("forced observation failure"),
        ):
            with self.assertRaises(IntegrityError):
                import_aliexpress_product("42", client=FakeClient([product(title="New title")]))
        existing.refresh_from_db()
        self.assertEqual(existing.title, "Old title")
        self.assertEqual(existing.last_seen_at, original_last_seen)
        self.assertEqual(OfferObservation.objects.count(), 0)

    def test_dry_run_validates_then_rolls_back_all_database_changes(self):
        result = import_aliexpress_product("42", client=FakeClient([product()]), dry_run=True)
        self.assertTrue(result.dry_run)
        self.assertEqual(Offer.objects.count(), 0)
        self.assertEqual(OfferObservation.objects.count(), 0)

    def test_manual_import_has_no_search_logistics(self):
        import_aliexpress_product("42", client=FakeClient([product()]))
        obs = OfferObservation.objects.get()
        self.assertIsNone(obs.search_ship_to_days_raw)
        self.assertIsNone(obs.search_delivery_days)
        self.assertEqual(obs.ship_to_days_raw, "Ship to PT in 3 Days")
        self.assertEqual(obs.delivery_days, 3)

    def test_search_five_detail_none_preserves_provenance(self):
        search = product(
            ship_to_days_raw="Ship to PT in 5 days",
            delivery_days=5,
        )
        detail = product(ship_to_days_raw=None, delivery_days=None)
        result = import_aliexpress_product("42", client=FakeClient([detail]), search_product=search)
        obs = result.observation
        self.assertEqual(obs.search_ship_to_days_raw, "Ship to PT in 5 days")
        self.assertEqual(obs.search_delivery_days, 5)
        self.assertIsNone(obs.ship_to_days_raw)
        self.assertIsNone(obs.delivery_days)

    def test_search_none_detail_five_preserves_provenance(self):
        search = product(ship_to_days_raw=None, delivery_days=None)
        detail = product(
            ship_to_days_raw="Ship to PT in 5 Days",
            delivery_days=5,
        )
        result = import_aliexpress_product("42", client=FakeClient([detail]), search_product=search)
        obs = result.observation
        self.assertIsNone(obs.search_ship_to_days_raw)
        self.assertIsNone(obs.search_delivery_days)
        self.assertEqual(obs.ship_to_days_raw, "Ship to PT in 5 Days")
        self.assertEqual(obs.delivery_days, 5)

    def test_matching_search_and_detail_are_both_preserved(self):
        search = product(ship_to_days_raw="Ship to PT in 5 Days", delivery_days=5)
        detail = product(ship_to_days_raw="Ship to PT in 5 Days", delivery_days=5)
        obs = import_aliexpress_product(
            "42", client=FakeClient([detail]), search_product=search
        ).observation
        self.assertEqual((obs.search_delivery_days, obs.delivery_days), (5, 5))

    def test_different_search_and_detail_are_both_preserved(self):
        search = product(ship_to_days_raw="Ship to PT in 5 Days", delivery_days=5)
        detail = product(ship_to_days_raw="Ship to PT in 7 Days", delivery_days=7)
        obs = import_aliexpress_product(
            "42", client=FakeClient([detail]), search_product=search
        ).observation
        self.assertEqual((obs.search_delivery_days, obs.delivery_days), (5, 7))

    def test_detail_product_id_mismatch_fails_before_affiliate_or_writes(self):
        client = FakeClient([product(product_id="84")])
        with self.assertRaisesRegex(AliExpressResponseError, "detail product_id"):
            import_aliexpress_product("42", client=client)
        self.assertEqual(client.link_calls, [])
        self.assertEqual(client.atomic_states, [False])
        self.assertEqual((Offer.objects.count(), OfferObservation.objects.count()), (0, 0))

    def test_search_product_id_mismatch_fails_before_network_or_writes(self):
        client = FakeClient([product()])
        with self.assertRaisesRegex(ValueError, "search_product product_id"):
            import_aliexpress_product(
                "42",
                client=client,
                search_product=product(product_id="84"),
            )
        self.assertEqual(client.atomic_states, [])
        self.assertEqual((Offer.objects.count(), OfferObservation.objects.count()), (0, 0))

    def test_reimport_appends_distinct_search_and_detail_logistics(self):
        first_search = product(ship_to_days_raw="Ship to PT in 5 Days", delivery_days=5)
        second_search = product(ship_to_days_raw="Ship to PT in 7 Days", delivery_days=7)
        client = FakeClient(
            [
                product(ship_to_days_raw=None, delivery_days=None),
                product(ship_to_days_raw="Ship to PT in 6 Days", delivery_days=6),
            ]
        )
        import_aliexpress_product("42", client=client, search_product=first_search)
        import_aliexpress_product("42", client=client, search_product=second_search)
        self.assertEqual(Offer.objects.count(), 1)
        self.assertEqual(OfferObservation.objects.count(), 2)
        observations = list(OfferObservation.objects.order_by("observed_at", "pk"))
        self.assertEqual(
            [(o.search_delivery_days, o.delivery_days) for o in observations],
            [(5, None), (7, 6)],
        )

    def test_product_family_preserved_with_search_evidence(self):
        family = ProductFamily.objects.create(name="HIFU provenance", slug="hifu-provenance")
        Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="42",
            product_family=family,
        )
        import_aliexpress_product(
            "42",
            client=FakeClient([product(delivery_days=None, ship_to_days_raw=None)]),
            search_product=product(delivery_days=5, ship_to_days_raw="Ship to PT in 5 Days"),
        )
        self.assertEqual(Offer.objects.get().product_family, family)

    def test_dry_run_rolls_back_search_logistics_too(self):
        result = import_aliexpress_product(
            "42",
            client=FakeClient([product(delivery_days=None, ship_to_days_raw=None)]),
            search_product=product(delivery_days=5, ship_to_days_raw="Ship to PT in 5 Days"),
            dry_run=True,
        )
        self.assertEqual(result.observation.search_delivery_days, 5)
        self.assertIsNone(result.observation.delivery_days)
        self.assertEqual((Offer.objects.count(), OfferObservation.objects.count()), (0, 0))

from contextlib import nullcontext
from datetime import timedelta
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import (
    Offer,
    OfferCandidate,
    OfferClick,
    OfferFamilyPlacement,
    OfferObservation,
    ProductFamily,
)
from apps.catalog.services.cavitation_availability import (
    monitor_cavitation_availability,
    select_manual_cavitation_batch,
)
from apps.catalog.services.offer_maintenance import select_maintenance_batch
from apps.integrations.aliexpress.exceptions import (
    AliExpressAPIError,
    AliExpressTransportError,
)
from apps.integrations.aliexpress.types import AliExpressProduct


@override_settings(PUBLIC_RECENT_PRICE_REQUIRED=True)
class CavitationManualOnlyTests(TestCase):
    def setUp(self):
        self.family = ProductFamily.objects.create(
            name="Cavitação + RF + Vacuum",
            slug="cavitacao-rf-vacuum-corpo",
            display_order=1,
        )
        self.other = ProductFamily.objects.create(
            name="HIFU", slug="hifu", display_order=4
        )
        self.staff = get_user_model().objects.create_user(
            username="cavitation-owner", password="secret", is_staff=True
        )
        self.manual = self.make_offer("1005012193878441", self.family)
        OfferObservation.objects.create(
            offer=self.manual, destination_country="PT",
            price="139.90", currency="EUR",
        )
        self.legacy = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="legacy-cav",
            title="Legacy should not be published or auto-refreshed",
            product_family=self.family,
        )
        self.pending = OfferCandidate.objects.create(
            product_family=self.family,
            source=Offer.Source.ALIEXPRESS,
            external_product_id="legacy-pending",
        )

    @staticmethod
    def make_offer(product_id, family):
        offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS_OWNER,
            external_product_id=product_id,
            title="Owner product " + product_id,
            affiliate_url="https://s.click.aliexpress.com/e/_" + product_id,
            product_url="https://www.aliexpress.com/item/" + product_id + ".html",
            image_url="https://ae01.alicdn.com/kf/test-product.jpg",
            protocol_verified_at=timezone.now(),
        )
        OfferFamilyPlacement.objects.create(
            offer=offer, product_family=family,
        )
        return offer

    def test_owner_historical_eur_price_survives_24h_and_null_availability(self):
        previous = timezone.now() - timedelta(days=2)
        OfferObservation.objects.filter(
            offer=self.manual, price__isnull=False
        ).update(observed_at=previous)
        # This is what the availability-only timer writes: no price.
        OfferObservation.objects.create(
            offer=self.manual, destination_country="PT",
            observed_at=timezone.now(),
            availability=OfferObservation.Availability.UNKNOWN,
        )
        count_before = OfferObservation.objects.filter(offer=self.manual).count()
        original_url = self.manual.affiliate_url

        for url in (
            reverse("storefront:home"),
            reverse("storefront:product-family-detail", args=[self.family.slug]),
        ):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertContains(response, "139,90 EUR")
                if url == reverse("storefront:home"):
                    self.assertContains(response, "Observado em")
                else:
                    self.assertNotContains(response, "Observado em")
        detail = self.client.get(
            reverse("storefront:product-family-detail", args=[self.family.slug])
        )
        self.assertIn('data-price="139.90" data-currency="EUR"', detail.content.decode())
        self.assertEqual(OfferObservation.objects.filter(offer=self.manual).count(), count_before)
        self.manual.refresh_from_db()
        self.assertEqual(self.manual.affiliate_url, original_url)
        self.assertEqual(
            self.client.head(reverse("storefront:offer-go", args=[self.manual.pk])).status_code,
            302,
        )

    def test_owner_eur_price_older_than_seven_days_shows_explicit_warning(self):
        OfferObservation.objects.filter(
            offer=self.manual, price__isnull=False
        ).update(observed_at=timezone.now() - timedelta(days=12))
        detail = self.client.get(
            reverse("storefront:product-family-detail", args=[self.family.slug])
        )
        self.assertContains(detail, "139,90 EUR")
        self.assertContains(detail, "Observação com mais de 7 dias.")
        self.assertContains(detail, "Confirme o preço atual no parceiro.")

    def test_owner_without_genuine_pt_eur_price_stays_unavailable(self):
        OfferObservation.objects.filter(offer=self.manual).delete()
        now = timezone.now()
        for price, currency, age in (
            ("0.00", "EUR", 3),
            ("999.00", "USD", 2),
            ("500.00", "EUR", -1),
        ):
            OfferObservation.objects.create(
                offer=self.manual, price=price, currency=currency,
                destination_country="PT",
                observed_at=now - timedelta(hours=age),
            )
        OfferObservation.objects.create(
            offer=self.manual, price="300.00", currency="EUR",
            destination_country="ES", observed_at=now - timedelta(hours=1),
        )
        detail = self.client.get(
            reverse("storefront:product-family-detail", args=[self.family.slug])
        )
        self.assertContains(detail, "Preço observado")
        self.assertContains(detail, "Não disponível")
        self.assertNotContains(detail, "999,00 USD")
        self.assertNotContains(detail, "500,00 EUR")
        self.assertNotContains(detail, "300,00 EUR")
        self.assertNotContains(detail, "0,00 EUR")

    def test_private_panel_shows_only_montra_and_delete(self):
        self.client.force_login(self.staff)
        url = reverse("owner-panel:family", args=[self.family.slug])
        for suffix in ("", "?vista=rever", "?vista=aprovados"):
            response = self.client.get(url + suffix)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "MONTRA")
            self.assertContains(response, "ELIMINAR DA MONTRA")
            self.assertContains(response, "CONFIRMAR ELIMINAÇÃO")
            self.assertNotContains(response, "A REVER")
            self.assertNotContains(response, "APROVAR")
            self.assertNotContains(response, "REVALIDAR")
            self.assertNotContains(response, "GERAR LINK")

    def test_private_public_category_only_has_manual_delete_action(self):
        self.client.force_login(self.staff)
        response = self.client.get(
            reverse("storefront:product-family-detail", args=[self.family.slug])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ELIMINAR DA MONTRA")
        self.assertNotContains(response, "A rever <span>")
        self.assertNotContains(response, "MUDAR FAMÍLIA")
        self.assertNotContains(response, "APROVAR")
        self.assertNotContains(response, "RETIRAR DA MONTRA")

    def test_owner_can_remove_exactly_one_offer_without_changing_link(self):
        second = self.make_offer("1005002200220022", self.family)
        other = self.make_offer("1005003300330033", self.other)
        self.client.force_login(self.staff)
        original = self.manual.affiliate_url
        response = self.client.post(
            reverse("owner-panel:offer-hide", args=[self.family.slug, self.manual.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.manual.refresh_from_db()
        second.refresh_from_db()
        other.refresh_from_db()
        self.assertTrue(self.manual.owner_hidden)
        self.assertEqual(self.manual.affiliate_url, original)
        self.assertFalse(second.owner_hidden)
        self.assertFalse(other.owner_hidden)
        self.assertEqual(
            self.client.head(reverse("storefront:offer-go", args=[self.manual.pk])).status_code,
            404,
        )
        self.assertEqual(OfferClick.objects.filter(offer=self.manual).count(), 0)
        response = self.client.get(reverse("owner-panel:family", args=[self.family.slug]))
        self.assertNotContains(response, self.manual.title)
        self.assertContains(response, second.title)

    def test_manual_action_requires_csrf_and_owner(self):
        url = reverse("owner-panel:offer-hide", args=[self.family.slug, self.manual.pk])
        self.assertEqual(self.client.post(url).status_code, 302)
        strict = Client(enforce_csrf_checks=True)
        strict.force_login(self.staff)
        self.assertEqual(strict.post(url).status_code, 403)
        self.manual.refresh_from_db()
        self.assertFalse(self.manual.owner_hidden)

    def test_legacy_actions_are_forbidden_for_cavitation(self):
        self.client.force_login(self.staff)
        endpoints = (
            ("manual-candidate-intake", [self.family.slug]),
            ("candidate-approve", [self.family.slug, self.pending.pk]),
            ("candidate-reject", [self.family.slug, self.pending.pk]),
            ("candidate-revalidate", [self.family.slug, self.pending.pk]),
            ("candidate-move", [self.family.slug, self.pending.pk]),
            ("offer-publish", [self.family.slug, self.manual.pk]),
        )
        for name, args in endpoints:
            with self.subTest(name=name):
                self.assertEqual(
                    self.client.post(reverse("owner-panel:" + name, args=args)).status_code,
                    403,
                )

    @patch("apps.catalog.services.cavitation_availability.maintenance_run_lock")
    def test_monitor_two_confirmations_then_removes_without_touching_url(self, lock):
        lock.return_value = nullcontext()
        client = Mock()
        client.get_product_detail.return_value = AliExpressProduct(
            product_id=self.manual.external_product_id,
            availability_raw="out of stock",
        )
        start = timezone.now()
        original = self.manual.affiliate_url

        result = monitor_cavitation_availability(client=client, now=start)
        self.assertEqual(result.awaiting_confirmation, 1)
        self.manual.refresh_from_db()
        self.assertFalse(self.manual.owner_hidden)

        result = monitor_cavitation_availability(
            client=client, now=start + timedelta(hours=4)
        )
        self.assertEqual(result.removed_from_storefront, 1)
        self.manual.refresh_from_db()
        self.assertTrue(self.manual.owner_hidden)
        self.assertFalse(self.manual.is_active)
        self.assertEqual(self.manual.affiliate_url, original)
        self.assertEqual(
            self.client.head(reverse("storefront:offer-go", args=[self.manual.pk])).status_code,
            404,
        )
        self.assertEqual(monitor_cavitation_availability(client=client).selected, 0)
        self.assertEqual(client.generate_affiliate_link.call_count, 0)

    @patch("apps.catalog.services.cavitation_availability.maintenance_run_lock")
    def test_unknown_or_transient_error_never_eliminates_and_breaks_streak(self, lock):
        lock.return_value = nullcontext()
        client = Mock()
        client.get_product_detail.side_effect = [
            AliExpressProduct(product_id=self.manual.external_product_id,
                              availability_raw="offline"),
            AliExpressTransportError("network outage"),
            AliExpressProduct(product_id=self.manual.external_product_id,
                              availability_raw="offline"),
        ]
        start = timezone.now()
        first = monitor_cavitation_availability(client=client, now=start)
        middle = monitor_cavitation_availability(
            client=client, now=start + timedelta(hours=4)
        )
        last = monitor_cavitation_availability(
            client=client, now=start + timedelta(hours=8)
        )
        self.assertEqual(first.awaiting_confirmation, 1)
        self.assertEqual(middle.unknown, 1)
        self.assertEqual(last.awaiting_confirmation, 1)
        self.manual.refresh_from_db()
        self.assertTrue(self.manual.is_active)
        self.assertFalse(self.manual.owner_hidden)

    @patch("apps.catalog.services.cavitation_availability.maintenance_run_lock")
    def test_definitively_missing_product_is_hidden_on_first_check(self, lock):
        lock.return_value = nullcontext()
        client = Mock()
        client.get_product_detail.side_effect = AliExpressAPIError(
            "AliExpress product does not exist"
        )
        original_url = self.manual.affiliate_url
        first = monitor_cavitation_availability(client=client, now=timezone.now())
        self.assertEqual(first.removed_from_storefront, 1)
        self.assertEqual(first.awaiting_confirmation, 0)
        self.manual.refresh_from_db()
        self.assertFalse(self.manual.is_active)
        self.assertTrue(self.manual.owner_hidden)
        self.assertEqual(self.manual.affiliate_url, original_url)
        self.assertEqual(monitor_cavitation_availability(client=client).selected, 0)
        self.assertEqual(client.generate_affiliate_link.call_count, 0)

    @patch("apps.catalog.services.cavitation_availability.maintenance_run_lock")
    def test_definitive_removed_detail_is_hidden_on_first_check(self, lock):
        lock.return_value = nullcontext()
        client = Mock()
        client.get_product_detail.return_value = AliExpressProduct(
            product_id=self.manual.external_product_id,
            availability_raw="deleted",
        )
        result = monitor_cavitation_availability(client=client, now=timezone.now())
        self.assertEqual(result.removed_from_storefront, 1)
        self.manual.refresh_from_db()
        self.assertTrue(self.manual.owner_hidden)
        self.assertEqual(client.generate_affiliate_link.call_count, 0)

    @patch("apps.catalog.services.cavitation_availability.maintenance_run_lock")
    def test_stockout_requires_two_signals_at_least_twenty_minutes_apart(self, lock):
        lock.return_value = nullcontext()
        client = Mock()
        client.get_product_detail.return_value = AliExpressProduct(
            product_id=self.manual.external_product_id,
            availability_raw="sold out",
        )
        start = timezone.now()
        first = monitor_cavitation_availability(client=client, now=start)
        too_soon = monitor_cavitation_availability(
            client=client, now=start + timedelta(minutes=10)
        )
        self.assertEqual(first.awaiting_confirmation, 1)
        self.assertEqual(too_soon.awaiting_confirmation, 1)
        self.manual.refresh_from_db()
        self.assertFalse(self.manual.owner_hidden)
        confirmed = monitor_cavitation_availability(
            client=client, now=start + timedelta(minutes=35)
        )
        self.assertEqual(confirmed.removed_from_storefront, 1)
        self.manual.refresh_from_db()
        self.assertTrue(self.manual.owner_hidden)
        self.assertEqual(client.generate_affiliate_link.call_count, 0)

    @patch("apps.catalog.services.cavitation_availability.maintenance_run_lock")
    def test_ambiguous_unavailable_api_error_still_requires_confirmation(self, lock):
        lock.return_value = nullcontext()
        client = Mock()
        client.get_product_detail.side_effect = AliExpressAPIError(
            "Product unavailable"
        )
        start = timezone.now()
        first = monitor_cavitation_availability(client=client, now=start)
        self.assertEqual(first.awaiting_confirmation, 1)
        self.manual.refresh_from_db()
        self.assertFalse(self.manual.owner_hidden)
        second = monitor_cavitation_availability(
            client=client, now=start + timedelta(minutes=30)
        )
        self.assertEqual(second.removed_from_storefront, 1)
        self.assertEqual(client.generate_affiliate_link.call_count, 0)

    def test_manual_cavitation_and_hifu_are_monitored_but_legacy_is_not(self):
        other_manual = self.make_offer("1005008800880088", self.other)
        selected = select_manual_cavitation_batch()
        self.assertEqual({x.pk for x in selected}, {self.manual.pk, other_manual.pk})
        selected_old = select_maintenance_batch(20)
        self.assertNotIn(self.manual.pk, [x.pk for x in selected_old])
        self.assertNotIn(self.legacy.pk, [x.pk for x in selected_old])
        self.assertNotIn(self.legacy.pk, [x.pk for x in selected])

"""The manually curated second category mirrors the approved Cavitation UI."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import (
    Offer,
    OfferCandidate,
    OfferFamilyPlacement,
    OfferObservation,
    ProductFamily,
)


class MicrodermoManualOnlyTests(TestCase):
    def setUp(self):
        self.family = ProductFamily.objects.create(
            name="Microdermoabrasão / Hidrodermoabrasão / Multifunções faciais",
            slug="hydrodermoabrasao-aqua-facial-multifuncoes",
            display_order=2,
            status=ProductFamily.Status.NEW,
        )
        self.owner = get_user_model().objects.create_user(
            username="micro-owner", password="test", is_staff=True,
        )
        self.offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS_OWNER,
            external_product_id="1005003003003000",
            title="Facial microdermabrasion equipment",
            affiliate_url="https://s.click.aliexpress.com/e/_MicroFixtureOwner",
            product_url="https://www.aliexpress.com/item/1005003003003000.html",
            protocol_verified_at=timezone.now(),
        )
        OfferFamilyPlacement.objects.create(offer=self.offer, product_family=self.family)
        OfferObservation.objects.create(
            offer=self.offer, destination_country="PT", price="219.90",
            currency="EUR",
        )
        self.legacy = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="micro-old-candidate",
            title="Old candidate",
        )
        OfferFamilyPlacement.objects.create(
            offer=self.legacy, product_family=self.family,
        )
        self.candidate = OfferCandidate.objects.create(
            product_family=self.family,
            source=Offer.Source.ALIEXPRESS,
            external_product_id="micro-pending",
        )

    def test_public_card_has_cavitation_layout_and_hidden_affiliate_link(self):
        url = reverse("storefront:product-family-detail", args=[self.family.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Enviado da Europa")
        self.assertContains(response, "Preço observado")
        self.assertContains(response, "219,90 EUR")
        self.assertContains(response, "+ Comparar equipamento")
        self.assertContains(response, "VER PREÇO NO ALIEXPRESS")
        self.assertContains(response, "PARTILHAR ESTE PRODUTO")
        self.assertContains(
            response,
            'data-affiliate-original-url="https://s.click.aliexpress.com/e/_MicroFixtureOwner"',
        )
        self.assertNotContains(response, "Produto a partilhar")
        self.assertNotContains(response, "Logística observada")
        self.assertNotContains(response, "Consultar avaliações e vendas indicadas")
        self.assertNotContains(response, "Não abriu no navegador?")
        self.assertNotContains(response, "Compra externa.")
        self.assertNotContains(response, "data-affiliate-copy")
        self.assertEqual(
            self.client.head(
                reverse("storefront:offer-go", args=[self.offer.pk])
            ).status_code,
            302,
        )

    def test_owner_sees_only_montra_and_delete_controls(self):
        self.client.force_login(self.owner)
        url = reverse("owner-panel:family", args=[self.family.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Montra manual.")
        self.assertContains(response, "ELIMINAR DA MONTRA")
        self.assertNotContains(response, "A REVER")
        self.assertNotContains(response, "APROVAR")
        detail = self.client.get(
            reverse("storefront:product-family-detail", args=[self.family.slug])
        )
        self.assertContains(detail, "Gestão manual")
        self.assertContains(detail, "ELIMINAR DA MONTRA")
        self.assertNotContains(detail, "MUDAR FAMÍLIA")
        self.assertNotContains(detail, "A rever <span>")

    def test_legacy_review_actions_are_blocked(self):
        self.client.force_login(self.owner)
        routes = (
            ("manual-candidate-intake", [self.family.slug]),
            ("candidate-approve", [self.family.slug, self.candidate.pk]),
            ("candidate-reject", [self.family.slug, self.candidate.pk]),
            ("candidate-revalidate", [self.family.slug, self.candidate.pk]),
            ("offer-publish", [self.family.slug, self.offer.pk]),
        )
        for route, args in routes:
            with self.subTest(route=route):
                response = self.client.post(
                    reverse("owner-panel:" + route, args=args)
                )
                self.assertEqual(response.status_code, 403)

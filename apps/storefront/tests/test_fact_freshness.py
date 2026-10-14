from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import Offer, OfferFamilyPlacement, OfferObservation, ProductFamily


class PublicObservationAgeNoticeTests(TestCase):
    def setUp(self):
        self.family = ProductFamily.objects.create(name="Avisos de preço", slug="avisos-de-preco")
        now = timezone.now()
        self.offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="age-notice-001",
            title="Equipamento de avaliação",
            affiliate_url="https://affiliate.example.test/age-notice",
            affiliate_promotion_status=Offer.AffiliatePromotionStatus.ELIGIBLE,
            affiliate_promotion_verified_at=now,
            protocol_verified_at=now - timedelta(days=90),
            is_active=True,
            owner_hidden=False,
        )
        OfferFamilyPlacement.objects.create(offer=self.offer, product_family=self.family)
        self.detail_url = reverse(
            "storefront:product-family-detail", kwargs={"slug": self.family.slug}
        )

    def test_old_facts_warn_but_original_offer_eligibility_is_preserved(self):
        OfferObservation.objects.create(
            offer=self.offer,
            observed_at=timezone.now() - timedelta(days=12),
            price=Decimal("175.50"),
            currency="EUR",
            search_delivery_days=5,
        )
        # Later incomplete observations must not invent or erase the last known price.
        OfferObservation.objects.create(offer=self.offer, observed_at=timezone.now())
        detail = self.client.get(self.detail_url)
        self.assertContains(detail, "175,50 EUR")
        self.assertContains(detail, "Confirme o preço atual no parceiro.")
        self.assertContains(detail, "Confirme o prazo no parceiro.")
        home = self.client.get(reverse("storefront:home"))
        self.assertContains(home, "Preço histórico; confirme no parceiro.")
        self.assertContains(home, "Prazo histórico; confirme no parceiro.")
        # A display-only 7-day warning must not introduce a protocol expiry.
        self.assertEqual(
            self.client.get(reverse("storefront:offer-go", args=[self.offer.pk])).status_code,
            302,
        )

    def test_recent_facts_show_observation_date_without_warning(self):
        OfferObservation.objects.create(
            offer=self.offer,
            observed_at=timezone.now() - timedelta(days=1),
            price=Decimal("100.00"),
            currency="EUR",
            delivery_days=4,
        )
        detail = self.client.get(self.detail_url)
        self.assertContains(detail, "Observado em")
        self.assertNotContains(detail, "Confirme o preço atual no parceiro.")
        self.assertNotContains(detail, "Confirme o prazo no parceiro.")

    def test_unknown_facts_do_not_invent_dates_or_age_warnings(self):
        detail = self.client.get(self.detail_url)
        self.assertContains(detail, "Não disponível")
        self.assertContains(detail, "Prazo não confirmado")
        self.assertNotContains(detail, "Observação com mais de 7 dias.")

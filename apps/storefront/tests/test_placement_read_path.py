from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import Offer, OfferFamilyPlacement, ProductFamily


class StorefrontPlacementReadPathTests(TestCase):
    def make_offer(self, external_id, **kwargs):
        return Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id=external_id,
            ship_from_country="PL",
            protocol_verified_at=timezone.now(),
            **kwargs,
        )

    def test_legacy_fk_alone_does_not_publish_offer(self):
        family_a = ProductFamily.objects.create(name="Legacy A", slug="legacy-a", display_order=1)
        family_b = ProductFamily.objects.create(name="Placed B", slug="placed-b", display_order=2)
        offer = self.make_offer(
            "legacy-independent", product_family=family_a, title="Placed only in B"
        )
        OfferFamilyPlacement.objects.create(offer=offer, product_family=family_b)

        detail_a = self.client.get(
            reverse("storefront:product-family-detail", kwargs={"slug": family_a.slug})
        )
        detail_b = self.client.get(
            reverse("storefront:product-family-detail", kwargs={"slug": family_b.slug})
        )

        self.assertNotContains(detail_a, offer.title)
        self.assertContains(detail_b, offer.title)

    def test_same_offer_can_publish_in_two_families_without_duplication(self):
        family_a = ProductFamily.objects.create(name="Family A", slug="family-a", display_order=1)
        family_b = ProductFamily.objects.create(name="Family B", slug="family-b", display_order=2)
        offer = self.make_offer("multi-family", title="Shared Offer")
        OfferFamilyPlacement.objects.create(offer=offer, product_family=family_a)
        OfferFamilyPlacement.objects.create(offer=offer, product_family=family_b)

        self.assertContains(
            self.client.get(
                reverse("storefront:product-family-detail", kwargs={"slug": family_a.slug})
            ),
            offer.title,
        )
        self.assertContains(
            self.client.get(
                reverse("storefront:product-family-detail", kwargs={"slug": family_b.slug})
            ),
            offer.title,
        )
        self.assertEqual(Offer.objects.filter(external_product_id="multi-family").count(), 1)

    def test_selection_and_other_groups_follow_placement_order(self):
        family = ProductFamily.objects.create(name="Grouped", slug="grouped", display_order=1)
        selection_two = self.make_offer("selection-two", title="Selection Two")
        selection_one = self.make_offer("selection-one", title="Selection One")
        normal_two = self.make_offer("normal-two", title="Normal Two")
        normal_one = self.make_offer("normal-one", title="Normal One")
        OfferFamilyPlacement.objects.create(
            offer=selection_two, product_family=family, selection_position=2
        )
        OfferFamilyPlacement.objects.create(
            offer=selection_one, product_family=family, selection_position=1
        )
        OfferFamilyPlacement.objects.create(
            offer=normal_two, product_family=family, display_order=20
        )
        OfferFamilyPlacement.objects.create(
            offer=normal_one, product_family=family, display_order=10
        )
        response = self.client.get(
            reverse("storefront:product-family-detail", kwargs={"slug": family.slug})
        )
        content = response.content.decode()
        self.assertIn("Seleções Lowcost Europa", content)
        self.assertIn("Outras ofertas selecionadas", content)
        self.assertLess(content.index("Selection One"), content.index("Selection Two"))
        self.assertLess(content.index("Normal One"), content.index("Normal Two"))
        self.assertNotIn("Top 5", content)
        self.assertNotIn("melhores", content.lower())
        self.assertIn("não representa um ranking objetivo", content.lower())

    def test_homepage_uses_first_selection_as_representative_offer(self):
        family = ProductFamily.objects.create(
            name="Representative", slug="representative", display_order=1
        )
        normal = self.make_offer(
            "normal", title="Normal Offer", image_url="https://images.example/normal.jpg"
        )
        selected = self.make_offer(
            "selected", title="Selected Offer", image_url="https://images.example/selected.jpg"
        )
        OfferFamilyPlacement.objects.create(offer=normal, product_family=family, display_order=1)
        OfferFamilyPlacement.objects.create(
            offer=selected, product_family=family, selection_position=2, display_order=99
        )
        response = self.client.get(reverse("storefront:home"))
        self.assertContains(response, selected.image_url)
        self.assertNotContains(response, normal.image_url)

    def test_retired_family_is_hidden_and_has_no_public_offers(self):
        family = ProductFamily.objects.create(
            name="Retired",
            slug="retired-placement",
            status=ProductFamily.Status.RETIRED,
            display_order=99,
        )
        offer = self.make_offer("retired-offer", title="Hidden Retired Offer")
        OfferFamilyPlacement.objects.create(
            offer=offer, product_family=family, selection_position=1
        )
        self.assertNotContains(self.client.get(reverse("storefront:home")), family.name)
        detail = self.client.get(
            reverse("storefront:product-family-detail", kwargs={"slug": family.slug})
        )
        self.assertEqual(detail.status_code, 200)
        self.assertNotContains(detail, offer.title)
        self.assertContains(detail, "Seleção em preparação")

    def test_homepage_lists_eight_active_families_in_display_order(self):
        for order in range(8, 0, -1):
            ProductFamily.objects.create(
                name=f"Family {order}", slug=f"family-{order}", display_order=order
            )
        ProductFamily.objects.create(
            name="Retired Family",
            slug="retired-family-order",
            status=ProductFamily.Status.RETIRED,
            display_order=99,
        )
        response = self.client.get(reverse("storefront:home"))
        content = response.content.decode()
        positions = [content.index(f"Family {order}") for order in range(1, 9)]
        self.assertEqual(positions, sorted(positions))
        self.assertNotContains(response, "Retired Family")

    def test_empty_family_renders_200_with_empty_state(self):
        for slug in (
            "radiofrequencia-facial",
            "pressoterapia-vacuum-drenagem",
            "microcorrente-ultrassons",
            "remocao-tatuagens-pigmentacao",
        ):
            family = ProductFamily.objects.create(name=slug, slug=slug)
            response = self.client.get(
                reverse("storefront:product-family-detail", kwargs={"slug": family.slug})
            )
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "Seleção em preparação")

    def test_hifu_real_grouping_uses_placements_only(self):
        hifu = ProductFamily.objects.create(name="HIFU", slug="hifu", display_order=6)
        offer_51 = self.make_offer("1005012522304882", title="Offer 51")
        offer_52 = self.make_offer("1005013116584854", title="Offer 52")
        offer_53 = self.make_offer("1005013002556821", title="Offer 53")
        OfferFamilyPlacement.objects.create(
            offer=offer_51, product_family=hifu, selection_position=1
        )
        OfferFamilyPlacement.objects.create(offer=offer_52, product_family=hifu, display_order=0)
        OfferFamilyPlacement.objects.create(
            offer=offer_53, product_family=hifu, selection_position=2
        )

        response = self.client.get(
            reverse("storefront:product-family-detail", kwargs={"slug": hifu.slug})
        )
        content = response.content.decode()
        selections_start = content.index("Seleções Lowcost Europa")
        others_start = content.index("Outras ofertas selecionadas")
        self.assertLess(selections_start, content.index("Offer 51"))
        self.assertLess(content.index("Offer 51"), content.index("Offer 53"))
        self.assertLess(content.index("Offer 53"), others_start)
        self.assertLess(others_start, content.index("Offer 52"))


class StorefrontVisualCommercialTests(TestCase):
    def make_placed_offer(self, family, external_id, **kwargs):
        offer = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id=external_id,
            product_family=family,
            ship_from_country="PL",
            protocol_verified_at=timezone.now(),
            **kwargs,
        )
        placement = OfferFamilyPlacement.objects.create(offer=offer, product_family=family)
        return offer, placement

    def test_selection_reason_is_conditional(self):
        family = ProductFamily.objects.create(name="Reason", slug="reason", display_order=1)
        offer, placement = self.make_placed_offer(family, "reason-offer", title="Reason Offer")
        detail_url = reverse("storefront:product-family-detail", kwargs={"slug": family.slug})
        self.assertNotContains(self.client.get(detail_url), "Porque está aqui")
        placement.selection_reason = "Incluída para comparação editorial factual."
        placement.save(update_fields=["selection_reason"])
        response = self.client.get(detail_url)
        self.assertContains(response, "Porque está aqui")
        self.assertContains(response, placement.selection_reason)

    def test_equipment_badge_only_appears_for_factual_types(self):
        family = ProductFamily.objects.create(name="Types", slug="types", display_order=1)
        unknown, _ = self.make_placed_offer(family, "unknown", title="Unknown Type")
        dedicated, _ = self.make_placed_offer(
            family,
            "dedicated",
            title="Dedicated Type",
            equipment_type=Offer.EquipmentType.DEDICATED,
        )
        combo, _ = self.make_placed_offer(
            family, "combo", title="Combo Type", equipment_type=Offer.EquipmentType.COMBO
        )
        response = self.client.get(
            reverse("storefront:product-family-detail", kwargs={"slug": family.slug})
        )
        self.assertContains(response, "Equipamento dedicado")
        self.assertContains(response, "Combo multifunções")
        self.assertNotContains(response, 'class="equipment-badge">Unknown')
        self.assertEqual(unknown.equipment_type, Offer.EquipmentType.UNKNOWN)
        self.assertEqual(dedicated.equipment_type, Offer.EquipmentType.DEDICATED)
        self.assertEqual(combo.equipment_type, Offer.EquipmentType.COMBO)

    def test_unproven_europe_claims_are_absent(self):
        family = ProductFamily.objects.create(name="Claims", slug="claims", display_order=1)
        self.make_placed_offer(family, "claims-offer", title="Claims Offer")
        responses = [
            self.client.get(reverse("storefront:home")),
            self.client.get(
                reverse("storefront:product-family-detail", kwargs={"slug": family.slug})
            ),
        ]
        forbidden = (
            "Armazém europeu",
            "Stock europeu",
            "Enviado da Europa",
            "Envio desde Portugal",
            "Sem alfândega",
            "Compra mais barato. Recebe a partir da Europa.",
        )
        for response in responses:
            content = response.content.decode()
            for phrase in forbidden:
                self.assertNotIn(phrase, content)

    def test_offer_cta_is_internal_and_transparent(self):
        family = ProductFamily.objects.create(name="Partner", slug="partner", display_order=1)
        offer, _ = self.make_placed_offer(
            family,
            "partner-offer",
            title="Partner Offer",
            affiliate_url="https://affiliate.example/private",
        )
        response = self.client.get(
            reverse("storefront:product-family-detail", kwargs={"slug": family.slug})
        )
        self.assertContains(response, "Ver oferta no parceiro")
        self.assertContains(response, "Compra externa")
        self.assertContains(response, reverse("storefront:offer-go", args=[offer.pk]))
        self.assertNotContains(response, offer.affiliate_url)

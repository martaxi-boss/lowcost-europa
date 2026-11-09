from datetime import timedelta
from decimal import Decimal
from io import StringIO
from unittest.mock import Mock, patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import (
    Offer,
    OfferClick,
    OfferFamilyPlacement,
    OfferObservation,
    ProductFamily,
)
from apps.catalog.services.offer_maintenance import select_maintenance_batch
from apps.catalog.services.public_eligibility import public_eligibility_q


@override_settings(PUBLIC_RECENT_PRICE_REQUIRED=True)
class OwnerAffiliateDirectPublishTests(TestCase):
    LINK = "https://s.click.aliexpress.com/e/_OwnerTestOnly"
    ID = "1005009204862057"
    CANONICAL = "https://www.aliexpress.com/item/1005009204862057.html"

    def setUp(self):
        self.family = ProductFamily.objects.create(
            name="Microdermoabrasão / Hidrodermoabrasão / Multifunções faciais",
            slug="hydrodermoabrasao-aqua-facial-multifuncoes",
            display_order=2,
        )
        self.other = ProductFamily.objects.create(
            name="Cavitação + RF + Vacuum",
            slug="cavitacao-rf-vacuum-corpo",
            display_order=1,
        )
        self.old = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="older-catalog-001",
            title="Produto anterior",
            affiliate_url="https://s.click.aliexpress.com/e/_OldExample",
            affiliate_promotion_status=Offer.AffiliatePromotionStatus.ELIGIBLE,
            affiliate_promotion_verified_at=timezone.now(),
            protocol_verified_at=timezone.now(),
        )
        OfferFamilyPlacement.objects.create(offer=self.old, product_family=self.family)
        OfferFamilyPlacement.objects.create(offer=self.old, product_family=self.other)
        OfferObservation.objects.create(
            offer=self.old,
            observed_at=timezone.now(),
            destination_country="PT",
            price=Decimal("100.00"),
            currency="EUR",
        )
        self.hidden = Offer.objects.create(
            source=Offer.Source.ALIEXPRESS,
            external_product_id="older-catalog-002",
            title="Anterior oculto",
            owner_hidden=True,
        )
        OfferFamilyPlacement.objects.create(offer=self.hidden, product_family=self.family)

    @staticmethod
    def detail():
        return Mock(
            product_id=OwnerAffiliateDirectPublishTests.ID,
            title="10 in 1 Hydrogen Oxygen Hydro Dermabrasion",
            price=Decimal("285.03"),
            original_price=None,
            currency="EUR",
            image_url="https://ae01.alicdn.com/kf/example.jpg",
            evaluation_rate_percent=None,
            sales_count=None,
            commission_rate=None,
            ship_to_days_raw=None,
            delivery_days=None,
        )

    def publish(self, **extra):
        with patch(
            "apps.catalog.management.commands.publish_owner_affiliate_link.resolve_aliexpress_product_url",
            return_value=(self.ID, self.CANONICAL),
        ) as resolve, patch(
            "apps.catalog.management.commands.publish_owner_affiliate_link.AliExpressClient"
        ) as client:
            client.return_value.get_product_detail.return_value = self.detail()
            buf = StringIO()
            call_command(
                "publish_owner_affiliate_link",
                self.LINK,
                family=self.family.slug,
                stdout=buf,
                **extra,
            )
            resolve.assert_called_once_with(self.LINK)
            client.return_value.get_product_detail.assert_called_once_with(self.ID, "PT", "EUR")
            self.assertNotIn("generate_affiliate_link", str(client.mock_calls))
            return buf.getvalue()

    def test_exact_link_and_atomic_category_replacement(self):
        out = self.publish(replace_family=True)
        self.assertIn("old_placements_removed=2", out)
        rows = list(OfferFamilyPlacement.objects.filter(product_family=self.family))
        self.assertEqual(len(rows), 1)
        offer = rows[0].offer
        self.assertEqual(offer.source, Offer.Source.ALIEXPRESS_OWNER)
        self.assertEqual(offer.affiliate_url, self.LINK)
        self.assertEqual(offer.external_product_id, self.ID)
        self.assertEqual(offer.affiliate_promotion_status, Offer.AffiliatePromotionStatus.UNKNOWN)
        self.assertIsNone(offer.affiliate_promotion_verified_at)
        self.assertTrue(Offer.objects.filter(pk=self.old.pk).exists())
        self.assertTrue(OfferFamilyPlacement.objects.filter(
            product_family=self.other, offer=self.old
        ).exists())
        self.assertEqual(
            list(OfferFamilyPlacement.objects.filter(
                product_family=self.family
            ).filter(public_eligibility_q(prefix="offer__")).values_list("offer_id", flat=True)),
            [offer.pk],
        )

        response = self.client.head(reverse("storefront:offer-go", args=[offer.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], self.LINK)
        self.assertEqual(OfferClick.objects.filter(offer=offer).count(), 0)

    def test_manual_offer_is_excluded_from_automatic_maintenance_even_after_price_ages(self):
        self.publish(replace_family=True)
        offer = Offer.objects.get(source=Offer.Source.ALIEXPRESS_OWNER)
        OfferObservation.objects.filter(offer=offer).update(
            observed_at=timezone.now() - timedelta(days=4)
        )
        self.assertTrue(
            Offer.objects.filter(pk=offer.pk).filter(public_eligibility_q()).exists()
        )
        selected = select_maintenance_batch(20)
        self.assertNotIn(offer.pk, [item.pk for item in selected])
        self.assertEqual(offer.affiliate_url, self.LINK)

    def test_invalid_or_incomplete_product_never_clears_existing_category(self):
        with self.assertRaises(CommandError):
            call_command(
                "publish_owner_affiliate_link",
                "https://untrusted.example/path",
                family=self.family.slug,
                replace_family=True,
            )
        with patch(
            "apps.catalog.management.commands.publish_owner_affiliate_link.resolve_aliexpress_product_url",
            return_value=(self.ID, self.CANONICAL),
        ), patch(
            "apps.catalog.management.commands.publish_owner_affiliate_link.AliExpressClient"
        ) as client:
            detail = self.detail()
            detail.price = None
            client.return_value.get_product_detail.return_value = detail
            with self.assertRaises(CommandError):
                call_command(
                    "publish_owner_affiliate_link",
                    self.LINK,
                    family=self.family.slug,
                    replace_family=True,
                )
        self.assertEqual(OfferFamilyPlacement.objects.filter(product_family=self.family).count(), 2)
        self.assertFalse(Offer.objects.filter(source=Offer.Source.ALIEXPRESS_OWNER).exists())

    def test_repeated_manual_link_is_idempotent(self):
        self.publish(replace_family=True)
        self.publish()
        self.assertEqual(
            Offer.objects.filter(
                source=Offer.Source.ALIEXPRESS_OWNER, external_product_id=self.ID
            ).count(), 1
        )
        self.assertEqual(OfferFamilyPlacement.objects.filter(product_family=self.family).count(), 1)

    def test_category_capacity_rejects_without_deleting_old(self):
        for n in range(18):
            offer = Offer.objects.create(
                source=Offer.Source.ALIEXPRESS, external_product_id=f"bulk-{n}"
            )
            OfferFamilyPlacement.objects.create(offer=offer, product_family=self.family)
        self.assertEqual(
            OfferFamilyPlacement.objects.filter(product_family=self.family).count(), 20
        )
        with self.assertRaises(CommandError):
            self.publish()
        self.assertEqual(
            OfferFamilyPlacement.objects.filter(product_family=self.family).count(), 20
        )
        self.assertFalse(Offer.objects.filter(source=Offer.Source.ALIEXPRESS_OWNER).exists())

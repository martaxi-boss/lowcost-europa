"""Synthetic, isolated browser-QA catalog; never run against a real customer database."""

import os
from decimal import Decimal

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.test")
import django

django.setup()

from django.utils import timezone  # noqa: E402

from apps.catalog.models import (  # noqa: E402
    Offer, OfferFamilyPlacement, OfferObservation, ProductFamily,
)


def seed():
    if ProductFamily.objects.exists() or Offer.objects.exists():
        raise RuntimeError("Refusing to overwrite a non-empty catalog")
    now = timezone.now()
    categories = (
        ("HIFU profissional", "hifu-profissional"),
        ("Laser estético", "laser-estetico"),
        ("Cavitação e radiofrequência", "cavitacao-radiofrequencia"),
        ("Hidrodermoabrasão", "hidrodermoabrasao"),
        ("Pressoterapia", "pressoterapia"),
    )
    count = 0
    for index, (name, slug) in enumerate(categories, 1):
        family = ProductFamily.objects.create(
            name=name,
            slug=slug,
            display_order=index,
            status=ProductFamily.Status.TESTING,
        )
        offers = 4 if index == 1 else 1
        for rank in range(1, offers + 1):
            count += 1
            offer = Offer.objects.create(
                source=Offer.Source.ALIEXPRESS,
                external_product_id=f"browser-qa-{index}-{rank}",
                product_family=family,
                title=f"{name} - equipamento demonstrativo {rank}",
                image_url="",  # Honest placeholder: no supplier photo fabricated.
                affiliate_url=f"https://affiliate.example.test/qa-{index}-{rank}",
                affiliate_promotion_status=Offer.AffiliatePromotionStatus.ELIGIBLE,
                affiliate_promotion_verified_at=now,
                ship_from_country="PL",
                ship_from_verified_at=now,
                protocol_verified_at=now,
                equipment_type=Offer.EquipmentType.DEDICATED,
            )
            OfferFamilyPlacement.objects.create(
                offer=offer,
                product_family=family,
                selection_position=rank,
                display_order=rank,
                selection_reason="Exemplo técnico para testar o layout.",
            )
            OfferObservation.objects.create(
                offer=offer,
                price=Decimal(250 + rank * 200 + (index - 1) * 100),
                currency="EUR",
                destination_country="PT",
                search_delivery_days=5,
                evaluation_rate_percent=Decimal("94.50"),
                sales_count=rank * 4,
            )
    print(f"SOURCE_BROWSER_QA_SEED=PASS families={len(categories)} offers={count}")


if __name__ == "__main__":
    seed()

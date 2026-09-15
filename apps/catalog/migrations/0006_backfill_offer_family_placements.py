from django.db import migrations


def backfill_offer_family_placements(apps, schema_editor):
    Offer = apps.get_model("catalog", "Offer")
    OfferFamilyPlacement = apps.get_model("catalog", "OfferFamilyPlacement")

    placements = []
    offers = Offer.objects.exclude(product_family_id=None).order_by("pk")
    for offer in offers.iterator():
        placements.append(
            OfferFamilyPlacement(
                offer_id=offer.pk,
                product_family_id=offer.product_family_id,
                selection_position=1 if offer.is_primary else None,
                display_order=0,
                selection_reason="",
            )
        )
    OfferFamilyPlacement.objects.bulk_create(placements)


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0005_offerfamilyplacement_offer_equipment_type_and_more"),
    ]

    operations = [
        migrations.RunPython(backfill_offer_family_placements, migrations.RunPython.noop),
    ]

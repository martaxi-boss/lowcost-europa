from django.db import migrations

OLD_07_SLUG = "depilacao-laser-triple-wave"
OLD_08_SLUG = "remocao-tatuagens-pigmentacao"
NEW_NAME = "Diodo Laser / Remoção de tatuagens / Pigmentação"
NEW_SLUG = "diodo-laser-remocao-tatuagens-pigmentacao"


def consolidate_taxonomy(apps, schema_editor):
    ProductFamily = apps.get_model("catalog", "ProductFamily")
    Offer = apps.get_model("catalog", "Offer")
    OfferCandidate = apps.get_model("catalog", "OfferCandidate")
    OfferFamilyPlacement = apps.get_model("catalog", "OfferFamilyPlacement")

    survivor = ProductFamily.objects.filter(slug=OLD_07_SLUG).first()
    retired = ProductFamily.objects.filter(slug=OLD_08_SLUG).first()
    if survivor is None and retired is None:
        # Fresh/empty installations have no legacy taxonomy data to consolidate.
        return
    if survivor is None or retired is None:
        raise RuntimeError("Incomplete legacy laser/tattoo taxonomy state")

    # Candidates retain identity, decisions, review signals, approved_offer and timestamps.
    OfferCandidate.objects.filter(product_family=retired).update(product_family=survivor)

    # Preserve the survivor's existing primary. If both families had a primary, the
    # retired-family primary becomes a normal offer before reassociation.
    survivor_has_primary = Offer.objects.filter(product_family=survivor, is_primary=True).exists()
    if survivor_has_primary:
        Offer.objects.filter(product_family=retired, is_primary=True).update(is_primary=False)
    Offer.objects.filter(product_family=retired).update(product_family=survivor)

    # Move placements defensively. Existing survivor placements win on overlap.
    # A conflicting selection slot on the destination is cleared on the migrated row.
    for placement in list(
        OfferFamilyPlacement.objects.filter(product_family=retired).order_by("pk")
    ):
        existing = OfferFamilyPlacement.objects.filter(
            product_family=survivor, offer_id=placement.offer_id
        ).first()
        if existing:
            placement.delete()
            continue
        if (
            placement.selection_position is not None
            and OfferFamilyPlacement.objects.filter(
                product_family=survivor, selection_position=placement.selection_position
            ).exists()
        ):
            placement.selection_position = None
        placement.product_family = survivor
        update_fields = ["product_family", "updated_at"]
        if placement.selection_position is None:
            update_fields.append("selection_position")
        placement.save(update_fields=update_fields)

    survivor.name = NEW_NAME
    survivor.slug = NEW_SLUG
    survivor.display_order = 7
    survivor.save(update_fields=["name", "slug", "display_order", "updated_at"])

    retired.status = "RETIRED"
    retired.save(update_fields=["status", "updated_at"])


class Migration(migrations.Migration):
    dependencies = [("catalog", "0013_owner_editorial_override")]

    operations = [
        migrations.RunPython(consolidate_taxonomy, migrations.RunPython.noop),
    ]

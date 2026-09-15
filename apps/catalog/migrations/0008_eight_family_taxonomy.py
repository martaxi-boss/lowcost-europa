from django.db import migrations

EXPECTED_FAMILIES = {
    1: ("Máquinas HIFU 7D", "maquinas-hifu-7d"),
    2: ("Máquinas HIFU 22D MAX", "maquinas-hifu-22d-max"),
    3: ("Máquinas Cavitation + RF Body Shaping", "maquinas-cavitation-rf-body-shaping"),
    4: ("Máquinas Diode Laser Hair Removal", "maquinas-diode-laser-hair-removal"),
    5: ("Máquinas Hydro Dermabrasion / Aqua Peel", "maquinas-hydro-dermabrasion-aqua-peel"),
}

EXPECTED_OFFERS = {
    51: ("1005012522304882", 1, True),
    52: ("1005013116584854", 1, False),
    53: ("1005013002556821", 2, True),
    54: ("1005012828137048", 3, True),
    55: ("1005012991431121", 4, True),
    56: ("1005012839981986", 5, True),
}

NEW_FAMILIES = (
    ("Radiofrequência facial", "radiofrequencia-facial", 3),
    ("Pressoterapia / Vacuum / Drenagem", "pressoterapia-vacuum-drenagem", 4),
    ("Microcorrente / Ultrassons", "microcorrente-ultrassons", 5),
    ("Remoção de tatuagens / pigmentação", "remocao-tatuagens-pigmentacao", 8),
)


def _fail(message):
    raise RuntimeError(f"EIGHT-FAMILY TAXONOMY 001 baseline mismatch: {message}")


def _validate_baseline(ProductFamily, Offer, OfferObservation, OfferClick, OfferFamilyPlacement):
    counts = (
        ProductFamily.objects.count(),
        Offer.objects.count(),
        OfferObservation.objects.count(),
        OfferFamilyPlacement.objects.count(),
    )
    if counts == (0, 0, 0, 0) and OfferClick.objects.count() == 0:
        return False
    if counts != (5, 6, 15, 6):
        _fail(f"counts={counts}, expected=(5, 6, 15, 6)")

    families = {
        pk: (name, slug)
        for pk, name, slug in ProductFamily.objects.order_by("pk").values_list("pk", "name", "slug")
    }
    if families != EXPECTED_FAMILIES:
        _fail(f"families={families!r}")

    offers = {
        pk: (external_id, family_id, is_primary)
        for pk, external_id, family_id, is_primary in Offer.objects.order_by("pk").values_list(
            "pk", "external_product_id", "product_family_id", "is_primary"
        )
    }
    if offers != EXPECTED_OFFERS:
        _fail(f"offers={offers!r}")

    placements = {
        offer_id: (family_id, position)
        for offer_id, family_id, position in OfferFamilyPlacement.objects.order_by(
            "offer_id"
        ).values_list("offer_id", "product_family_id", "selection_position")
    }
    expected_placements = {
        51: (1, 1),
        52: (1, None),
        53: (2, 1),
        54: (3, 1),
        55: (4, 1),
        56: (5, 1),
    }
    if placements != expected_placements:
        _fail(f"placements={placements!r}")

    if Offer.objects.exclude(equipment_type="UNKNOWN").exists():
        _fail("equipment_type must remain UNKNOWN for all six Offers")
    return True


def apply_eight_family_taxonomy(apps, schema_editor):
    ProductFamily = apps.get_model("catalog", "ProductFamily")
    Offer = apps.get_model("catalog", "Offer")
    OfferObservation = apps.get_model("catalog", "OfferObservation")
    OfferClick = apps.get_model("catalog", "OfferClick")
    OfferFamilyPlacement = apps.get_model("catalog", "OfferFamilyPlacement")

    if not _validate_baseline(
        ProductFamily, Offer, OfferObservation, OfferClick, OfferFamilyPlacement
    ):
        return

    clicks_before = OfferClick.objects.count()
    observations_before = OfferObservation.objects.count()

    family_1 = ProductFamily.objects.get(pk=1)
    family_2 = ProductFamily.objects.get(pk=2)
    family_3 = ProductFamily.objects.get(pk=3)
    family_4 = ProductFamily.objects.get(pk=4)
    family_5 = ProductFamily.objects.get(pk=5)

    # Avoid the legacy one-primary-per-family constraint before moving Offer 53.
    Offer.objects.filter(pk=53).update(is_primary=False)
    Offer.objects.filter(pk=53).update(product_family_id=1)
    OfferFamilyPlacement.objects.filter(offer_id=53).update(
        product_family_id=1,
        selection_position=2,
    )

    family_1.name = "HIFU"
    family_1.slug = "hifu"
    family_1.display_order = 6
    family_1.save(update_fields=["name", "slug", "display_order", "updated_at"])

    family_2.status = "RETIRED"
    family_2.display_order = 99
    family_2.save(update_fields=["status", "display_order", "updated_at"])

    existing_updates = (
        (family_3, "Cavitação + RF + Vacuum (corpo)", "cavitacao-rf-vacuum-corpo", 1),
        (
            family_5,
            "Hydrodermoabrasão / Aqua Facial / Multifunções faciais",
            "hydrodermoabrasao-aqua-facial-multifuncoes",
            2,
        ),
        (family_4, "Depilação Laser Triple Wave", "depilacao-laser-triple-wave", 7),
    )
    for family, name, slug, display_order in existing_updates:
        family.name = name
        family.slug = slug
        family.display_order = display_order
        family.save(update_fields=["name", "slug", "display_order", "updated_at"])

    for name, slug, display_order in NEW_FAMILIES:
        ProductFamily.objects.create(
            name=name,
            slug=slug,
            status="NEW",
            display_order=display_order,
        )

    if ProductFamily.objects.count() != 9:
        _fail("post-migration ProductFamily total must be 9")
    if ProductFamily.objects.exclude(status="RETIRED").count() != 8:
        _fail("post-migration active/non-retired ProductFamily count must be 8")
    if ProductFamily.objects.filter(status="RETIRED").count() != 1:
        _fail("post-migration retired ProductFamily count must be 1")
    if Offer.objects.count() != 6 or OfferFamilyPlacement.objects.count() != 6:
        _fail("Offer and placement counts must remain 6")
    if OfferObservation.objects.count() != observations_before:
        _fail("OfferObservation count changed")
    if OfferClick.objects.count() != clicks_before:
        _fail("OfferClick count changed")
    if Offer.objects.exclude(equipment_type="UNKNOWN").exists():
        _fail("equipment_type changed unexpectedly")


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0007_productfamily_display_order"),
    ]

    operations = [
        migrations.RunPython(apply_eight_family_taxonomy, migrations.RunPython.noop),
    ]

from django.db import migrations

SURVIVING_UPDATES = {
    "cavitacao-rf-vacuum-corpo": ("Cavitação + RF + Vacuum", 1),
    "hydrodermoabrasao-aqua-facial-multifuncoes": (
        "Microdermoabrasão / Hidrodermoabrasão / Multifunções faciais",
        2,
    ),
    "pressoterapia-vacuum-drenagem": ("Pressoterapia / Drenagem", 3),
    "hifu": ("HIFU", 4),
    "diodo-laser-remocao-tatuagens-pigmentacao": (
        "Diodo Laser / Remoção de tatuagens / Pigmentação",
        5,
    ),
}

RETIRE_SLUGS = ("radiofrequencia-facial", "microcorrente-ultrassons")

PREVIOUS_VALUES = {
    "cavitacao-rf-vacuum-corpo": ("Cavitação + RF + Vacuum (corpo)", 1, "NEW"),
    "hydrodermoabrasao-aqua-facial-multifuncoes": (
        "Microdermoabrasão / Hidrodermoabrasão / Multifunções faciais",
        2,
        "NEW",
    ),
    "radiofrequencia-facial": ("Radiofrequência facial", 3, "NEW"),
    "pressoterapia-vacuum-drenagem": ("Pressoterapia / Vacuum / Drenagem", 4, "NEW"),
    "microcorrente-ultrassons": ("Microcorrente / Ultrassons", 5, "NEW"),
    "hifu": ("HIFU", 6, "NEW"),
    "diodo-laser-remocao-tatuagens-pigmentacao": (
        "Diodo Laser / Remoção de tatuagens / Pigmentação",
        7,
        "NEW",
    ),
}


def apply_taxonomy_reduction(apps, schema_editor):
    ProductFamily = apps.get_model("catalog", "ProductFamily")
    if not ProductFamily.objects.exists():
        return
    required = set(SURVIVING_UPDATES) | set(RETIRE_SLUGS)
    current = {
        slug: (name, display_order, status)
        for slug, name, display_order, status in ProductFamily.objects.filter(
            slug__in=required
        ).values_list("slug", "name", "display_order", "status")
    }
    missing = required - set(current)
    if missing:
        raise RuntimeError(f"TAXONOMY REDUCTION 001 missing families: {sorted(missing)}")
    mismatches = {
        slug: (current[slug], PREVIOUS_VALUES[slug])
        for slug in required
        if current[slug] != PREVIOUS_VALUES[slug]
    }
    if mismatches:
        raise RuntimeError(f"TAXONOMY REDUCTION 001 baseline mismatch: {mismatches!r}")

    ProductFamily.objects.filter(slug__in=RETIRE_SLUGS).update(status="RETIRED")
    for slug, (name, display_order) in SURVIVING_UPDATES.items():
        ProductFamily.objects.filter(slug=slug).update(name=name, display_order=display_order)


def reverse_taxonomy_reduction(apps, schema_editor):
    ProductFamily = apps.get_model("catalog", "ProductFamily")
    for slug, (name, display_order, status) in PREVIOUS_VALUES.items():
        ProductFamily.objects.filter(slug=slug).update(
            name=name,
            display_order=display_order,
            status=status,
        )


class Migration(migrations.Migration):
    dependencies = [("catalog", "0016_candidatefamilymoveevent")]
    operations = [migrations.RunPython(apply_taxonomy_reduction, reverse_taxonomy_reduction)]

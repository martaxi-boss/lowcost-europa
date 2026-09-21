from django.db import migrations

SLUG = "pressoterapia-vacuum-drenagem"
OLD_NAME = "Pressoterapia / Drenagem"
NEW_NAME = "Pressoterapia / RF Tecar"


def rename_family(apps, schema_editor):
    ProductFamily = apps.get_model("catalog", "ProductFamily")
    ProductFamily.objects.filter(slug=SLUG).update(name=NEW_NAME)


def restore_family_name(apps, schema_editor):
    ProductFamily = apps.get_model("catalog", "ProductFamily")
    ProductFamily.objects.filter(slug=SLUG).update(name=OLD_NAME)


class Migration(migrations.Migration):
    dependencies = [("catalog", "0017_taxonomy_reduction_menu_realignment")]

    operations = [migrations.RunPython(rename_family, restore_family_name)]

from django.db import migrations

SLUG = "hydrodermoabrasao-aqua-facial-multifuncoes"
OLD_NAME = "Hydrodermoabrasão / Aqua Facial / Multifunções faciais"
NEW_NAME = "Microdermoabrasão / Hidrodermoabrasão / Multifunções faciais"


def rename_family(apps, schema_editor):
    ProductFamily = apps.get_model("catalog", "ProductFamily")
    family = ProductFamily.objects.filter(slug=SLUG).first()
    if family is None:
        return
    family.name = NEW_NAME
    family.save(update_fields=["name", "updated_at"])


def restore_family_name(apps, schema_editor):
    ProductFamily = apps.get_model("catalog", "ProductFamily")
    family = ProductFamily.objects.filter(slug=SLUG).first()
    if family is None:
        return
    family.name = OLD_NAME
    family.save(update_fields=["name", "updated_at"])


class Migration(migrations.Migration):
    dependencies = [("catalog", "0014_consolidate_laser_tattoo_taxonomy")]

    operations = [migrations.RunPython(rename_family, restore_family_name)]

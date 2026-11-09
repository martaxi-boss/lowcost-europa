"""Delete the disconnected advertising account aggregate, preserving other sources."""

from django.db import migrations


def purge_meta_aggregate(apps, schema_editor):
    snapshot = apps.get_model("catalog", "ExternalMetricsSnapshot")
    snapshot.objects.using(schema_editor.connection.alias).filter(source="META").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0020_externalmetricssnapshot"),
    ]

    operations = [
        migrations.RunPython(purge_meta_aggregate, reverse_code=migrations.RunPython.noop),
    ]

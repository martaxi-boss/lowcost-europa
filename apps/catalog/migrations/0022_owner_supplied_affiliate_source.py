from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [("catalog", "0021_purge_disconnected_meta_snapshot")]

    operations = [
        migrations.AlterField(
            model_name="offer",
            name="source",
            field=models.CharField(
                max_length=30,
                choices=[
                    ("ALIEXPRESS", "AliExpress"),
                    ("ALIEXPRESS_OWNER", "AliExpress"),
                ],
            ),
        ),
        migrations.AlterField(
            model_name="offercandidate",
            name="source",
            field=models.CharField(
                max_length=30,
                choices=[
                    ("ALIEXPRESS", "AliExpress"),
                    ("ALIEXPRESS_OWNER", "AliExpress"),
                ],
            ),
        ),
        migrations.RemoveConstraint(
            model_name="offer",
            name="catalog_offer_source_valid",
        ),
        migrations.AddConstraint(
            model_name="offer",
            constraint=models.CheckConstraint(
                condition=Q(source__in=["ALIEXPRESS", "ALIEXPRESS_OWNER"]),
                name="catalog_offer_source_valid",
            ),
        ),
    ]

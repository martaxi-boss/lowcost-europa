from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0019_affiliate_promotion_gate"),
    ]

    operations = [
        migrations.CreateModel(
            name="ExternalMetricsSnapshot",
            fields=[
                ("source", models.CharField(max_length=24, primary_key=True, serialize=False)),
                ("period_start", models.DateTimeField()),
                ("period_end", models.DateTimeField()),
                ("checked_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("payload", models.JSONField(default=dict)),
            ],
        ),
    ]

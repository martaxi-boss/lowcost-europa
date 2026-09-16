from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0009_candidatedecision_offercandidate_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='candidatedecision',
            name='reason',
            field=models.CharField(blank=True, choices=[('DOES_NOT_SHIP_TO_PT', 'Não envia para Portugal'), ('PT_DELIVERY_NOT_CONFIRMED', 'Não consigo confirmar entrega em Portugal'), ('ORIGIN_NOT_CONFIRMED', 'País de envio não aparece / não consigo confirmar'), ('ORIGIN_NOT_ALLOWED', 'País de envio fora dos 5 permitidos'), ('WRONG_FAMILY', 'Produto pertence a outra família'), ('ACCESSORY_OR_PART', 'Acessório, peça, cartucho ou consumível'), ('DUPLICATE', 'Produto duplicado'), ('LISTING_UNAVAILABLE', 'Anúncio indisponível'), ('LISTING_CHANGED', 'Anúncio ou variante mudou'), ('POOR_LISTING', 'Oferta/listagem sem qualidade suficiente'), ('OTHER', 'Outro motivo'), ('IRRELEVANT', 'Irrelevante (legado)')], max_length=30),
        ),
    ]

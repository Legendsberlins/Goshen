from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gosh_main', '0011_logisticscompany_ordertracking_trackinghistory'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='unit',
            field=models.CharField(
                choices=[
                    ('item', 'Item'),
                    ('kg', 'Kilogram (kg)'),
                    ('g', 'Gram (g)'),
                    ('l', 'Liter (L)'),
                    ('ml', 'Milliliter (ml)'),
                    ('bag', 'Bag'),
                    ('bottle', 'Bottle'),
                    ('pack', 'Pack'),
                ],
                default='item',
                max_length=20,
            ),
        ),
    ]

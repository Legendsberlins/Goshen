from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gosh_main', '0008_seed_feature_data'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='is_featured',
            field=models.BooleanField(default=False),
        ),
    ]

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gosh_main', '0006_restaurantorder'),
    ]

    operations = [
        migrations.CreateModel(
            name='Feature',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('image', models.CharField(help_text="Static path under static/ (e.g. 'gosh_main/images/features/natural.png')", max_length=255)),
            ],
            options={
                'ordering': ['id'],
            },
        ),
    ]

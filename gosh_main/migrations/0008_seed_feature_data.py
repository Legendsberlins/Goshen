from django.db import migrations


def seed_features(apps, schema_editor):
    Feature = apps.get_model('gosh_main', 'Feature')

    default_features = [
        {
            'title': '100% Natural Ingredients',
            'description': 'We use only naturally grown and responsibly sourced ingredients—free from artificial preservatives, additives, and GMOs. What you see is what you eat.',
            'image': 'gosh_main/images/Feature_1.jpg',
        },
        {
            'title': 'Proudly African, Globally Trusted',
            'description': 'Rooted in Africa, reaching the world. Our products bring the rich taste of African heritage to homes across Nigeria, the diaspora, and beyond.',
            'image': 'gosh_main/images/Feature_2.jpg',
        },
        {
            'title': 'Reliable Nationwide & International Delivery',
            'description': 'We deliver across Nigeria and ship to the USA, UK, Canada, and beyond. Whether retail or wholesale, we get your order to your doorstep—fast and fresh.',
            'image': 'gosh_main/images/Feature_3.jpg',
        },
    ]

    for feature in default_features:
        Feature.objects.get_or_create(
            title=feature['title'],
            defaults={
                'description': feature['description'],
                'image': feature['image'],
            },
        )


def unseed_features(apps, schema_editor):
    Feature = apps.get_model('gosh_main', 'Feature')
    Feature.objects.filter(title__in=[
        '100% Natural Ingredients',
        'Proudly African, Globally Trusted',
        'Reliable Nationwide & International Delivery',
    ]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('gosh_main', '0007_feature'),
    ]

    operations = [
        migrations.RunPython(seed_features, unseed_features),
    ]

import re
from django.db import migrations


def infer_unit_from_name(name: str) -> str:
    if not name:
        return 'item'

    text = str(name).lower()

    if re.search(r'\b\d+(?:\.\d+)?\s*kg\b', text):
        return 'kg'
    if re.search(r'\b\d+(?:\.\d+)?\s*g\b', text):
        return 'g'
    if re.search(r'\b\d+(?:\.\d+)?\s*ml\b', text):
        return 'ml'
    if re.search(r'\b\d+(?:\.\d+)?\s*l\b', text):
        return 'l'

    if re.search(r'\bbag\b', text):
        return 'bag'
    if re.search(r'\bbottle\b', text):
        return 'bottle'
    if re.search(r'\bpack\b', text):
        return 'pack'

    return 'item'


def backfill_product_units(apps, schema_editor):
    Product = apps.get_model('gosh_main', 'Product')

    for product in Product.objects.all().only('id', 'name', 'unit'):
        inferred = infer_unit_from_name(product.name)
        if product.unit != inferred:
            product.unit = inferred
            product.save(update_fields=['unit'])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('gosh_main', '0012_product_unit'),
    ]

    operations = [
        migrations.RunPython(backfill_product_units, noop_reverse),
    ]

from django.db import migrations


def apply_revised_catalog(apps, schema_editor):
    Category = apps.get_model('gosh_main', 'Category')
    Product = apps.get_model('gosh_main', 'Product')

    categories = [
        {
            'name': 'African Vegetable Leaves & Pods',
            'slug': 'vegetable-leaves',
            'description': 'Dried African vegetable leaves and pods',
            'default_image': 'gosh_main/images/product6.jpg',
        },
        {
            'name': 'African Staples & Thickeners',
            'slug': 'staples-thickeners',
            'description': 'African staple foods and soup thickeners',
            'default_image': 'gosh_main/images/Feature_1.jpg',
        },
        {
            'name': 'African Seafoods',
            'slug': 'seafoods',
            'description': 'Smoked, dried, and preserved seafoods',
            'default_image': 'gosh_main/images/Feature_2.jpg',
        },
        {
            'name': 'African Plant-Milk Beverages',
            'slug': 'plant-milk',
            'description': 'Natural plant-based milk beverages',
            'default_image': 'gosh_main/images/product4.jpg',
        },
        {
            'name': 'Natural African Edible Oils & Fats',
            'slug': 'oils-fats',
            'description': 'Natural edible oils and fats',
            'default_image': 'gosh_main/images/product5.jpg',
        },
        {
            'name': 'African Flours & Grains',
            'slug': 'flours-grains',
            'description': 'Traditional African flours and grains',
            'default_image': 'gosh_main/images/Feature_3.jpg',
        },
        {
            'name': 'African Condiments & Seasonings',
            'slug': 'condiments-seasonings',
            'description': 'Spices, powders, and cooking condiments',
            'default_image': 'gosh_main/images/product5.jpg',
        },
        {
            'name': 'Natural African Juices & Beverages',
            'slug': 'juices-beverages',
            'description': 'Natural juices and beverages',
            'default_image': 'gosh_main/images/product2.jpg',
        },
        {
            'name': 'Packaged Drinking Water',
            'slug': 'packaged-water',
            'description': 'Packaged and bottled drinking water',
            'default_image': 'gosh_main/images/product6.jpg',
        },
        {
            'name': 'Animal Feeds',
            'slug': 'animal-feeds',
            'description': 'Animal feed products',
            'default_image': 'gosh_main/images/product4.jpg',
        },
    ]

    category_map = {}
    for cat in categories:
        category_obj, _ = Category.objects.get_or_create(
            slug=cat['slug'],
            defaults={
                'name': cat['name'],
                'description': cat['description'],
            },
        )
        category_map[cat['slug']] = category_obj

    old_seed_slugs = [
        'ground-egusi-500g',
        'dried-ukazi-50g',
        'smoked-catfish-1kg',
        'tigernut-milk-500ml',
        'red-palm-oil-1l',
        'plantain-flour-1kg',
    ]
    Product.objects.filter(slug__in=old_seed_slugs).delete()

    products = [
        {'name': 'Dried Ukazi (Afang) Leaf - 1kg', 'slug': 'dried-ukazi-afang-leaf-1kg', 'category': 'vegetable-leaves'},
        {'name': 'Dried Bitter Leaf - 1kg', 'slug': 'dried-bitter-leaf-1kg', 'category': 'vegetable-leaves'},
        {'name': 'Dried Ugu (Fluted Pumpkin) - 1kg', 'slug': 'dried-ugu-fluted-pumpkin-1kg', 'category': 'vegetable-leaves'},
        {'name': 'Dried Utazi Leaf - 1kg', 'slug': 'dried-utazi-leaf-1kg', 'category': 'vegetable-leaves'},
        {'name': 'Ground Melon (Egusi) - 1kg', 'slug': 'ground-melon-egusi-1kg', 'category': 'staples-thickeners'},
        {'name': 'Whole Melon (Egusi) Seeds - 5kg', 'slug': 'whole-melon-egusi-seeds-5kg', 'category': 'staples-thickeners'},
        {'name': 'Ground Ogbono Seeds - 1kg', 'slug': 'ground-ogbono-seeds-1kg', 'category': 'staples-thickeners'},
        {'name': 'Whole Ogbono Seeds - 5kg', 'slug': 'whole-ogbono-seeds-5kg', 'category': 'staples-thickeners'},
        {'name': 'Catfish (Smoked) - 5kg', 'slug': 'catfish-smoked-5kg', 'category': 'seafoods'},
        {'name': 'Crayfish (Whole) - 5kg', 'slug': 'crayfish-whole-5kg', 'category': 'seafoods'},
        {'name': 'Crayfish (Ground) - 5kg', 'slug': 'crayfish-ground-5kg', 'category': 'seafoods'},
        {'name': 'Snail (Dried, Frozen) - 5kg', 'slug': 'snail-dried-frozen-5kg', 'category': 'seafoods'},
        {'name': 'Tigernut Milk - 500ml', 'slug': 'tigernut-milk-500ml', 'category': 'plant-milk'},
        {'name': 'Coconut Milk - 500ml', 'slug': 'coconut-milk-500ml', 'category': 'plant-milk'},
        {'name': 'Almond Milk - 500ml', 'slug': 'almond-milk-500ml', 'category': 'plant-milk'},
        {'name': 'Soy Milk - 500ml', 'slug': 'soy-milk-500ml', 'category': 'plant-milk'},
        {'name': 'Red Palm Oil - 5L', 'slug': 'red-palm-oil-5l', 'category': 'oils-fats'},
        {'name': 'Groundnut Oil - 5L', 'slug': 'groundnut-oil-5l', 'category': 'oils-fats'},
        {'name': 'Sunflower Oil - 5L', 'slug': 'sunflower-oil-5l', 'category': 'oils-fats'},
        {'name': 'Palm Olein Vegetable Oil - 5L', 'slug': 'palm-olein-vegetable-oil-5l', 'category': 'oils-fats'},
        {'name': 'Soybean Oil - 5L', 'slug': 'soybean-oil-5l', 'category': 'oils-fats'},
        {'name': 'Almond Oil - 5L', 'slug': 'almond-oil-5l', 'category': 'oils-fats'},
        {'name': 'Coconut Oil - 5L', 'slug': 'coconut-oil-5l', 'category': 'oils-fats'},
        {'name': 'Yam Flour - 5kg', 'slug': 'yam-flour-5kg', 'category': 'flours-grains'},
        {'name': 'Cassava Flour - 5kg', 'slug': 'cassava-flour-5kg', 'category': 'flours-grains'},
        {'name': 'Plantain Flour - 5kg', 'slug': 'plantain-flour-5kg', 'category': 'flours-grains'},
        {'name': 'Cocoyam Flour - 5kg', 'slug': 'cocoyam-flour-5kg', 'category': 'flours-grains'},
        {'name': 'Almond Flour - 5kg', 'slug': 'almond-flour-5kg', 'category': 'flours-grains'},
        {'name': 'Soybean Flour - 5kg', 'slug': 'soybean-flour-5kg', 'category': 'flours-grains'},
        {'name': 'Honey Bean Flour - 5kg', 'slug': 'honey-bean-flour-5kg', 'category': 'flours-grains'},
        {'name': 'Garri (Yellow & White) - 5kg', 'slug': 'garri-yellow-white-5kg', 'category': 'flours-grains'},
        {'name': 'Dry Red Pepper (Chili / Cameroon Pepper)', 'slug': 'dry-red-pepper-chili-cameroon-pepper', 'category': 'condiments-seasonings'},
        {'name': 'Ginger Powder - 198g', 'slug': 'ginger-powder-198g', 'category': 'condiments-seasonings'},
        {'name': 'Garlic Powder - 198g', 'slug': 'garlic-powder-198g', 'category': 'condiments-seasonings'},
        {'name': 'Turmeric Powder - 198g', 'slug': 'turmeric-powder-198g', 'category': 'condiments-seasonings'},
        {'name': 'Dry Onion Powder - 198g', 'slug': 'dry-onion-powder-198g', 'category': 'condiments-seasonings'},
        {'name': 'Red Pepper Paste - 198g', 'slug': 'red-pepper-paste-198g', 'category': 'condiments-seasonings'},
        {'name': 'Tomato Paste - 198g', 'slug': 'tomato-paste-198g', 'category': 'condiments-seasonings'},
        {'name': 'Tomato Ketchup - 1kg', 'slug': 'tomato-ketchup-1kg', 'category': 'condiments-seasonings'},
        {'name': 'Ginger Juice - 500ml', 'slug': 'ginger-juice-500ml', 'category': 'juices-beverages'},
        {'name': 'Zobo (Hibiscus Drink) - 500ml', 'slug': 'zobo-hibiscus-drink-500ml', 'category': 'juices-beverages'},
        {'name': 'Turmeric Juice - 500ml', 'slug': 'turmeric-juice-500ml', 'category': 'juices-beverages'},
        {'name': 'Orange Juice - 500ml', 'slug': 'orange-juice-500ml', 'category': 'juices-beverages'},
        {'name': 'Pineapple Juice - 500ml', 'slug': 'pineapple-juice-500ml', 'category': 'juices-beverages'},
        {'name': 'Apple Juice - 500ml', 'slug': 'apple-juice-500ml', 'category': 'juices-beverages'},
        {'name': 'Mango Juice - 500ml', 'slug': 'mango-juice-500ml', 'category': 'juices-beverages'},
        {'name': 'Watermelon Juice - 500ml', 'slug': 'watermelon-juice-500ml', 'category': 'juices-beverages'},
        {'name': 'Table Water - 500ml', 'slug': 'table-water-500ml', 'category': 'packaged-water'},
        {'name': 'Sachet Water - 500ml', 'slug': 'sachet-water-500ml', 'category': 'packaged-water'},
        {'name': 'Fish Feed - 15kg', 'slug': 'fish-feed-15kg', 'category': 'animal-feeds'},
        {'name': 'Poultry Feed - 25kg', 'slug': 'poultry-feed-25kg', 'category': 'animal-feeds'},
    ]

    featured_slugs = {
        'ground-melon-egusi-1kg',
        'dried-ukazi-afang-leaf-1kg',
        'catfish-smoked-5kg',
        'tigernut-milk-500ml',
        'red-palm-oil-5l',
        'plantain-flour-5kg',
    }

    for item in products:
        category_slug = item['category']
        category_obj = category_map[category_slug]
        category_image = next(c['default_image'] for c in categories if c['slug'] == category_slug)

        Product.objects.update_or_create(
            slug=item['slug'],
            defaults={
                'name': item['name'],
                'description': item['name'],
                'price': None,
                'category': category_obj,
                'image': category_image,
                'is_featured': item['slug'] in featured_slugs,
            },
        )


def unapply_revised_catalog(apps, schema_editor):
    Product = apps.get_model('gosh_main', 'Product')

    revised_slugs = [
        'dried-ukazi-afang-leaf-1kg',
        'dried-bitter-leaf-1kg',
        'dried-ugu-fluted-pumpkin-1kg',
        'dried-utazi-leaf-1kg',
        'ground-melon-egusi-1kg',
        'whole-melon-egusi-seeds-5kg',
        'ground-ogbono-seeds-1kg',
        'whole-ogbono-seeds-5kg',
        'catfish-smoked-5kg',
        'crayfish-whole-5kg',
        'crayfish-ground-5kg',
        'snail-dried-frozen-5kg',
        'tigernut-milk-500ml',
        'coconut-milk-500ml',
        'almond-milk-500ml',
        'soy-milk-500ml',
        'red-palm-oil-5l',
        'groundnut-oil-5l',
        'sunflower-oil-5l',
        'palm-olein-vegetable-oil-5l',
        'soybean-oil-5l',
        'almond-oil-5l',
        'coconut-oil-5l',
        'yam-flour-5kg',
        'cassava-flour-5kg',
        'plantain-flour-5kg',
        'cocoyam-flour-5kg',
        'almond-flour-5kg',
        'soybean-flour-5kg',
        'honey-bean-flour-5kg',
        'garri-yellow-white-5kg',
        'dry-red-pepper-chili-cameroon-pepper',
        'ginger-powder-198g',
        'garlic-powder-198g',
        'turmeric-powder-198g',
        'dry-onion-powder-198g',
        'red-pepper-paste-198g',
        'tomato-paste-198g',
        'tomato-ketchup-1kg',
        'ginger-juice-500ml',
        'zobo-hibiscus-drink-500ml',
        'turmeric-juice-500ml',
        'orange-juice-500ml',
        'pineapple-juice-500ml',
        'apple-juice-500ml',
        'mango-juice-500ml',
        'watermelon-juice-500ml',
        'table-water-500ml',
        'sachet-water-500ml',
        'fish-feed-15kg',
        'poultry-feed-25kg',
    ]

    Product.objects.filter(slug__in=revised_slugs).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('gosh_main', '0009_product_is_featured'),
    ]

    operations = [
        migrations.RunPython(apply_revised_catalog, unapply_revised_catalog),
    ]

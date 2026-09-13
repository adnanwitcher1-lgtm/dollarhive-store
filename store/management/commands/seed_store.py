"""
Seeds a handful of sample categories and products so the storefront
isn't empty on first run.

Usage:
    python manage.py seed_store
"""
from django.core.management.base import BaseCommand
from store.models import Category, Product


CATEGORIES = ['Electronics', 'Laptops', 'Audio', 'Home', 'Watches', 'Kitchen', 'Sports', 'Toys']

PRODUCTS = [
    ('Wireless Bluetooth Headphones', 'Audio', 29.99, 59.99, True),
    ('Smart Fitness Watch', 'Watches', 34.99, 64.99, True),
    ('Portable Blender Bottle', 'Kitchen', 14.99, 24.99, False),
    ('14" Slim Laptop Sleeve', 'Laptops', 9.99, 19.99, False),
    ('4K Action Camera', 'Electronics', 44.99, 89.99, True),
    ('Non-Stick Cookware Set', 'Kitchen', 39.99, 79.99, False),
    ('Yoga Mat with Carry Strap', 'Sports', 12.99, None, False),
    ('Building Blocks Set (300pc)', 'Toys', 17.99, 29.99, False),
    ('LED Desk Lamp', 'Home', 11.99, 21.99, False),
    ('Noise Cancelling Earbuds', 'Audio', 24.99, 49.99, True),
    ('Mechanical Gaming Keyboard', 'Electronics', 27.99, None, False),
    ('Stainless Steel Water Bottle', 'Sports', 8.99, 15.99, False),
]


class Command(BaseCommand):
    help = 'Seeds sample categories and products for the DollarHive storefront.'

    def handle(self, *args, **options):
        cat_objs = {}
        for name in CATEGORIES:
            cat, created = Category.objects.get_or_create(name=name)
            cat_objs[name] = cat
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created category: {name}'))

        for name, cat_name, price, discount_price, featured in PRODUCTS:
            product, created = Product.objects.get_or_create(
                name=name,
                defaults={
                    'category': cat_objs[cat_name],
                    'price': price,
                    'discount_price': discount_price,
                    'is_featured': featured,
                    'stock': 25,
                    'description': f'{name} — a DollarHive customer favorite. Quality checked and ready to ship.',
                },
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created product: {name}'))

        self.stdout.write(self.style.SUCCESS('DollarHive sample data seeded successfully.'))

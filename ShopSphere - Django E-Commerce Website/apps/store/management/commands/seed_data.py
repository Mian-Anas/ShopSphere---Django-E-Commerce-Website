"""
Management command: seed_data
Populates the database with demo categories, brands, and products.

Usage:
    python manage.py seed_data
"""
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from apps.store.models import Category, Brand, Product
from decimal import Decimal
import random


CATEGORIES = [
    ('Electronics', '💻'),
    ('Fashion', '👗'),
    ('Home & Garden', '🏡'),
    ('Sports & Outdoors', '⚽'),
    ('Books', '📚'),
    ('Beauty & Health', '💄'),
]

BRANDS = ['Apple', 'Samsung', 'Nike', 'Adidas', 'IKEA', 'Sony', 'LG', 'Zara']

PRODUCTS = [
    ('iPhone 15 Pro', 'Electronics', 'Apple', 999.99, 899.99, 50, True),
    ('Samsung Galaxy S24', 'Electronics', 'Samsung', 849.99, None, 30, True),
    ('Sony WH-1000XM5 Headphones', 'Electronics', 'Sony', 349.99, 279.99, 25, True),
    ('LG 4K OLED TV 55"', 'Electronics', 'LG', 1499.99, 1199.99, 10, True),
    ('Nike Air Max 270', 'Sports & Outdoors', 'Nike', 149.99, 119.99, 80, True),
    ('Adidas Ultraboost 23', 'Sports & Outdoors', 'Adidas', 189.99, 159.99, 60, True),
    ('Nike Dri-FIT T-Shirt', 'Fashion', 'Nike', 34.99, None, 200, False),
    ('Zara Premium Blazer', 'Fashion', 'Zara', 89.99, 64.99, 40, False),
    ('IKEA KALLAX Shelf', 'Home & Garden', 'IKEA', 79.99, None, 15, False),
    ('IKEA POÄNG Chair', 'Home & Garden', 'IKEA', 119.99, 89.99, 8, True),
    ('The Pragmatic Programmer', 'Books', None, 49.99, 39.99, 100, False),
    ('Clean Code', 'Books', None, 44.99, None, 75, False),
    ('Samsung Galaxy Buds Pro', 'Electronics', 'Samsung', 199.99, 149.99, 45, False),
    ('Nike Running Shorts', 'Sports & Outdoors', 'Nike', 39.99, None, 150, False),
    ('Apple AirPods Pro', 'Electronics', 'Apple', 249.99, 209.99, 35, True),
    ('Sony PlayStation 5', 'Electronics', 'Sony', 499.99, None, 5, True),
]


class Command(BaseCommand):
    help = 'Seed the database with demo categories, brands, and products'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('[Seed] Seeding ShopSphere demo data...'))

        # Create Categories
        cat_objs = {}
        for name, icon in CATEGORIES:
            cat, created = Category.objects.get_or_create(
                name=name,
                defaults={'slug': slugify(name), 'description': f'{icon} {name} products'}
            )
            cat_objs[name] = cat
            status = '  Created' if created else '  Exists'
            self.stdout.write(f'{status}: Category -> {name}')

        # Create Brands
        brand_objs = {}
        for name in BRANDS:
            brand, created = Brand.objects.get_or_create(
                name=name,
                defaults={'slug': slugify(name)}
            )
            brand_objs[name] = brand
            status = '  Created' if created else '  Exists'
            self.stdout.write(f'{status}: Brand -> {name}')

        # Create Products
        created_count = 0
        for data in PRODUCTS:
            name, cat_name, brand_name, price, disc_price, stock, featured = data
            product, created = Product.objects.get_or_create(
                name=name,
                defaults={
                    'category': cat_objs.get(cat_name),
                    'brand': brand_objs.get(brand_name) if brand_name else None,
                    'price': Decimal(str(price)),
                    'discount_price': Decimal(str(disc_price)) if disc_price else None,
                    'stock': stock,
                    'is_active': True,
                    'is_featured': featured,
                    'description': f'Premium quality {name}. This is a demo product description showcasing the quality and features of {name}. Perfect for everyday use with exceptional build quality and reliability.',
                }
            )
            if created:
                created_count += 1
                self.stdout.write(f'  Created: Product -> {name}')

        self.stdout.write(self.style.SUCCESS(
            f'\n[Success] Done! Created {created_count} new products, '
            f'{len(CATEGORIES)} categories, {len(BRANDS)} brands.\n'
            f'Run: python manage.py runserver'
        ))

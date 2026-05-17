"""
Seed the Category table with the 12 default categories.
Uses get_or_create so re-running migrations on an already-populated DB is safe.
"""

from django.db import migrations

CATEGORIES = [
    "Electronics",
    "Clothing & Shoes",
    "Furniture",
    "Books",
    "Sports & Outdoors",
    "Toys & Games",
    "Vehicles",
    "Home & Garden",
    "Musical Instruments",
    "Art & Collectibles",
    "Baby & Kids",
    "Other",
]


def seed_categories(apps, schema_editor):
    Category = apps.get_model("marketplace", "Category")
    for name in CATEGORIES:
        Category.objects.get_or_create(name=name)


def unseed_categories(apps, schema_editor):
    Category = apps.get_model("marketplace", "Category")
    Category.objects.filter(name__in=CATEGORIES).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("marketplace", "0006_sprint4_messaging"),
    ]

    operations = [
        migrations.RunPython(seed_categories, reverse_code=unseed_categories),
    ]

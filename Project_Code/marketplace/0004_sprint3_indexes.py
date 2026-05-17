"""
Sprint 3 — Search & Browse performance indexes.
Adds B-tree indexes on fields used in WHERE / ORDER BY clauses.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0003_item_sprint2_fields'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='item',
            index=models.Index(fields=['status'], name='item_status_idx'),
        ),
        migrations.AddIndex(
            model_name='item',
            index=models.Index(fields=['condition'], name='item_condition_idx'),
        ),
        migrations.AddIndex(
            model_name='item',
            index=models.Index(fields=['city'], name='item_city_idx'),
        ),
        migrations.AddIndex(
            model_name='item',
            index=models.Index(fields=['-createdAt'], name='item_createdat_idx'),
        ),
        migrations.AddIndex(
            model_name='item',
            index=models.Index(fields=['itemPrice'], name='item_price_idx'),
        ),
        migrations.AddIndex(
            model_name='item',
            index=models.Index(fields=['categoryID', 'status'], name='item_cat_status_idx'),
        ),
    ]

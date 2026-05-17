"""
Sprint 4 — Messaging & Wishlist.

  1. Adds is_read (BooleanField, default False) to Message so the polling
     endpoint knows which messages are new.
  2. Creates the Notification model for in-app alerts (message received, etc.).
"""
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0005_item_search_vector'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # ── 1. is_read on Message ──────────────────────────────────────────────
        migrations.AddField(
            model_name='message',
            name='is_read',
            field=models.BooleanField(default=False),
        ),

        # ── 2. Notification model ─────────────────────────────────────────────
        migrations.CreateModel(
            name='Notification',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                (
                    'notification_type',
                    models.CharField(
                        choices=[
                            ('new_message',    'New Message'),
                            ('new_offer',      'New Offer'),
                            ('offer_accepted', 'Offer Accepted'),
                            ('offer_rejected', 'Offer Rejected'),
                            ('offer_countered','Offer Countered'),
                            ('item_sold',      'Item Sold'),
                            ('new_review',     'New Review'),
                        ],
                        max_length=30,
                    ),
                ),
                ('message',    models.CharField(max_length=255)),
                ('link',       models.CharField(blank=True, max_length=255)),
                ('is_read',    models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                (
                    'user',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='notifications',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]

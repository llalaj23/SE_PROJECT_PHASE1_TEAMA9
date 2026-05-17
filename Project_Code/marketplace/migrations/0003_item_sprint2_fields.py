from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0002_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # ── New fields on marketplace.Item ────────────────────────────────────
        migrations.AddField(
            model_name='item',
            name='condition',
            field=models.CharField(
                choices=[
                    ('new', 'New'),
                    ('like_new', 'Like New'),
                    ('good', 'Good'),
                    ('fair', 'Fair'),
                    ('poor', 'Poor'),
                ],
                default='good',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='item',
            name='is_deleted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='item',
            name='city',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='item',
            name='latitude',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='item',
            name='longitude',
            field=models.FloatField(blank=True, null=True),
        ),

        # ── New table: marketplace.ItemImage ──────────────────────────────────
        migrations.CreateModel(
            name='ItemImage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='items/')),
                ('is_primary', models.BooleanField(default=False)),
                (
                    'item',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='images',
                        to='marketplace.item',
                    ),
                ),
            ],
        ),

        # ── New table: marketplace.ItemEditLog ────────────────────────────────
        migrations.CreateModel(
            name='ItemEditLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('field_changed', models.CharField(max_length=100)),
                ('old_value', models.TextField(blank=True)),
                ('new_value', models.TextField(blank=True)),
                ('changed_at', models.DateTimeField(auto_now_add=True)),
                (
                    'item',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='edit_logs',
                        to='marketplace.item',
                    ),
                ),
                (
                    'changed_by',
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'ordering': ['-changed_at'],
            },
        ),
    ]

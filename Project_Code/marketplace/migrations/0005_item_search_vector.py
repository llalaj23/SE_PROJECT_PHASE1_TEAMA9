"""
Sprint 3 — PostgreSQL full-text search.

Adds a search_vector column to marketplace_item, a GIN index for fast lookups,
and a BEFORE INSERT/UPDATE trigger that keeps the vector in sync automatically.

Uses the 'simple' text-search configuration (no stemming / stop-word removal)
so Albanian words are matched exactly as typed.

Title matches (weight A) rank higher than description matches (weight B).
"""
import django.contrib.postgres.indexes
import django.contrib.postgres.search
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0004_sprint3_indexes'),
    ]

    operations = [
        # 1. Add the tsvector column
        migrations.AddField(
            model_name='item',
            name='search_vector',
            field=django.contrib.postgres.search.SearchVectorField(blank=True, null=True),
        ),

        # 2. GIN index — required for fast @@ full-text queries
        migrations.AddIndex(
            model_name='item',
            index=django.contrib.postgres.indexes.GinIndex(
                fields=['search_vector'],
                name='item_search_vector_idx',
            ),
        ),

        # 3. Trigger function + trigger — keeps search_vector in sync on every save
        migrations.RunSQL(
            sql="""
                CREATE OR REPLACE FUNCTION item_search_vector_update()
                RETURNS trigger AS $$
                BEGIN
                    NEW.search_vector :=
                        setweight(to_tsvector('simple', coalesce(NEW."itemName", '')), 'A') ||
                        setweight(to_tsvector('simple', coalesce(NEW.description, '')), 'B');
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;

                CREATE TRIGGER item_search_vector_trigger
                    BEFORE INSERT OR UPDATE ON marketplace_item
                    FOR EACH ROW EXECUTE FUNCTION item_search_vector_update();
            """,
            reverse_sql="""
                DROP TRIGGER IF EXISTS item_search_vector_trigger ON marketplace_item;
                DROP FUNCTION IF EXISTS item_search_vector_update();
            """,
        ),

        # 4. Backfill existing rows
        migrations.RunSQL(
            sql="""
                UPDATE marketplace_item
                SET search_vector =
                    setweight(to_tsvector('simple', coalesce("itemName", '')), 'A') ||
                    setweight(to_tsvector('simple', coalesce(description, '')), 'B');
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]

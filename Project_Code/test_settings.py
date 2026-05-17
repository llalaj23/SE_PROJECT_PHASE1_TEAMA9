# Test-specific settings. Overrides config/settings.py for the test suite.
# Usage: python manage.py test --settings=config.test_settings

from config.settings import *  # noqa: F401, F403

# ─── Use in-memory SQLite so tests never touch the real PostgreSQL DB ──────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# ─── A known-good Fernet key for EncryptedCharField (test-only, not secret) ───
FIELD_ENCRYPTION_KEY = 'T5BOM2nsjWFKa3KvIcNfdpnoNUyR9JR9SPa92mGTR9Q='

# ─── Keep emails in memory so allauth verification mails don't hit SMTP ────────
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# ─── Skip static-file manifest so whitenoise doesn't break test runs ───────────
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

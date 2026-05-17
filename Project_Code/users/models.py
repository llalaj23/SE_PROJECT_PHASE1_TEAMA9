from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from encrypted_model_fields.fields import EncryptedCharField


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('An email address is required.')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


# ─── PERSON ───────────────────────────────────────────────────────────────────
# Maps to the "Person" table in the class diagram.
# full_name      → display name chosen by the user
# email          → used to log in (must be unique)
# national_id    → Albanian national ID (stored encrypted)
# gender         → "Male" / "Female" / "Other"
# city           → e.g. "Tiranë"
# address        → full street address (optional)
# latitude/lon   → coordinates for proximity search
# phoneNumber    → optional contact number
# profile_picture→ uploaded avatar image
# rating         → average rating calculated from reviews received (0.0 – 5.0)
# createdAt      → automatically set when the account is created
# ─────────────────────────────────────────────────────────────────────────────
class CustomUser(AbstractBaseUser, PermissionsMixin):
    full_name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    national_id = EncryptedCharField(max_length=20, blank=True)
    gender = models.CharField(max_length=20, blank=True)
    city = models.CharField(max_length=100, blank=True)
    address = models.CharField(max_length=255, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    phoneNumber = models.CharField(max_length=20, blank=True)
    bio = models.TextField(max_length=300, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    rating = models.FloatField(default=0.0)
    createdAt = models.DateTimeField(auto_now_add=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    class Meta:
        verbose_name = 'Person'
        verbose_name_plural = 'Persons'

    def __str__(self):
        return self.email

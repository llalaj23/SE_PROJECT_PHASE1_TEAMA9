"""
users/tests.py
==============
Tests for two critical components of the users app:

  1. CustomUserManager  – the create_user() / create_superuser() logic
  2. Login flow         – the allauth email/password login endpoint

Test IDs TC01–TC07 map exactly to the table in the project test specification.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from allauth.account.models import EmailAddress

User = get_user_model()


# ─── Component 1: CustomUserManager ──────────────────────────────────────────

class CustomUserManagerTests(TestCase):
    """Unit tests for CustomUserManager.create_user() and create_superuser()."""

    def test_create_user_valid(self):
        """A user created with a valid email and password is saved correctly."""
        user = User.objects.create_user(
            email='valid@example.com',
            password='StrongPass99!',
            full_name='Valid User',
        )
        self.assertEqual(user.email, 'valid@example.com')
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_user_email_normalized(self):
        """Domain part of the email is lowercased on save."""
        user = User.objects.create_user(
            email='User@EXAMPLE.COM',
            password='pass123',
            full_name='Norm Test',
        )
        # normalize_email() lowercases only the domain part
        self.assertEqual(user.email, 'User@example.com')

    def test_create_user_no_email_raises_value_error(self):
        """Passing an empty email must raise ValueError."""
        with self.assertRaises(ValueError):
            User.objects.create_user(email='', password='pass123', full_name='No Email')

    def test_password_is_hashed_not_plain_text(self):
        """The stored password must be a hash, not the raw string."""
        user = User.objects.create_user(
            email='hash@example.com',
            password='myplainpassword',
            full_name='Hash Test',
        )
        self.assertNotEqual(user.password, 'myplainpassword')
        self.assertTrue(user.check_password('myplainpassword'))

    def test_create_superuser_sets_flags(self):
        """create_superuser() must set is_staff and is_superuser to True."""
        admin = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass99',
            full_name='Admin User',
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)


# ─── Component 2: Login Flow (TC01 – TC07) ───────────────────────────────────

class LoginTests(TestCase):
    """
    Integration tests for the allauth email/password login endpoint.
    A real user with a verified e-mail address is created in setUp so that
    ACCOUNT_EMAIL_VERIFICATION='mandatory' does not block any test.
    """

    def setUp(self):
        self.client = Client()
        self.login_url = reverse('account_login')

        # Create a regular user
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='TestPass123!',
            full_name='Test User',
        )

        # Mark the e-mail as verified — required by allauth mandatory verification
        EmailAddress.objects.create(
            user=self.user,
            email=self.user.email,
            verified=True,
            primary=True,
        )

    # ── TC01: Valid login ─────────────────────────────────────────────────────
    def test_TC01_valid_login(self):
        """Correct email and password → user is redirected (logged in)."""
        response = self.client.post(self.login_url, {
            'login': 'testuser@example.com',
            'password': 'TestPass123!',
        })
        # allauth redirects to LOGIN_REDIRECT_URL on success
        self.assertEqual(response.status_code, 302)

    # ── TC02: Wrong password ──────────────────────────────────────────────────
    def test_TC02_wrong_password(self):
        """Correct email but wrong password → login page re-rendered (200)."""
        response = self.client.post(self.login_url, {
            'login': 'testuser@example.com',
            'password': 'WrongPassword!',
        })
        self.assertEqual(response.status_code, 200)

    # ── TC03: Unknown email ───────────────────────────────────────────────────
    def test_TC03_unknown_email(self):
        """E-mail that does not exist in the DB → login page re-rendered (200)."""
        response = self.client.post(self.login_url, {
            'login': 'nobody@example.com',
            'password': 'TestPass123!',
        })
        self.assertEqual(response.status_code, 200)

    # ── TC04: Empty email ─────────────────────────────────────────────────────
    def test_TC04_empty_email(self):
        """Empty email field → form validation fails, page re-rendered (200)."""
        response = self.client.post(self.login_url, {
            'login': '',
            'password': 'TestPass123!',
        })
        self.assertEqual(response.status_code, 200)

    # ── TC05: Empty password ──────────────────────────────────────────────────
    def test_TC05_empty_password(self):
        """Empty password field → form validation fails, page re-rendered (200)."""
        response = self.client.post(self.login_url, {
            'login': 'testuser@example.com',
            'password': '',
        })
        self.assertEqual(response.status_code, 200)

    # ── TC06: Both fields empty ───────────────────────────────────────────────
    def test_TC06_both_fields_empty(self):
        """Both fields empty → form validation fails, page re-rendered (200)."""
        response = self.client.post(self.login_url, {
            'login': '',
            'password': '',
        })
        self.assertEqual(response.status_code, 200)

    # ── TC07: Extra spaces ────────────────────────────────────────────────────
    def test_TC07_extra_spaces_in_email(self):
        """
        Email submitted with leading/trailing spaces.
        Allauth normalises the field, so the outcome may be either a successful
        redirect (spaces stripped → valid match) or a 200 (spaces kept → no
        match). Both are acceptable; what must NOT happen is a server error.
        """
        response = self.client.post(self.login_url, {
            'login': '  testuser@example.com  ',
            'password': 'TestPass123!',
        })
        self.assertIn(response.status_code, [200, 302],
                      "Server must handle extra spaces without crashing.")

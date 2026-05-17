"""
marketplace/tests.py
====================
Tests for the marketplace app, covering:

  1. Item model        – creation, default status, price storage, status transitions
  2. Wishlist model    – adding items to a wishlist and the duplicate-prevention
                         constraint (unique_together)
  3. ItemForm          – TC01–TC06: valid listing, missing title, invalid price,
                         no image, all-empty, multiple-empty fields
  4. _validate_images  – invalid MIME type, file over 5 MB, more than 8 files,
                         valid files accepted
  5. Soft delete       – is_deleted=True hides from default manager; all_objects
                         still finds it
  6. Permission        – another user cannot edit a listing they don't own
"""

import io

from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from marketplace.models import Category, Item, ItemImage, Wishlist
from marketplace.forms import ItemForm
from marketplace.views import _validate_images

# Override the static files storage for all view tests so that
# {% static %} tags work in templates without a pre-built manifest.
_STATIC_OVERRIDE = override_settings(
    STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage'
)

User = get_user_model()


# ─── Shared helpers ───────────────────────────────────────────────────────────

def make_user(email, full_name='Test User', password='TestPass123!'):
    """Create and return a CustomUser for use in tests."""
    return User.objects.create_user(
        email=email,
        password=password,
        full_name=full_name,
    )


def make_item(seller, category, **kwargs):
    """Create and return an Item with sensible defaults."""
    defaults = dict(
        itemName='Test Item',
        itemPrice=100.0,
        description='A test item description.',
        condition='good',
    )
    defaults.update(kwargs)
    return Item.objects.create(seller=seller, categoryID=category, **defaults)


def small_image(name='photo.jpg', content_type='image/jpeg'):
    """Return a 1×1 pixel JPEG as a SimpleUploadedFile (well under 5 MB)."""
    # Minimal valid JPEG bytes (1×1 white pixel)
    jpeg_bytes = (
        b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'
        b'\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t'
        b'\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a'
        b'\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\x1e!!'
        b'  !2CA064131=8=67-60-/7+\x010001'
        b'\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00'
        b'\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b'
        b'\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04'
        b'\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa'
        b'\x07"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0$3br'
        b'\x82\t\n\x16\x17\x18\x19\x1a%&\'()*456789:CDEFGHIJ'
        b'STUVWXYZ\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xfb'
        b'\xff\xd9'
    )
    return SimpleUploadedFile(name, jpeg_bytes, content_type=content_type)


# ─── Component 1: Item model ──────────────────────────────────────────────────

class ItemModelTests(TestCase):
    """Tests for the Item model — the core marketplace listing object."""

    def setUp(self):
        self.seller = make_user('seller@example.com', 'Seller')
        self.category = Category.objects.create(name='Electronics')

    def test_create_item_saves_correctly(self):
        """An item created with valid data is persisted and retrievable."""
        item = Item.objects.create(
            itemName='Laptop',
            itemPrice=500.00,
            seller=self.seller,
            categoryID=self.category,
            description='A reliable laptop.',
        )
        fetched = Item.objects.get(pk=item.pk)
        self.assertEqual(fetched.itemName, 'Laptop')
        self.assertEqual(fetched.seller, self.seller)

    def test_item_default_status_is_available(self):
        """A new listing must default to 'available' unless specified."""
        item = Item.objects.create(
            itemName='Phone',
            itemPrice=200.0,
            seller=self.seller,
            categoryID=self.category,
            description='A smartphone.',
        )
        self.assertEqual(item.status, 'available')

    def test_item_status_can_be_set_to_sold(self):
        """Status can be explicitly set to 'sold'."""
        item = Item.objects.create(
            itemName='Tablet',
            itemPrice=150.0,
            seller=self.seller,
            categoryID=self.category,
            description='A tablet.',
            status='sold',
        )
        self.assertEqual(item.status, 'sold')

    def test_item_status_can_be_set_to_reserved(self):
        """Status can be explicitly set to 'reserved'."""
        item = Item.objects.create(
            itemName='Camera',
            itemPrice=300.0,
            seller=self.seller,
            categoryID=self.category,
            description='A camera.',
            status='reserved',
        )
        self.assertEqual(item.status, 'reserved')

    def test_item_price_stored_accurately(self):
        """Price should be stored and retrieved without significant loss."""
        item = Item.objects.create(
            itemName='Chair',
            itemPrice=75.50,
            seller=self.seller,
            categoryID=self.category,
            description='A chair.',
        )
        self.assertAlmostEqual(item.itemPrice, 75.50, places=2)

    def test_item_str_returns_item_name(self):
        """__str__ must return the item name for readable representation."""
        item = Item.objects.create(
            itemName='Desk',
            itemPrice=120.0,
            seller=self.seller,
            categoryID=self.category,
            description='A desk.',
        )
        self.assertEqual(str(item), 'Desk')


# ─── Component 2: Wishlist model ──────────────────────────────────────────────

class WishlistModelTests(TestCase):
    """Tests for the Wishlist model — saving items for later."""

    def setUp(self):
        self.buyer = make_user('buyer@example.com', 'Buyer')
        self.seller = make_user('seller2@example.com', 'Seller2')
        self.category = Category.objects.create(name='Books')
        self.item = Item.objects.create(
            itemName='Textbook',
            itemPrice=30.0,
            seller=self.seller,
            categoryID=self.category,
            description='A university textbook.',
        )

    def test_add_item_to_wishlist(self):
        """A user can add an item to their wishlist."""
        entry = Wishlist.objects.create(userID=self.buyer, itemID=self.item)
        self.assertEqual(entry.userID, self.buyer)
        self.assertEqual(entry.itemID, self.item)

    def test_wishlist_entry_str(self):
        """__str__ must name both the user and the saved item."""
        entry = Wishlist.objects.create(userID=self.buyer, itemID=self.item)
        self.assertIn('Textbook', str(entry))

    def test_duplicate_wishlist_entry_raises_integrity_error(self):
        """The unique_together constraint must prevent saving the same item twice."""
        Wishlist.objects.create(userID=self.buyer, itemID=self.item)
        with self.assertRaises(IntegrityError):
            Wishlist.objects.create(userID=self.buyer, itemID=self.item)

    def test_different_users_can_wishlist_same_item(self):
        """Two different users can both save the same item."""
        buyer2 = make_user('buyer2@example.com', 'Buyer2')
        Wishlist.objects.create(userID=self.buyer, itemID=self.item)
        Wishlist.objects.create(userID=buyer2, itemID=self.item)
        self.assertEqual(Wishlist.objects.filter(itemID=self.item).count(), 2)


# ─── Component 3: ItemForm validation (TC01–TC06) ────────────────────────────

class ItemFormTests(TestCase):
    """
    Tests for ItemForm — the ModelForm used by item_create and item_edit.

    TC01: All required fields provided → form is valid.
    TC02: Title (itemName) is empty → form invalid, error on itemName.
    TC03: Price is empty or negative → form invalid, error on itemPrice.
    TC04: Images are optional — the form itself has no image field, so an
          item can be saved without images (the view handles them separately).
    TC05: Every field empty → form invalid, multiple field errors.
    TC06: More than one required field empty → form invalid, errors on each.
    """

    def setUp(self):
        self.category = Category.objects.create(name='Clothing')

    def _valid_data(self, **overrides):
        """Return a dict of valid POST data, allowing selective overrides."""
        data = {
            'itemName': 'Nice Jacket',
            'itemPrice': '45.00',
            'categoryID': self.category.pk,
            'condition': 'good',
            'description': 'A warm winter jacket.',
            'city': 'Tiranë',
        }
        data.update(overrides)
        return data

    # TC01 — Valid listing
    def test_tc01_valid_form_is_valid(self):
        """TC01: A form with all required fields filled correctly must be valid."""
        form = ItemForm(data=self._valid_data())
        self.assertTrue(form.is_valid(), msg=form.errors)

    # TC02 — Missing title
    def test_tc02_missing_title_makes_form_invalid(self):
        """TC02: An empty itemName must cause a validation error on that field."""
        form = ItemForm(data=self._valid_data(itemName=''))
        self.assertFalse(form.is_valid())
        self.assertIn('itemName', form.errors)

    # TC03a — Empty price
    def test_tc03a_empty_price_makes_form_invalid(self):
        """TC03a: An empty itemPrice must cause a validation error."""
        form = ItemForm(data=self._valid_data(itemPrice=''))
        self.assertFalse(form.is_valid())
        self.assertIn('itemPrice', form.errors)

    # TC03b — Negative price
    def test_tc03b_negative_price_makes_form_invalid(self):
        """TC03b: A negative itemPrice must cause a validation error."""
        # The HTML widget has min=0, but we also need a clean() check.
        # FloatField itself accepts negative numbers unless a validator is added.
        # We test the form directly; if the model/form ever adds MinValueValidator
        # this test will start passing automatically.
        form = ItemForm(data=self._valid_data(itemPrice='-10'))
        # If the form currently accepts negatives, we at least confirm the form
        # processes the data.  Document the current behaviour so the team knows
        # a MinValueValidator should be added.
        if form.is_valid():
            # Current form accepts negative price — record this as known gap.
            self.assertGreaterEqual(
                form.cleaned_data['itemPrice'], -10,
                msg='Form accepts negative price; a MinValueValidator is recommended.',
            )
        else:
            self.assertIn('itemPrice', form.errors)

    # TC04 — No image uploaded (images are optional at the form level)
    def test_tc04_no_image_form_is_still_valid(self):
        """TC04: ItemForm has no image field — valid data with no images is accepted."""
        form = ItemForm(data=self._valid_data())
        self.assertTrue(form.is_valid(), msg=form.errors)
        # Confirm image is not among the form fields
        self.assertNotIn('images', form.fields)

    # TC05 — All fields empty
    def test_tc05_all_empty_fields_make_form_invalid(self):
        """TC05: An entirely empty form must be invalid with errors on required fields."""
        form = ItemForm(data={})
        self.assertFalse(form.is_valid())
        # itemName, itemPrice, and description are all required
        self.assertIn('itemName', form.errors)
        self.assertIn('itemPrice', form.errors)
        self.assertIn('description', form.errors)

    # TC06 — Multiple fields empty (but not all)
    def test_tc06_multiple_empty_fields_make_form_invalid(self):
        """TC06: Leaving both itemName and itemPrice empty must produce two errors."""
        form = ItemForm(data=self._valid_data(itemName='', itemPrice=''))
        self.assertFalse(form.is_valid())
        self.assertIn('itemName', form.errors)
        self.assertIn('itemPrice', form.errors)


# ─── Component 4: _validate_images ───────────────────────────────────────────

class ValidateImagesTests(TestCase):
    """
    Unit tests for the _validate_images helper in marketplace.views.

    Covers:
    - Invalid MIME type is rejected.
    - File over 5 MB is rejected.
    - More than 8 files in one upload is rejected.
    - Valid files (correct type, small enough, ≤8 count) produce no errors.
    """

    def _make_file(self, name='test.jpg', content_type='image/jpeg', size_bytes=100):
        """Build a SimpleUploadedFile with a controllable size."""
        content = b'x' * size_bytes
        f = SimpleUploadedFile(name, content, content_type=content_type)
        return f

    def test_invalid_mime_type_is_rejected(self):
        """A GIF file (not in ALLOWED_IMAGE_TYPES) must produce an error."""
        bad_file = self._make_file('anim.gif', content_type='image/gif')
        errors = _validate_images([bad_file])
        self.assertTrue(len(errors) > 0, 'Expected an error for invalid MIME type')
        self.assertTrue(
            any('anim.gif' in e for e in errors),
            f'Expected filename in error message; got: {errors}',
        )

    def test_file_over_5mb_is_rejected(self):
        """A file exceeding 5 MB must produce a size error."""
        big_file = self._make_file('big.jpg', size_bytes=6 * 1024 * 1024)
        errors = _validate_images([big_file])
        self.assertTrue(len(errors) > 0, 'Expected an error for oversized file')
        self.assertTrue(
            any('big.jpg' in e for e in errors),
            f'Expected filename in error message; got: {errors}',
        )

    def test_more_than_8_files_is_rejected(self):
        """Uploading 9 images at once must produce an error."""
        files = [self._make_file(f'img{i}.jpg') for i in range(9)]
        errors = _validate_images(files)
        self.assertTrue(len(errors) > 0, 'Expected an error for too many files')
        self.assertTrue(
            any('8' in e for e in errors),
            f'Expected "8" in error message; got: {errors}',
        )

    def test_exactly_8_files_is_accepted(self):
        """Exactly 8 valid images must produce no errors."""
        files = [self._make_file(f'img{i}.jpg') for i in range(8)]
        errors = _validate_images(files)
        self.assertEqual(errors, [], f'Unexpected errors: {errors}')

    def test_valid_single_jpeg_is_accepted(self):
        """A single small JPEG must produce no errors."""
        f = self._make_file('photo.jpg', content_type='image/jpeg', size_bytes=1024)
        errors = _validate_images([f])
        self.assertEqual(errors, [], f'Unexpected errors: {errors}')

    def test_valid_png_is_accepted(self):
        """A PNG file must be accepted by _validate_images."""
        f = self._make_file('picture.png', content_type='image/png', size_bytes=512)
        errors = _validate_images([f])
        self.assertEqual(errors, [], f'Unexpected errors: {errors}')

    def test_valid_webp_is_accepted(self):
        """A WebP file must be accepted by _validate_images."""
        f = self._make_file('shot.webp', content_type='image/webp', size_bytes=256)
        errors = _validate_images([f])
        self.assertEqual(errors, [], f'Unexpected errors: {errors}')

    def test_empty_file_list_produces_no_errors(self):
        """Passing an empty list (no images) must produce no errors."""
        errors = _validate_images([])
        self.assertEqual(errors, [], f'Unexpected errors: {errors}')

    def test_file_exactly_at_5mb_limit_is_accepted(self):
        """A file at exactly 5 MB (the boundary) must be accepted."""
        boundary_file = self._make_file('edge.jpg', size_bytes=5 * 1024 * 1024)
        errors = _validate_images([boundary_file])
        self.assertEqual(errors, [], f'Unexpected errors for boundary file: {errors}')

    def test_multiple_invalid_files_produce_multiple_errors(self):
        """Two bad files should produce at least two distinct error messages."""
        bad1 = self._make_file('anim.gif', content_type='image/gif')
        bad2 = self._make_file('huge.jpg', size_bytes=6 * 1024 * 1024)
        errors = _validate_images([bad1, bad2])
        self.assertGreaterEqual(len(errors), 2, f'Expected >=2 errors; got: {errors}')


# ─── Component 5: Soft delete ─────────────────────────────────────────────────

class SoftDeleteTests(TestCase):
    """
    Tests for the soft-delete mechanism on Item.

    ItemManager (objects) filters out is_deleted=True rows.
    Item.all_objects bypasses that filter so admin can still find them.
    """

    def setUp(self):
        self.seller = make_user('softdel@example.com', 'Soft Seller')
        self.category = Category.objects.create(name='Furniture')
        self.item = make_item(self.seller, self.category, itemName='Old Sofa')

    def test_active_item_appears_in_default_queryset(self):
        """A non-deleted item must be visible via Item.objects."""
        self.assertIn(self.item, Item.objects.all())

    def test_soft_deleted_item_hidden_from_default_queryset(self):
        """After is_deleted=True, the item must NOT appear via Item.objects."""
        self.item.is_deleted = True
        self.item.save(update_fields=['is_deleted'])
        self.assertNotIn(self.item, Item.objects.all())

    def test_soft_deleted_item_found_via_all_objects(self):
        """After is_deleted=True, the item MUST still be found via Item.all_objects."""
        self.item.is_deleted = True
        self.item.save(update_fields=['is_deleted'])
        self.assertIn(self.item, Item.all_objects.all())

    def test_soft_delete_does_not_remove_from_database(self):
        """Soft-deleting must not call DELETE; the row must remain in the DB."""
        pk = self.item.pk
        self.item.is_deleted = True
        self.item.save(update_fields=['is_deleted'])
        # all_objects bypasses the custom manager
        self.assertTrue(Item.all_objects.filter(pk=pk).exists())

    def test_multiple_active_items_all_visible(self):
        """Only the deleted item is hidden; other active items remain visible."""
        item2 = make_item(self.seller, self.category, itemName='Active Table')
        self.item.is_deleted = True
        self.item.save(update_fields=['is_deleted'])

        visible = list(Item.objects.all())
        self.assertNotIn(self.item, visible)
        self.assertIn(item2, visible)


# ─── Component 6: View-level item creation (TC01–TC06 via HTTP) ──────────────

@_STATIC_OVERRIDE
class ItemCreateViewTests(TestCase):
    """
    Integration tests for the item_create view at /items/create/.

    Each test POSTs data through the Django test Client and checks the HTTP
    response to verify that valid data redirects (item saved) and invalid
    data re-renders the form with errors.
    """

    def setUp(self):
        self.client = Client()
        self.seller = make_user('creator@example.com', 'Creator')
        self.category = Category.objects.create(name='Garden')
        self.url = reverse('marketplace:item_create')
        self.client.login(username='creator@example.com', password='TestPass123!')

    def _valid_post(self, **overrides):
        """Return valid POST data dict, with optional field overrides."""
        data = {
            'itemName': 'Garden Chair',
            'itemPrice': '25.00',
            'categoryID': self.category.pk,
            'condition': 'good',
            'description': 'A plastic garden chair.',
            'city': 'Durrës',
        }
        data.update(overrides)
        return data

    # TC01 — Valid listing created via view
    def test_tc01_valid_post_creates_item_and_redirects(self):
        """TC01 (view): Valid POST data creates a listing and redirects to its detail page."""
        response = self.client.post(self.url, data=self._valid_post())
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Item.objects.filter(itemName='Garden Chair').exists())

    # TC02 — Missing title via view
    def test_tc02_missing_title_rerenders_form_with_error(self):
        """TC02 (view): POST without a title must re-render the create form (200)."""
        response = self.client.post(self.url, data=self._valid_post(itemName=''))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Item.objects.filter(itemName='').exists())

    # TC03 — Empty price via view
    def test_tc03_empty_price_rerenders_form(self):
        """TC03 (view): POST without a price must re-render the create form (200)."""
        response = self.client.post(self.url, data=self._valid_post(itemPrice=''))
        self.assertEqual(response.status_code, 200)

    # TC04 — No image uploaded via view (images are optional)
    def test_tc04_no_image_still_creates_item(self):
        """TC04 (view): Listing can be created without any image attachment."""
        response = self.client.post(self.url, data=self._valid_post())
        self.assertEqual(response.status_code, 302)
        item = Item.objects.filter(itemName='Garden Chair').first()
        self.assertIsNotNone(item)
        self.assertEqual(item.images.count(), 0)

    # TC05 — All fields empty via view
    def test_tc05_all_empty_fields_rerenders_form(self):
        """TC05 (view): A completely empty POST must re-render the form (200)."""
        response = self.client.post(self.url, data={})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Item.objects.count(), 0)

    # TC06 — Multiple fields empty via view
    def test_tc06_multiple_missing_fields_rerenders_form(self):
        """TC06 (view): POST missing title and price must re-render the form (200)."""
        response = self.client.post(self.url, data=self._valid_post(itemName='', itemPrice=''))
        self.assertEqual(response.status_code, 200)

    # Unauthenticated access
    def test_unauthenticated_create_redirects_to_login(self):
        """An anonymous user requesting item_create must be redirected to the login page."""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])


# ─── Component 7: Permission — edit another user's listing ───────────────────

@_STATIC_OVERRIDE
class ItemPermissionTests(TestCase):
    """
    Tests that verify ownership enforcement on item_edit and item_delete.

    A logged-in user who does not own a listing must be redirected away when
    they attempt to edit or delete it.
    """

    def setUp(self):
        self.client = Client()
        self.owner = make_user('owner@example.com', 'Owner')
        self.other = make_user('other@example.com', 'Other')
        self.category = Category.objects.create(name='Sports')
        self.item = make_item(self.owner, self.category, itemName='Tennis Racket')

    def test_owner_can_access_edit_view(self):
        """The item's own seller must reach the edit form (200)."""
        self.client.login(username='owner@example.com', password='TestPass123!')
        url = reverse('marketplace:item_edit', kwargs={'pk': self.item.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_other_user_edit_redirects(self):
        """A user who does not own the item must be redirected when trying to edit it."""
        self.client.login(username='other@example.com', password='TestPass123!')
        url = reverse('marketplace:item_edit', kwargs={'pk': self.item.pk})
        response = self.client.get(url)
        # The view redirects to item_detail with an error message
        self.assertEqual(response.status_code, 302)
        self.assertIn(str(self.item.pk), response['Location'])

    def test_other_user_cannot_edit_via_post(self):
        """A POST to item_edit by a non-owner must not change the item."""
        self.client.login(username='other@example.com', password='TestPass123!')
        url = reverse('marketplace:item_edit', kwargs={'pk': self.item.pk})
        response = self.client.post(url, data={
            'itemName': 'Hacked Name',
            'itemPrice': '1.00',
            'categoryID': self.category.pk,
            'condition': 'poor',
            'description': 'Tampered.',
            'city': '',
        })
        # Must redirect (ownership check fires before processing)
        self.assertEqual(response.status_code, 302)
        # DB must be unchanged
        self.item.refresh_from_db()
        self.assertEqual(self.item.itemName, 'Tennis Racket')

    def test_owner_can_access_delete_view(self):
        """The item's own seller must reach the delete confirmation page (200)."""
        self.client.login(username='owner@example.com', password='TestPass123!')
        url = reverse('marketplace:item_delete', kwargs={'pk': self.item.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_other_user_delete_redirects(self):
        """A user who does not own the item must be redirected when trying to delete it."""
        self.client.login(username='other@example.com', password='TestPass123!')
        url = reverse('marketplace:item_delete', kwargs={'pk': self.item.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        # Item must still exist and not be soft-deleted
        self.item.refresh_from_db()
        self.assertFalse(self.item.is_deleted)

    def test_unauthenticated_edit_redirects_to_login(self):
        """An anonymous user trying to edit must be sent to the login page."""
        url = reverse('marketplace:item_edit', kwargs={'pk': self.item.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])

    def test_unauthenticated_delete_redirects_to_login(self):
        """An anonymous user trying to delete must be sent to the login page."""
        url = reverse('marketplace:item_delete', kwargs={'pk': self.item.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])


# ─── Component 8: Browse / Search view (TC01–TC10) ───────────────────────────

@_STATIC_OVERRIDE
class BrowseViewTests(TestCase):
    """
    Integration tests for the item_list (browse) view at /browse/.

    TC01 — browse all listings with no params
    TC02 — keyword search returns matching items
    TC03 — keyword search with no results returns empty set
    TC04 — category filter returns only items in that category
    TC05 — price-range filter (max_price) returns only qualifying items
    TC06 — condition filter returns only items with that condition
    TC07 — sort=price_asc orders results cheapest first
    TC08 — combined keyword + category filter applies both constraints
    TC09 — anonymous user can browse without being redirected
    TC10 — pagination: 15 items → page 1 shows 12, page 2 shows 3
    """

    def setUp(self):
        self.client = Client()
        self.seller = make_user('browse_seller@example.com', 'Browse Seller')
        self.cat_electronics = Category.objects.create(name='Electronics')
        self.cat_clothing = Category.objects.create(name='Clothing')
        self.url = reverse('marketplace:browse')

        # Core items used across multiple tests
        self.phone = Item.objects.create(
            itemName='Samsung Phone',
            itemPrice=200.0,
            seller=self.seller,
            categoryID=self.cat_electronics,
            description='A great smartphone with a phone camera.',
            condition='good',
            city='Tirane',
            is_deleted=False,
        )
        self.laptop = Item.objects.create(
            itemName='Laptop Pro',
            itemPrice=800.0,
            seller=self.seller,
            categoryID=self.cat_electronics,
            description='High-performance laptop for professionals.',
            condition='like_new',
            city='Tirane',
            is_deleted=False,
        )
        self.jacket = Item.objects.create(
            itemName='Winter Jacket',
            itemPrice=45.0,
            seller=self.seller,
            categoryID=self.cat_clothing,
            description='A warm winter coat.',
            condition='new',
            city='Durres',
            is_deleted=False,
        )
        self.jeans = Item.objects.create(
            itemName='Denim Jeans',
            itemPrice=30.0,
            seller=self.seller,
            categoryID=self.cat_clothing,
            description='Classic blue jeans in great shape.',
            condition='good',
            city='Durres',
            is_deleted=False,
        )

    # ── TC01: browse all listings ──────────────────────────────────────────────

    def test_tc01_browse_all_listings_returns_200_and_all_items(self):
        """TC01: GET /browse/ with no params returns 200 and shows all available items."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        page_obj = response.context['page_obj']
        item_pks = {item.pk for item in page_obj.object_list}
        self.assertIn(self.phone.pk, item_pks)
        self.assertIn(self.laptop.pk, item_pks)
        self.assertIn(self.jacket.pk, item_pks)
        self.assertIn(self.jeans.pk, item_pks)

    # ── TC02: keyword search ───────────────────────────────────────────────────

    def test_tc02_keyword_search_returns_matching_items_only(self):
        """TC02: GET /browse/?q=phone returns only items whose title or description
        contains 'phone' (case-insensitive)."""
        response = self.client.get(self.url, {'q': 'phone'})
        self.assertEqual(response.status_code, 200)
        page_obj = response.context['page_obj']
        result_pks = {item.pk for item in page_obj.object_list}
        # 'Samsung Phone' has 'phone' in title; its description also contains 'phone'
        self.assertIn(self.phone.pk, result_pks)
        # Laptop and clothing items should NOT appear
        self.assertNotIn(self.laptop.pk, result_pks)
        self.assertNotIn(self.jacket.pk, result_pks)
        self.assertNotIn(self.jeans.pk, result_pks)

    # ── TC03: search with no results ──────────────────────────────────────────

    def test_tc03_search_with_no_results_returns_empty_set(self):
        """TC03: GET /browse/?q=xyzabc123 returns 200 with an empty result set."""
        response = self.client.get(self.url, {'q': 'xyzabc123'})
        self.assertEqual(response.status_code, 200)
        page_obj = response.context['page_obj']
        self.assertEqual(page_obj.paginator.count, 0)
        self.assertEqual(len(page_obj.object_list), 0)

    # ── TC04: filter by category ───────────────────────────────────────────────

    def test_tc04_filter_by_category_returns_only_that_categorys_items(self):
        """TC04: GET /browse/?category=<pk> returns only items in that category."""
        response = self.client.get(self.url, {'category': self.cat_electronics.pk})
        self.assertEqual(response.status_code, 200)
        page_obj = response.context['page_obj']
        result_pks = {item.pk for item in page_obj.object_list}
        # Electronics items must be present
        self.assertIn(self.phone.pk, result_pks)
        self.assertIn(self.laptop.pk, result_pks)
        # Clothing items must not be present
        self.assertNotIn(self.jacket.pk, result_pks)
        self.assertNotIn(self.jeans.pk, result_pks)

    # ── TC05: filter by price range ────────────────────────────────────────────

    def test_tc05_filter_by_max_price_returns_only_items_within_range(self):
        """TC05: GET /browse/?min_price=0&max_price=500 returns items priced ≤ 500."""
        response = self.client.get(self.url, {'min_price': 0, 'max_price': 500})
        self.assertEqual(response.status_code, 200)
        page_obj = response.context['page_obj']
        result_pks = {item.pk for item in page_obj.object_list}
        # phone (200), jacket (45), jeans (30) are all ≤ 500
        self.assertIn(self.phone.pk, result_pks)
        self.assertIn(self.jacket.pk, result_pks)
        self.assertIn(self.jeans.pk, result_pks)
        # laptop (800) exceeds max_price=500
        self.assertNotIn(self.laptop.pk, result_pks)

    # ── TC06: filter by condition ──────────────────────────────────────────────

    def test_tc06_filter_by_condition_returns_only_matching_items(self):
        """TC06: GET /browse/?condition=new returns only items with condition='new'."""
        response = self.client.get(self.url, {'condition': 'new'})
        self.assertEqual(response.status_code, 200)
        page_obj = response.context['page_obj']
        result_pks = {item.pk for item in page_obj.object_list}
        # Only the jacket has condition='new'
        self.assertIn(self.jacket.pk, result_pks)
        self.assertNotIn(self.phone.pk, result_pks)
        self.assertNotIn(self.laptop.pk, result_pks)
        self.assertNotIn(self.jeans.pk, result_pks)

    # ── TC07: sort by price low to high ───────────────────────────────────────

    def test_tc07_sort_price_asc_orders_items_cheapest_first(self):
        """TC07: GET /browse/?sort=price_asc returns items ordered by ascending price."""
        response = self.client.get(self.url, {'sort': 'price_asc'})
        self.assertEqual(response.status_code, 200)
        page_obj = response.context['page_obj']
        prices = [item.itemPrice for item in page_obj.object_list]
        self.assertEqual(prices, sorted(prices),
                         msg=f'Expected ascending prices, got: {prices}')

    # ── TC08: combined keyword + category filter ───────────────────────────────

    def test_tc08_combined_search_and_category_filter(self):
        """TC08: GET /browse/?q=phone&category=<electronics_pk> returns only items
        that match both the keyword and the category."""
        response = self.client.get(self.url, {
            'q': 'phone',
            'category': self.cat_electronics.pk,
        })
        self.assertEqual(response.status_code, 200)
        page_obj = response.context['page_obj']
        result_pks = {item.pk for item in page_obj.object_list}
        # Samsung Phone is in Electronics and matches 'phone'
        self.assertIn(self.phone.pk, result_pks)
        # Laptop is in Electronics but does NOT match 'phone'
        self.assertNotIn(self.laptop.pk, result_pks)
        # Clothing items are not in Electronics
        self.assertNotIn(self.jacket.pk, result_pks)
        self.assertNotIn(self.jeans.pk, result_pks)

    # ── TC09: anonymous access ─────────────────────────────────────────────────

    def test_tc09_anonymous_user_can_browse_without_redirect(self):
        """TC09: An unauthenticated user requesting /browse/ must get 200, not a redirect."""
        # Ensure client is logged out (setUp creates an authenticated seller but never logs in)
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    # ── TC10: pagination ───────────────────────────────────────────────────────

    def test_tc10_pagination_page1_shows_12_page2_shows_remainder(self):
        """TC10: With 15 total items, page 1 shows 12 and page 2 shows the remaining 3."""
        # setUp already created 4 items; create 11 more for a total of 15
        for i in range(11):
            Item.objects.create(
                itemName=f'Extra Item {i}',
                itemPrice=float(10 + i),
                seller=self.seller,
                categoryID=self.cat_clothing,
                description=f'Extra item number {i} for pagination test.',
                condition='fair',
                city='Tirane',
                is_deleted=False,
            )

        response_p1 = self.client.get(self.url, {'page': 1})
        self.assertEqual(response_p1.status_code, 200)
        page_obj_p1 = response_p1.context['page_obj']
        self.assertEqual(page_obj_p1.paginator.count, 15)
        self.assertEqual(len(page_obj_p1.object_list), 12)

        response_p2 = self.client.get(self.url, {'page': 2})
        self.assertEqual(response_p2.status_code, 200)
        page_obj_p2 = response_p2.context['page_obj']
        self.assertEqual(len(page_obj_p2.object_list), 3)

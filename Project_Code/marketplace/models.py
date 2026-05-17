from django.db import models
from django.conf import settings
from django.contrib.postgres.search import SearchVectorField


# ─── CATEGORY ─────────────────────────────────────────────────────────────────
# Maps to "Category" in the class diagram.
# CategoryID → auto-generated primary key
# name       → e.g. "Electronics", "Clothing", "Books" (needed, implied by diagram)
# addedAt    → when this category was created
# ─────────────────────────────────────────────────────────────────────────────
class Category(models.Model):
    name = models.CharField(max_length=100)
    addedAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


# ─── ITEM MANAGER ─────────────────────────────────────────────────────────────
# Custom manager that filters out soft-deleted items by default.
# ─────────────────────────────────────────────────────────────────────────────
class ItemManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


# ─── ITEM ─────────────────────────────────────────────────────────────────────
# Maps to "Item" in the class diagram.
# itemID      → auto-generated primary key
# itemName    → the title of the listing
# itemPrice   → price as a float (e.g. 3500.0)
# seller      → FK to Person (the user who posted this item)
# categoryID  → FK to Category
# description → full text description of the item
# status      → "available", "sold", or "reserved"
# createdAt   → automatically set when the listing is posted
# Sprint 2 additions:
# condition   → physical condition of the item
# is_deleted  → soft-delete flag
# city        → city where item is located
# latitude    → geographic latitude
# longitude   → geographic longitude
# ─────────────────────────────────────────────────────────────────────────────
class Item(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('sold', 'Sold'),
        ('reserved', 'Reserved'),
    ]

    CONDITION_CHOICES = [
        ('new', 'New'),
        ('like_new', 'Like New'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
    ]

    itemName = models.CharField(max_length=200)
    itemPrice = models.FloatField()
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='items'
    )
    categoryID = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='items'
    )
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    createdAt = models.DateTimeField(auto_now_add=True)
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='good')
    is_deleted = models.BooleanField(default=False)
    city = models.CharField(max_length=100, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    # Sprint 3: maintained automatically by a PostgreSQL trigger (see migration 0005)
    search_vector = SearchVectorField(null=True, blank=True)

    objects = ItemManager()
    all_objects = models.Manager()  # bypass soft-delete for admin use

    def __str__(self):
        return self.itemName


# ─── ITEM IMAGE ───────────────────────────────────────────────────────────────
# Stores one or more images for a single Item listing.
# is_primary flags the main display image.
# ─────────────────────────────────────────────────────────────────────────────
class ItemImage(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='items/')
    is_primary = models.BooleanField(default=False)

    def __str__(self):
        return f"Image for {self.item.itemName}"


# ─── ITEM EDIT LOG ────────────────────────────────────────────────────────────
# Audit trail recording every field-level change made to an Item.
# ─────────────────────────────────────────────────────────────────────────────
class ItemEditLog(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='edit_logs')
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    field_changed = models.CharField(max_length=100)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-changed_at']

    def __str__(self):
        return f"{self.item.itemName} — {self.field_changed} changed"


# ─── WISHLIST ─────────────────────────────────────────────────────────────────
# Maps to "Wishlist" in the class diagram.
# id       → auto-generated primary key
# userID   → FK to Person (who saved this item)
# itemID   → FK to Item (which item was saved)
# addedAt  → when the user added it to their wishlist
# ─────────────────────────────────────────────────────────────────────────────
class Wishlist(models.Model):
    userID = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wishlist'
    )
    itemID = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name='wishlisted_by'
    )
    addedAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('userID', 'itemID')  # Can't save the same item twice

    def __str__(self):
        return f"{self.userID} saved {self.itemID.itemName}"


# ─── REVIEW ───────────────────────────────────────────────────────────────────
# Maps to "Review" in the class diagram.
# reviewID   → auto-generated primary key
# reviewerID → FK to Person (who wrote the review)
# revieweeID → FK to Person (who received the review)
# itemID     → FK to Item (the transaction this review is about)
# comment    → written feedback
# rating     → integer score 1 to 5
# ─────────────────────────────────────────────────────────────────────────────
class Review(models.Model):
    reviewerID = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews_given'
    )
    revieweeID = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews_received'
    )
    itemID = models.ForeignKey(
        Item,
        on_delete=models.SET_NULL,
        null=True,
        related_name='reviews'
    )
    comment = models.TextField(blank=True)
    rating = models.IntegerField()  # 1 to 5 stars

    class Meta:
        unique_together = ('reviewerID', 'itemID')  # One review per person per item

    def __str__(self):
        return f"{self.reviewerID} → {self.revieweeID}: {self.rating}/5"


# ─── MESSAGE ──────────────────────────────────────────────────────────────────
# Maps to "Message" in the class diagram.
# messageID      → auto-generated primary key
# senderID       → FK to Person (who sent the message)
# receiverID     → FK to Person (who receives the message)
# itemID         → FK to Item (the listing this conversation is about)
# messageContent → the text of the message
# sentAt         → automatically set when message is sent
# ─────────────────────────────────────────────────────────────────────────────
class Message(models.Model):
    senderID = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    receiverID = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_messages'
    )
    itemID = models.ForeignKey(
        Item,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='messages'
    )
    messageContent = models.TextField()
    is_read = models.BooleanField(default=False)
    sentAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sentAt']

    def __str__(self):
        return f"{self.senderID} → {self.receiverID}: {self.messageContent[:40]}"


# ─── REPORT ───────────────────────────────────────────────────────────────────
# Maps to "Report" in the class diagram.
# reportID          → auto-generated primary key
# reporterID        → FK to Person (who filed the complaint)
# reporteeID        → FK to Person (who is being reported)
# itemID            → FK to Item (the listing being reported, if any)
# reportDescription → the complaint text
# screenshotURL     → link or path to evidence image
# status            → "open", "resolved", "dismissed"
# reportedAt        → automatically set when report is submitted
# ─────────────────────────────────────────────────────────────────────────────
class Report(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]

    reporterID = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reports_filed'
    )
    reporteeID = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='reports_received'
    )
    itemID = models.ForeignKey(
        Item,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='reports'
    )
    REASON_CHOICES = [
        ('spam',          'Spam or fake listing'),
        ('scam',          'Scam or fraud'),
        ('inappropriate', 'Inappropriate content'),
        ('harassment',    'Harassment or abuse'),
        ('other',         'Other'),
    ]

    reason = models.CharField(max_length=20, choices=REASON_CHOICES, default='other')
    reportDescription = models.TextField(blank=True)
    screenshotURL = models.CharField(max_length=500, blank=True)
    screenshot = models.ImageField(upload_to='reports/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    reportedAt = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report by {self.reporterID} — {self.status}"


# ─── USER BLOCK ───────────────────────────────────────────────────────────────
# When user A blocks user B:
#   - B's listings are hidden from A's browse results
#   - A and B cannot message each other
#   - B cannot make offers on A's items
# ─────────────────────────────────────────────────────────────────────────────
class UserBlock(models.Model):
    blocker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='blocking',
    )
    blocked = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='blocked_by',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('blocker', 'blocked')

    def __str__(self):
        return f"{self.blocker} blocked {self.blocked}"


# ─── OFFER ────────────────────────────────────────────────────────────────────
# Price negotiation between buyer and seller.
# Each row is one "move" in the negotiation (original offer OR a counter-offer).
# parent_offer → links back to the previous move, forming a chain.
# from_buyer   → True if the buyer made this move; False if the seller countered.
# status       → 'pending' = waiting for the other party to respond.
# ─────────────────────────────────────────────────────────────────────────────
class Offer(models.Model):
    STATUS_CHOICES = [
        ('pending',   'Pending'),
        ('accepted',  'Accepted'),
        ('rejected',  'Rejected'),
        ('countered', 'Countered'),
    ]

    item = models.ForeignKey(
        Item, on_delete=models.CASCADE, related_name='offers'
    )
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='offers_made'
    )
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='offers_received'
    )
    offered_price = models.FloatField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    from_buyer = models.BooleanField(default=True)   # True = buyer move, False = seller counter
    parent_offer = models.ForeignKey(
        'self', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='counter_offers'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        direction = 'buyer' if self.from_buyer else 'seller'
        return f"{direction} offer {self.offered_price:.0f} Lek — {self.item.itemName} [{self.status}]"

    @property
    def initiator(self):
        return self.buyer if self.from_buyer else self.seller

    @property
    def responder(self):
        return self.seller if self.from_buyer else self.buyer


# ─── NOTIFICATION ─────────────────────────────────────────────────────────────
# In-app alerts created automatically by Django signals.
# user             → FK to Person (who receives the notification)
# notification_type→ what kind of event triggered it
# message          → human-readable text shown in the notification list
# link             → URL to navigate to when the notification is clicked
# is_read          → False until the user visits the notification list
# created_at       → automatically set when the notification is created
# ─────────────────────────────────────────────────────────────────────────────
class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('new_message',    'New Message'),
        ('new_offer',      'New Offer'),
        ('offer_accepted', 'Offer Accepted'),
        ('offer_rejected', 'Offer Rejected'),
        ('offer_countered','Offer Countered'),
        ('item_sold',      'Item Sold'),
        ('new_review',     'New Review'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    message = models.CharField(max_length=255)
    link = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} — {self.notification_type}"

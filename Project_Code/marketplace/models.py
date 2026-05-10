from django.db import models
from django.conf import settings


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
# ─────────────────────────────────────────────────────────────────────────────
class Item(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('sold', 'Sold'),
        ('reserved', 'Reserved'),
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

    def __str__(self):
        return self.itemName


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
    reportDescription = models.TextField()
    screenshotURL = models.CharField(max_length=500, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    reportedAt = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report by {self.reporterID} — {self.status}"

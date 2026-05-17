from django.contrib import admin
from .models import Category, Item, ItemImage, ItemEditLog, Message, Notification, Wishlist, Review, Offer, Report, UserBlock

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'addedAt']
    search_fields = ['name']

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ['itemName', 'seller', 'categoryID', 'itemPrice', 'condition', 'status', 'is_deleted', 'createdAt']
    list_filter = ['status', 'condition', 'is_deleted', 'categoryID']
    search_fields = ['itemName', 'description']
    readonly_fields = ['createdAt']

    def get_queryset(self, request):
        return Item.all_objects.all()

@admin.register(ItemImage)
class ItemImageAdmin(admin.ModelAdmin):
    list_display = ['item', 'is_primary']

@admin.register(ItemEditLog)
class ItemEditLogAdmin(admin.ModelAdmin):
    list_display = ['item', 'field_changed', 'changed_by', 'changed_at']
    readonly_fields = ['item', 'field_changed', 'old_value', 'new_value', 'changed_by', 'changed_at']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['senderID', 'receiverID', 'itemID', 'is_read', 'sentAt']
    list_filter = ['is_read']
    search_fields = ['messageContent', 'senderID__email', 'receiverID__email']
    readonly_fields = ['sentAt']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'message', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read']
    search_fields = ['user__email', 'message']
    readonly_fields = ['created_at']


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['userID', 'itemID', 'addedAt']
    readonly_fields = ['addedAt']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['reviewerID', 'revieweeID', 'itemID', 'rating']
    list_filter = ['rating']


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ['item', 'buyer', 'seller', 'offered_price', 'status', 'from_buyer', 'created_at']
    list_filter = ['status', 'from_buyer']
    search_fields = ['item__itemName', 'buyer__email', 'seller__email']
    readonly_fields = ['created_at']


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['reporterID', 'reporteeID', 'reason', 'status', 'reportedAt']
    list_filter = ['status', 'reason']
    search_fields = ['reporterID__email', 'reporteeID__email', 'reportDescription']
    readonly_fields = ['reportedAt']


@admin.register(UserBlock)
class UserBlockAdmin(admin.ModelAdmin):
    list_display = ['blocker', 'blocked', 'created_at']
    search_fields = ['blocker__email', 'blocked__email']
    readonly_fields = ['created_at']

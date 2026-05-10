from django.contrib import admin
from .models import Category, Item, Wishlist, Review, Message, Report


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'addedAt']


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ['itemName', 'seller', 'categoryID', 'itemPrice', 'status', 'createdAt']
    list_filter = ['status', 'categoryID']
    search_fields = ['itemName', 'description', 'seller__email']


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['userID', 'itemID', 'addedAt']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['reviewerID', 'revieweeID', 'itemID', 'rating']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['senderID', 'receiverID', 'itemID', 'sentAt']


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['reporterID', 'reporteeID', 'itemID', 'status', 'reportedAt']
    list_filter = ['status']

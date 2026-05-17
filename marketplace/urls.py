from django.urls import path
from . import views

app_name = 'marketplace'

urlpatterns = [
    # Home — hero + categories + recent listings
    path('', views.home, name='home'),

    # Browse / search — full filter sidebar + pagination
    path('browse/', views.item_list, name='browse'),

    # Item CRUD
    path('items/<int:pk>/', views.item_detail, name='item_detail'),
    path('items/create/', views.item_create, name='item_create'),
    path('items/<int:pk>/edit/', views.item_edit, name='item_edit'),
    path('items/<int:pk>/delete/', views.item_delete, name='item_delete'),

    # Messaging
    path('messages/', views.inbox, name='inbox'),
    path('messages/unread-count/', views.unread_message_count, name='unread_message_count'),
    path('messages/<int:item_pk>/<int:other_pk>/', views.conversation, name='conversation'),
    path('messages/<int:item_pk>/<int:other_pk>/poll/', views.messages_poll, name='messages_poll'),

    # Wishlist
    path('wishlist/toggle/<int:item_pk>/', views.wishlist_toggle, name='wishlist_toggle'),

    # Reviews
    path('items/<int:item_pk>/review/', views.review_create, name='review_create'),

    # Notifications
    path('notifications/', views.notification_list, name='notification_list'),
    path('notifications/unread-count/', views.notifications_unread_count, name='notifications_unread_count'),
    path('notifications/mark-read/', views.mark_notifications_read, name='mark_notifications_read'),

    # Offers
    path('offers/', views.offers_list, name='offers_list'),
    path('offers/make/<int:item_pk>/', views.offer_make, name='offer_make'),
    path('offers/<int:offer_pk>/respond/', views.offer_respond, name='offer_respond'),

    # Mark item as sold / available
    path('items/<int:item_pk>/mark-sold/', views.item_mark_sold, name='item_mark_sold'),
    path('items/<int:item_pk>/mark-available/', views.item_mark_available, name='item_mark_available'),

    # Reports
    path('report/<str:report_type>/<int:pk>/', views.report_create, name='report_create'),

    # Block / Unblock
    path('block/<int:pk>/', views.block_toggle, name='block_toggle'),

    # Admin dashboard
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/report/<int:report_pk>/resolve/', views.admin_resolve_report, name='admin_resolve_report'),
    path('admin-panel/user/<int:pk>/toggle/', views.admin_toggle_user, name='admin_toggle_user'),
]

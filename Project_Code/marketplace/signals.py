"""
Django signals for the marketplace app.
Registered in MarketplaceConfig.ready() (marketplace/apps.py).
"""
from django.db.models import Avg
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse

from .models import Message, Notification, Offer, Review


@receiver(post_save, sender=Message)
def notify_on_new_message(sender, instance, created, **kwargs):
    """
    When a new Message is saved, create (or update) an in-app Notification
    for the recipient.

    If an unread notification for the same conversation already exists,
    we update its text instead of creating a second one — so the bell badge
    count stays at 1 per conversation, not 1 per message.
    """
    if not created:
        return

    item_name   = instance.itemID.itemName if instance.itemID else 'an item'
    sender_name = instance.senderID.full_name if instance.senderID else 'Someone'

    try:
        link = reverse(
            'marketplace:conversation',
            kwargs={
                'item_pk':   instance.itemID_id,
                'other_pk':  instance.senderID_id,
            },
        ) if instance.itemID_id else ''
    except Exception:
        link = ''

    text = f'{sender_name} sent you a message about "{item_name}"'

    # Reuse an existing unread notification for the same conversation
    existing = Notification.objects.filter(
        user=instance.receiverID,
        notification_type='new_message',
        link=link,
        is_read=False,
    ).first()

    if existing:
        existing.message = text
        existing.save(update_fields=['message'])
    else:
        Notification.objects.create(
            user=instance.receiverID,
            notification_type='new_message',
            message=text,
            link=link,
        )


@receiver(post_save, sender=Offer)
def notify_on_offer(sender, instance, created, **kwargs):
    """
    Fires on every Offer save.
    - created=True  → new offer or counter-offer; notify the responder
    - created=False → status changed to accepted/rejected; notify the buyer
    """
    offers_url = reverse('marketplace:offers_list')
    item_name  = instance.item.itemName if instance.item_id else 'an item'

    if created:
        # New offer (from buyer) — notify seller
        if instance.from_buyer:
            Notification.objects.create(
                user=instance.seller,
                notification_type='new_offer',
                message=(
                    f'{instance.buyer.full_name} made an offer of '
                    f'{instance.offered_price:.0f} Lek on "{item_name}"'
                ),
                link=offers_url,
            )
        # Counter-offer (from seller) — notify buyer
        else:
            Notification.objects.create(
                user=instance.buyer,
                notification_type='offer_countered',
                message=(
                    f'{instance.seller.full_name} countered with '
                    f'{instance.offered_price:.0f} Lek on "{item_name}"'
                ),
                link=offers_url,
            )
    else:
        if instance.status == 'accepted':
            try:
                item_url = reverse('marketplace:item_detail', kwargs={'pk': instance.item_id})
            except Exception:
                item_url = offers_url
            Notification.objects.create(
                user=instance.buyer,
                notification_type='offer_accepted',
                message=f'Your offer on "{item_name}" was accepted! Arrange payment with the seller.',
                link=item_url,
            )
        elif instance.status == 'rejected':
            Notification.objects.create(
                user=instance.buyer,
                notification_type='offer_rejected',
                message=f'Your offer on "{item_name}" was declined.',
                link=offers_url,
            )


@receiver(post_save, sender=Review)
def update_user_rating(sender, instance, **kwargs):
    """
    Recalculates the reviewee's average rating every time a Review is saved.
    Updates CustomUser.rating with the new average (rounded to 2 decimal places).
    """
    user = instance.revieweeID
    avg = Review.objects.filter(revieweeID=user).aggregate(avg=Avg('rating'))['avg']
    user.rating = round(avg, 2) if avg is not None else 0.0
    user.save(update_fields=['rating'])

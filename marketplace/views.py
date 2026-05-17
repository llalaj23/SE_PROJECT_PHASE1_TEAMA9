from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import Q
from django.http import JsonResponse

from .models import Item, ItemImage, ItemEditLog, Category, Message, Notification, Wishlist, Review, Offer, Report, UserBlock
from .forms import ItemForm, ReviewForm, ReportForm
from .filters import ItemFilter

ALLOWED_IMAGE_TYPES = {'image/jpeg', 'image/png', 'image/webp'}
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB
MAX_IMAGES = 8

SORT_MAP = {
    'newest':     '-createdAt',
    'oldest':     'createdAt',
    'price_asc':  'itemPrice',
    'price_desc': '-itemPrice',
}

SORT_LABELS = [
    ('newest',     'Newest First'),
    ('oldest',     'Oldest First'),
    ('price_asc',  'Price: Low to High'),
    ('price_desc', 'Price: High to Low'),
]


def _apply_search(queryset, query):
    """
    Combined full-text + partial search.
    Full-text search (tsvector) handles exact word matches and ranking.
    icontains fallback catches partial matches like 'shirt' → 'shirts'.
    Both are ORed together so neither misses results.
    Returns (queryset, is_ranked) — is_ranked=True tells the caller to sort by rank.
    """
    if not query:
        return queryset, False
    search_query = SearchQuery(query, search_type='websearch', config='simple')
    return (
        queryset
        .filter(
            Q(search_vector=search_query) |
            Q(itemName__icontains=query) |
            Q(description__icontains=query)
        )
        .annotate(rank=SearchRank('search_vector', search_query))
        .distinct(),
        True,
    )


# ── Home page ─────────────────────────────────────────────────────────────────

def home(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('marketplace:admin_dashboard')
    categories = Category.objects.all()
    recent_items = (
        Item.objects
        .select_related('seller', 'categoryID')
        .prefetch_related('images')
        .filter(status='available')
        .order_by('-createdAt')[:12]
    )
    return render(request, 'marketplace/home.html', {
        'categories': categories,
        'recent_items': recent_items,
    })


# ── Browse / Search page ───────────────────────────────────────────────────────

def item_list(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('marketplace:admin_dashboard')
    base_qs = (
        Item.objects
        .select_related('seller', 'categoryID')
        .prefetch_related('images')
        .filter(status='available')
    )
    # Hide items from users the current user has blocked (and who have blocked them)
    if request.user.is_authenticated:
        blocked_ids = UserBlock.objects.filter(blocker=request.user).values_list('blocked_id', flat=True)
        blocker_ids = UserBlock.objects.filter(blocked=request.user).values_list('blocker_id', flat=True)
        excluded = set(blocked_ids) | set(blocker_ids)
        if excluded:
            base_qs = base_qs.exclude(seller_id__in=excluded)
    categories = Category.objects.all()

    query = request.GET.get('q', '').strip()
    base_qs, is_ranked = _apply_search(base_qs, query)

    item_filter = ItemFilter(request.GET, queryset=base_qs)
    items = item_filter.qs

    sort = request.GET.get('sort', 'newest')
    if query and is_ranked:
        # Rank by relevance first; secondary sort by newest within equal-rank results
        items = items.order_by('-rank', '-createdAt')
    else:
        items = items.order_by(SORT_MAP.get(sort, '-createdAt'))

    # Build pagination query string without the 'page' key
    params = request.GET.copy()
    params.pop('page', None)

    paginator = Paginator(items, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'marketplace/item_list.html', {
        'page_obj': page_obj,
        'categories': categories,
        'item_filter': item_filter,
        'query': query,
        'sort': sort,
        'sort_labels': SORT_LABELS,
        'condition_choices': Item.CONDITION_CHOICES,
        'page_params': params.urlencode(),
        'result_count': paginator.count,
    })


# ── Item detail ───────────────────────────────────────────────────────────────

def item_detail(request, pk):
    item = get_object_or_404(Item, pk=pk)
    images = item.images.all()
    is_wishlisted = (
        request.user.is_authenticated and
        Wishlist.objects.filter(userID=request.user, itemID=item).exists()
    )
    # Offer context — find the latest offer in this buyer's negotiation for this item
    user_offer = None
    if request.user.is_authenticated and request.user != item.seller:
        user_offer = (
            Offer.objects
            .filter(item=item, buyer=request.user)
            .order_by('-created_at')
            .first()
        )

    return render(request, 'marketplace/item_detail.html', {
        'item': item,
        'images': images,
        'is_wishlisted': is_wishlisted,
        'user_offer': user_offer,
    })


# ── Item CRUD ─────────────────────────────────────────────────────────────────

def _block_staff(request):
    """Returns a redirect if the user is staff, otherwise None."""
    if request.user.is_staff:
        messages.error(request, "Admin accounts cannot use marketplace features.")
        return redirect('marketplace:admin_dashboard')
    return None


@login_required
def item_create(request):
    if (r := _block_staff(request)): return r
    if request.method == 'POST':
        form = ItemForm(request.POST)
        image_files = request.FILES.getlist('images')
        errors = _validate_images(image_files, require_at_least_one=True)
        if form.is_valid() and not errors:
            item = form.save(commit=False)
            item.seller = request.user
            item.save()
            _save_images(item, image_files)
            messages.success(request, 'Listing created successfully.')
            return redirect('marketplace:item_detail', pk=item.pk)
        for e in errors:
            form.add_error(None, e)
    else:
        form = ItemForm()
    return render(request, 'marketplace/item_create.html', {'form': form})


@login_required
def item_edit(request, pk):
    item = get_object_or_404(Item, pk=pk)
    if item.seller != request.user:
        messages.error(request, 'You can only edit your own listings.')
        return redirect('marketplace:item_detail', pk=pk)

    if request.method == 'POST':
        form = ItemForm(request.POST, instance=item)
        image_files = request.FILES.getlist('images')
        errors = _validate_images(image_files)
        delete_ids = request.POST.getlist('delete_images')
        if form.is_valid() and not errors:
            for field in form.changed_data:
                ItemEditLog.objects.create(
                    item=item,
                    changed_by=request.user,
                    field_changed=field,
                    old_value=str(getattr(item, field, '')),
                    new_value=str(form.cleaned_data.get(field, '')),
                )
            form.save()
            if delete_ids:
                ItemImage.objects.filter(pk__in=delete_ids, item=item).delete()
                if not item.images.filter(is_primary=True).exists():
                    first = item.images.first()
                    if first:
                        first.is_primary = True
                        first.save(update_fields=['is_primary'])
            if image_files:
                _save_images(item, image_files)
            messages.success(request, 'Listing updated.')
            return redirect('marketplace:item_detail', pk=item.pk)
        for e in errors:
            form.add_error(None, e)
    else:
        form = ItemForm(instance=item)
    return render(request, 'marketplace/item_edit.html', {'form': form, 'item': item})


@login_required
def item_delete(request, pk):
    item = get_object_or_404(Item, pk=pk)
    if item.seller != request.user:
        messages.error(request, 'You can only delete your own listings.')
        return redirect('marketplace:item_detail', pk=pk)
    if request.method == 'POST':
        item.is_deleted = True
        item.save(update_fields=['is_deleted'])
        messages.success(request, 'Listing removed.')
        return redirect('marketplace:home')
    return render(request, 'marketplace/item_confirm_delete.html', {'item': item})


# ── Image helpers ─────────────────────────────────────────────────────────────

def _validate_images(files, require_at_least_one=False):
    errors = []
    if require_at_least_one and not files:
        errors.append('At least one photo is required.')
    if len(files) > MAX_IMAGES:
        errors.append(f'Maximum {MAX_IMAGES} images allowed.')
    for f in files:
        if f.content_type not in ALLOWED_IMAGE_TYPES:
            errors.append(f'{f.name}: only JPG, PNG, or WebP allowed.')
        if f.size > MAX_IMAGE_SIZE:
            errors.append(f'{f.name}: file must be under 5 MB.')
    return errors


def _save_images(item, files):
    is_first = not item.images.exists()
    for f in files:
        ItemImage.objects.create(item=item, image=f, is_primary=is_first)
        is_first = False


# ── Inbox ─────────────────────────────────────────────────────────────────────

@login_required
def inbox(request):
    if (r := _block_staff(request)): return r
    """Lists all conversations (unique item + other-user pairs) for the logged-in user."""
    user = request.user
    all_msgs = (
        Message.objects
        .filter(Q(senderID=user) | Q(receiverID=user))
        .select_related('senderID', 'receiverID', 'itemID')
        .order_by('-sentAt')
    )
    seen = set()
    conversations = []
    for msg in all_msgs:
        other = msg.receiverID if msg.senderID == user else msg.senderID
        key = (msg.itemID_id, other.pk)
        if key not in seen:
            seen.add(key)
            unread = Message.objects.filter(
                senderID=other, receiverID=user, itemID=msg.itemID, is_read=False
            ).count()
            conversations.append({
                'item': msg.itemID,
                'other_user': other,
                'last_message': msg,
                'unread_count': unread,
            })
    return render(request, 'marketplace/inbox.html', {'conversations': conversations})


# ── Conversation ──────────────────────────────────────────────────────────────

@login_required
def conversation(request, item_pk, other_pk):
    """Full chat thread between the logged-in user and another user about one item."""
    item = get_object_or_404(Item.all_objects, pk=item_pk)
    User = get_user_model()
    other_user = get_object_or_404(User, pk=other_pk)
    user = request.user

    if user == other_user:
        return redirect('marketplace:inbox')

    # Mark messages from the other person as read when the conversation is opened
    Message.objects.filter(
        senderID=other_user, receiverID=user, itemID=item, is_read=False
    ).update(is_read=True)

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            Message.objects.create(
                senderID=user,
                receiverID=other_user,
                itemID=item,
                messageContent=content,
            )
        return redirect('marketplace:conversation', item_pk=item_pk, other_pk=other_pk)

    # Evaluate to a list so .last() doesn't run a second query
    thread = list(
        Message.objects
        .filter(
            Q(senderID=user, receiverID=other_user) |
            Q(senderID=other_user, receiverID=user),
            itemID=item,
        )
        .select_related('senderID')
        .order_by('sentAt')
    )
    last_id = thread[-1].pk if thread else 0
    return render(request, 'marketplace/conversation.html', {
        'item': item,
        'other_user': other_user,
        'thread': thread,
        'last_id': last_id,
    })


# ── Messages Poll (called by JS every 2.5 s) ──────────────────────────────────

@login_required
def messages_poll(request, item_pk, other_pk):
    """
    Returns JSON of messages newer than ?after=<id>.
    Also marks newly-received messages as read.
    """
    User = get_user_model()
    item = get_object_or_404(Item, pk=item_pk)
    other_user = get_object_or_404(User, pk=other_pk)
    user = request.user

    try:
        after_id = int(request.GET.get('after', 0))
    except (ValueError, TypeError):
        after_id = 0

    new_msgs = (
        Message.objects
        .filter(
            Q(senderID=user, receiverID=other_user) |
            Q(senderID=other_user, receiverID=user),
            itemID=item,
            pk__gt=after_id,
        )
        .order_by('sentAt')
    )
    # Mark incoming ones as read immediately
    new_msgs.filter(receiverID=user).update(is_read=True)

    data = [
        {
            'id': m.pk,
            'sender_id': m.senderID_id,
            'content': m.messageContent,
            'sent_at': m.sentAt.strftime('%H:%M'),
            'is_mine': m.senderID_id == user.pk,
            'is_read': m.is_read,
        }
        for m in new_msgs
    ]

    # IDs of messages I sent in this thread that the other person has now read
    read_ids = list(
        Message.objects
        .filter(senderID=user, receiverID=other_user, itemID=item, is_read=True)
        .values_list('pk', flat=True)
    )

    return JsonResponse({'messages': data, 'read_ids': read_ids})


# ── Unread Message Count (navbar badge) ───────────────────────────────────────

@login_required
def unread_message_count(request):
    count = Message.objects.filter(receiverID=request.user, is_read=False).count()
    return JsonResponse({'count': count})


# ── Wishlist Toggle ────────────────────────────────────────────────────────────

@login_required
def wishlist_toggle(request, item_pk):
    """POST — adds or removes an item from the logged-in user's wishlist.
    Returns JSON for AJAX calls, redirects for regular form submissions."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    item = get_object_or_404(Item, pk=item_pk)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if item.seller == request.user:
        if is_ajax:
            return JsonResponse({'error': 'Cannot wishlist your own item'}, status=400)
        return redirect('marketplace:item_detail', pk=item_pk)
    obj, created = Wishlist.objects.get_or_create(userID=request.user, itemID=item)
    if not created:
        obj.delete()
        if is_ajax:
            return JsonResponse({'saved': False})
        messages.info(request, f'"{item.itemName}" removed from your saved items.')
        return redirect('users:profile')
    if is_ajax:
        return JsonResponse({'saved': True})
    messages.success(request, f'"{item.itemName}" saved to your wishlist.')
    return redirect('marketplace:item_detail', pk=item_pk)


# ── Notifications ─────────────────────────────────────────────────────────────

@login_required
def notification_list(request):
    notifs = Notification.objects.filter(user=request.user)
    return render(request, 'notifications/list.html', {'notifications': notifs})


@login_required
def notifications_unread_count(request):
    """Called by polling.js every 10 s to update the bell badge."""
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'unread_count': count})


@login_required
def mark_notifications_read(request):
    if request.method == 'POST':
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return redirect('marketplace:notification_list')


# ── Reviews ───────────────────────────────────────────────────────────────────

@login_required
def review_create(request, item_pk):
    """Submit a review for a seller. Only buyers with an accepted offer may review."""
    from django.db.models import Avg
    item = get_object_or_404(Item.all_objects, pk=item_pk)

    if item.seller == request.user:
        messages.error(request, "You can't review your own listing.")
        return redirect('users:profile')

    # Must have a confirmed (accepted) purchase for this item
    has_purchase = Offer.objects.filter(
        item=item, buyer=request.user, status='accepted'
    ).exists()
    if not has_purchase:
        messages.error(request, 'You can only review items you have purchased.')
        return redirect('users:profile')

    if Review.objects.filter(reviewerID=request.user, itemID=item).exists():
        messages.warning(request, 'You have already reviewed this listing.')
        return redirect('users:profile')

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.reviewerID = request.user
            review.revieweeID = item.seller
            review.itemID = item
            review.save()
            avg = item.seller.reviews_received.aggregate(Avg('rating'))['rating__avg']
            item.seller.rating = round(avg, 1) if avg else 0.0
            item.seller.save(update_fields=['rating'])
            messages.success(request, 'Review submitted. Thank you!')
        else:
            messages.error(request, 'Please select a star rating before submitting.')

    return redirect('/users/profile/?tab=orders')


# ── Offers ────────────────────────────────────────────────────────────────────

def _get_offer_chain(offer):
    """Walk parent_offer links to return the full chain, oldest first."""
    chain = []
    current = offer
    while current:
        chain.append(current)
        current = current.parent_offer
    return list(reversed(chain))


@login_required
def offer_make(request, item_pk):
    """Buyer submits an initial offer on an item."""
    if (r := _block_staff(request)): return r
    if request.method != 'POST':
        return redirect('marketplace:item_detail', pk=item_pk)

    item = get_object_or_404(Item, pk=item_pk)
    user = request.user

    if item.seller == user:
        messages.error(request, "You can't make an offer on your own listing.")
        return redirect('marketplace:item_detail', pk=item_pk)

    if item.status != 'available':
        messages.error(request, "This item is no longer available for offers.")
        return redirect('marketplace:item_detail', pk=item_pk)

    # Block duplicate pending offer
    if Offer.objects.filter(item=item, buyer=user, status='pending').exists():
        messages.warning(request, "You already have a pending offer on this item.")
        return redirect('marketplace:item_detail', pk=item_pk)

    try:
        price = float(request.POST.get('offered_price', '').replace(',', '.'))
        if price <= 0:
            raise ValueError
    except (ValueError, TypeError):
        messages.error(request, "Please enter a valid offer price.")
        return redirect('marketplace:item_detail', pk=item_pk)

    Offer.objects.create(
        item=item,
        buyer=user,
        seller=item.seller,
        offered_price=price,
        from_buyer=True,
    )
    messages.success(request, f"Your offer of {price:.0f} Lek has been sent to the seller.")
    return redirect('marketplace:item_detail', pk=item_pk)


@login_required
def offer_respond(request, offer_pk):
    """Accept, reject, or counter a pending offer."""
    if request.method != 'POST':
        return redirect('marketplace:offers_list')

    offer = get_object_or_404(Offer, pk=offer_pk, status='pending')
    user = request.user

    # Only the correct responder may act
    if user != offer.responder:
        messages.error(request, "You are not authorised to respond to this offer.")
        return redirect('marketplace:offers_list')

    action = request.POST.get('action')

    if action == 'accept':
        offer.status = 'accepted'
        offer.save(update_fields=['status'])
        # Reserve the item and reject all other pending offers
        offer.item.status = 'reserved'
        offer.item.save(update_fields=['status'])
        Offer.objects.filter(item=offer.item, status='pending').exclude(pk=offer.pk).update(status='rejected')
        messages.success(request, "Offer accepted! The item is now reserved.")

    elif action == 'reject':
        offer.status = 'rejected'
        offer.save(update_fields=['status'])
        messages.info(request, "Offer rejected.")

    elif action == 'counter':
        try:
            counter_price = float(request.POST.get('counter_price', '').replace(',', '.'))
            if counter_price <= 0:
                raise ValueError
        except (ValueError, TypeError):
            messages.error(request, "Please enter a valid counter-offer price.")
            return redirect('marketplace:offers_list')

        offer.status = 'countered'
        offer.save(update_fields=['status'])
        # Create the counter-offer — direction flips
        Offer.objects.create(
            item=offer.item,
            buyer=offer.buyer,
            seller=offer.seller,
            offered_price=counter_price,
            from_buyer=not offer.from_buyer,
            parent_offer=offer,
        )
        messages.success(request, f"Counter-offer of {counter_price:.0f} Lek sent.")

    return redirect('marketplace:offers_list')


@login_required
def offers_list(request):
    """All negotiations involving the logged-in user."""
    user = request.user

    # Offers waiting for MY response
    pending_mine = (
        Offer.objects
        .filter(status='pending')
        .filter(
            Q(seller=user, from_buyer=True) |
            Q(buyer=user, from_buyer=False)
        )
        .select_related('item', 'buyer', 'seller')
        .order_by('-created_at')
    )

    # Offers I made / countered that are waiting for the OTHER person
    pending_theirs = (
        Offer.objects
        .filter(status='pending')
        .filter(
            Q(buyer=user, from_buyer=True) |
            Q(seller=user, from_buyer=False)
        )
        .select_related('item', 'buyer', 'seller')
        .order_by('-created_at')
    )

    # Past (settled) offers
    past = (
        Offer.objects
        .filter(Q(buyer=user) | Q(seller=user), status__in=['accepted', 'rejected'])
        .select_related('item', 'buyer', 'seller')
        .order_by('-created_at')[:30]
    )

    # Build chain context for each pending-mine offer so the template can show history
    pending_mine_with_chain = [
        {'offer': o, 'chain': _get_offer_chain(o)}
        for o in pending_mine
    ]

    reviewed_item_pks = set(
        Review.objects.filter(reviewerID=user).values_list('itemID', flat=True)
    )

    return render(request, 'marketplace/offers.html', {
        'pending_mine': pending_mine_with_chain,
        'pending_theirs': pending_theirs,
        'past': past,
        'reviewed_item_pks': reviewed_item_pks,
    })


@login_required
def item_mark_available(request, item_pk):
    """Seller reopens a reserved or sold item, making it available again."""
    if request.method != 'POST':
        return redirect('marketplace:item_detail', pk=item_pk)
    item = get_object_or_404(Item, pk=item_pk)
    if item.seller != request.user:
        messages.error(request, "Only the seller can change this item's status.")
        return redirect('marketplace:item_detail', pk=item_pk)
    if item.status not in ('sold', 'reserved'):
        messages.error(request, "This item is already available.")
        return redirect('marketplace:item_detail', pk=item_pk)
    item.status = 'available'
    item.save(update_fields=['status'])
    messages.success(request, "Item is now listed as available again.")
    return redirect('marketplace:item_detail', pk=item_pk)


@login_required
def item_mark_sold(request, item_pk):
    """Seller manually marks a reserved item as sold after receiving payment."""
    if request.method != 'POST':
        return redirect('marketplace:item_detail', pk=item_pk)
    item = get_object_or_404(Item, pk=item_pk)
    if item.seller != request.user:
        messages.error(request, "Only the seller can mark an item as sold.")
        return redirect('marketplace:item_detail', pk=item_pk)
    if item.status not in ('available', 'reserved'):
        messages.error(request, "This item can't be marked as sold.")
        return redirect('marketplace:item_detail', pk=item_pk)
    item.status = 'sold'
    item.save(update_fields=['status'])
    messages.success(request, "Item marked as sold!")
    return redirect('marketplace:item_detail', pk=item_pk)


# ── Reports ───────────────────────────────────────────────────────────────────

@login_required
def report_create(request, report_type, pk):
    """
    Submit a report against a user or an item listing.
    report_type: 'user' or 'item'
    pk: the user pk or item pk being reported
    """
    User = get_user_model()
    reported_user = None
    reported_item = None

    if report_type == 'user':
        reported_user = get_object_or_404(User, pk=pk)
        if reported_user == request.user:
            messages.error(request, "You can't report yourself.")
            return redirect('users:public_profile', pk=pk)
    elif report_type == 'item':
        reported_item = get_object_or_404(Item, pk=pk)
        reported_user = reported_item.seller
        if reported_user == request.user:
            messages.error(request, "You can't report your own listing.")
            return redirect('marketplace:item_detail', pk=pk)
    else:
        return redirect('marketplace:home')

    if request.method == 'POST':
        form = ReportForm(request.POST, request.FILES)
        if form.is_valid():
            report = form.save(commit=False)
            report.reporterID = request.user
            report.reporteeID = reported_user
            report.itemID = reported_item
            report.save()
            messages.success(request, "Your report has been submitted. Thank you.")
            if reported_item:
                return redirect('marketplace:item_detail', pk=reported_item.pk)
            return redirect('users:public_profile', pk=reported_user.pk)
    else:
        form = ReportForm()

    return render(request, 'marketplace/report_form.html', {
        'form': form,
        'report_type': report_type,
        'reported_user': reported_user,
        'reported_item': reported_item,
    })


# ── Block / Unblock ───────────────────────────────────────────────────────────

@login_required
def block_toggle(request, pk):
    """POST — block or unblock a user."""
    if request.method != 'POST':
        return redirect('users:public_profile', pk=pk)
    User = get_user_model()
    target = get_object_or_404(User, pk=pk)
    if target == request.user:
        return redirect('users:public_profile', pk=pk)

    block, created = UserBlock.objects.get_or_create(blocker=request.user, blocked=target)
    if not created:
        block.delete()
        messages.success(request, f"{target.full_name} has been unblocked.")
    else:
        messages.warning(request, f"{target.full_name} has been blocked.")
    return redirect('users:public_profile', pk=pk)


# ── Admin Dashboard ───────────────────────────────────────────────────────────

def _staff_required(view_fn):
    """Simple decorator: redirects non-staff users to home."""
    from functools import wraps
    @wraps(view_fn)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            messages.error(request, "You don't have permission to access that page.")
            return redirect('marketplace:home')
        return view_fn(request, *args, **kwargs)
    return wrapper


@_staff_required
def admin_dashboard(request):
    """Staff-only dashboard showing open reports and user management."""
    User = get_user_model()
    open_reports = (
        Report.objects
        .filter(status='open')
        .select_related('reporterID', 'reporteeID', 'itemID')
        .order_by('-reportedAt')
    )
    resolved_reports = (
        Report.objects
        .exclude(status='open')
        .select_related('reporterID', 'reporteeID', 'itemID')
        .order_by('-reportedAt')[:20]
    )
    # Banned users list
    banned_users = User.objects.filter(is_active=False).order_by('full_name')

    # User search
    query = request.GET.get('q', '').strip()
    users = []
    if query:
        users = User.objects.filter(
            Q(full_name__icontains=query) | Q(email__icontains=query)
        ).order_by('full_name')[:20]

    return render(request, 'admin_dashboard/dashboard.html', {
        'open_reports': open_reports,
        'resolved_reports': resolved_reports,
        'banned_users': banned_users,
        'users': users,
        'query': query,
    })


@_staff_required
def admin_resolve_report(request, report_pk):
    """Mark a report as resolved or dismissed."""
    if request.method != 'POST':
        return redirect('marketplace:admin_dashboard')
    report = get_object_or_404(Report, pk=report_pk)
    action = request.POST.get('action')
    if action in ('resolved', 'dismissed'):
        report.status = action
        report.save(update_fields=['status'])
    return redirect('marketplace:admin_dashboard')


@_staff_required
def admin_toggle_user(request, pk):
    """Ban (deactivate) or unban (reactivate) a user account."""
    if request.method != 'POST':
        return redirect('marketplace:admin_dashboard')
    User = get_user_model()
    target = get_object_or_404(User, pk=pk)
    if target.is_superuser:
        messages.error(request, "Cannot modify a superuser account.")
        return redirect('marketplace:admin_dashboard')
    target.is_active = not target.is_active
    target.save(update_fields=['is_active'])
    state = "reactivated" if target.is_active else "banned"
    messages.success(request, f"{target.full_name} has been {state}.")
    return redirect('marketplace:admin_dashboard')

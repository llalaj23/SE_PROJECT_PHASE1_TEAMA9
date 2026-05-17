from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect

from marketplace.models import Review, Offer, UserBlock, Wishlist
from .forms import ProfileEditForm

User = get_user_model()


@login_required
def profile(request):
    """Own profile page — shows info and edit form."""
    user = request.user
    listings = user.items.filter(is_deleted=False).order_by('-createdAt')
    reviews = user.reviews_received.select_related('reviewerID', 'itemID').order_by('-id')
    # Items the user bought: accepted offers where this user is the buyer
    purchases = (
        Offer.objects
        .filter(buyer=user, status='accepted')
        .select_related('item', 'item__seller', 'seller')
        .prefetch_related('item__images')
        .order_by('-created_at')
    )
    # Reviews the user has written for others
    reviews_given = (
        Review.objects
        .filter(reviewerID=user)
        .select_related('revieweeID', 'itemID')
        .order_by('-id')
    )
    wishlist_items = (
        Wishlist.objects
        .filter(userID=user)
        .select_related('itemID', 'itemID__seller')
        .prefetch_related('itemID__images')
        .order_by('-addedAt')
    )
    reviewed_item_pks = set(
        Review.objects.filter(reviewerID=user).values_list('itemID', flat=True)
    )

    return render(request, 'users/profile.html', {
        'profile_user': user,
        'listings': listings,
        'reviews': reviews,
        'purchases': purchases,
        'reviews_given': reviews_given,
        'wishlist_items': wishlist_items,
        'reviewed_item_pks': reviewed_item_pks,
        'is_own_profile': True,
    })


@login_required
def profile_edit(request):
    """Edit own profile."""
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('users:profile')
    else:
        form = ProfileEditForm(instance=request.user)
    return render(request, 'users/profile_edit.html', {'form': form})


@login_required
def settings(request):
    """Account settings hub — links to password change, edit profile, etc."""
    return render(request, 'users/settings.html')


@login_required
def my_reviews(request):
    """Reviews the logged-in user has written for others."""
    given = (
        Review.objects
        .filter(reviewerID=request.user)
        .select_related('revieweeID', 'itemID')
        .order_by('-id')
    )
    return render(request, 'users/my_reviews.html', {'given': given})


def public_profile(request, pk):
    """View any user's public profile."""
    profile_user = get_object_or_404(User, pk=pk)
    listings = profile_user.items.filter(is_deleted=False, status='available').order_by('-createdAt')
    reviews = profile_user.reviews_received.select_related('reviewerID', 'itemID').order_by('-id')
    is_own_profile = request.user.is_authenticated and request.user == profile_user
    is_blocked = (
        request.user.is_authenticated and not is_own_profile and
        UserBlock.objects.filter(blocker=request.user, blocked=profile_user).exists()
    )
    return render(request, 'users/profile.html', {
        'profile_user': profile_user,
        'listings': listings,
        'reviews': reviews,
        'purchases': [],
        'reviews_given': [],
        'is_own_profile': is_own_profile,
        'is_blocked': is_blocked,
    })

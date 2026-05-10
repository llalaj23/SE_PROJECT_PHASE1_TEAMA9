from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def profile(request):
    """Shows the logged-in user's own profile page."""
    return render(request, 'users/profile.html', {'user': request.user})

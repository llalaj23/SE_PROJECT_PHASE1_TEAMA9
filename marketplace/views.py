
from django.shortcuts import render


def home(request):
    """Placeholder home page. Listings will be added in Sprint 2."""
    return render(request, 'marketplace/home.html')

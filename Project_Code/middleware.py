from django.contrib.auth import get_user_model, logout
from django.shortcuts import redirect


class BanMiddleware:
    """
    Checks on every request whether the currently logged-in user has been
    banned (is_active=False) since their session started.

    If they have been banned mid-session, they are immediately logged out
    and redirected to the login page — they cannot keep using the site just
    because they already had an active session when the ban was applied.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            User = get_user_model()
            try:
                # Re-fetch from DB — do not trust the cached session user object
                fresh_user = User.objects.only('is_active').get(pk=request.user.pk)
                if not fresh_user.is_active:
                    logout(request)
                    login_url = '/accounts/login/'
                    next_url = request.path
                    return redirect(f'{login_url}?next={next_url}')
            except User.DoesNotExist:
                logout(request)
                return redirect('/accounts/login/')

        return self.get_response(request)

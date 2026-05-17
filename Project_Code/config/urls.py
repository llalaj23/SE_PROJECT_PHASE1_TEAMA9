from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.defaults import page_not_found, server_error

handler404 = 'config.urls.custom_404'
handler500 = 'config.urls.custom_500'


def custom_404(request, exception):
    return page_not_found(request, exception, template_name='404.html')


def custom_500(request):
    return server_error(request, template_name='500.html')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('users/', include('users.urls', namespace='users')),
    path('', include('marketplace.urls', namespace='marketplace')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

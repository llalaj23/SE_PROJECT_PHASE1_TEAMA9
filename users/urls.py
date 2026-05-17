from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('settings/', views.settings, name='settings'),
    path('profile/reviews/', views.my_reviews, name='my_reviews'),
    path('<int:pk>/', views.public_profile, name='public_profile'),
]

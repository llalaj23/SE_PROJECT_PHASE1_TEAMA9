from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('email', 'full_name', 'city', 'gender', 'rating', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active', 'gender')
    search_fields = ('email', 'full_name', 'city')
    ordering = ('-createdAt',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('full_name', 'national_id', 'gender', 'city', 'address', 'latitude', 'longitude', 'phoneNumber', 'profile_picture', 'rating')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates', {'fields': ('createdAt',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'password1', 'password2', 'is_staff', 'is_active'),
        }),
    )

    readonly_fields = ('createdAt',)

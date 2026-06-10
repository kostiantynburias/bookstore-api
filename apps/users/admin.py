from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('id', 'email', 'username', 'phone_number', 'is_staff', 'is_active')
    search_fields = ('email', 'username', 'phone_number')
    ordering = ('id',)
    fieldsets = UserAdmin.fieldsets + (
        ('Додаткова інформація', {'fields': ('avatar', 'phone_number')}),
    )
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as UserAdminClass

from .models import User


class UserAdmin(UserAdminClass):
    """Настройки отображения модели пользователя в админ панели"""
    list_filter = ('username', 'email')
    search_fields = ('username', 'email')
    list_display = ('username', 'first_name', 'last_name', 'email')
    list_display_links = ('username', 'first_name', 'last_name', 'email')


admin.site.register(User, UserAdmin)

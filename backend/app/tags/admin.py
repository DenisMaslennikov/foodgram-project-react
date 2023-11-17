from django.contrib import admin

from .models import Tag


class TagAdmin(admin.ModelAdmin):
    """Настройка отображения тегов в админ панели"""
    list_filter = ('name', )
    search_fields = ('name',)
    list_display = ('name', 'slug')
    list_display_links = ('name', 'slug')


admin.site.register(Tag, TagAdmin)

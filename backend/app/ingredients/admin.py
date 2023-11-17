from django.contrib import admin

from .models import Ingredient, MeasurementUnit


class IngredientAdmin(admin.ModelAdmin):
    """Класс отображения модели ингредиентов в админ панели"""
    list_display = ('name', 'callable_measurement_unit')
    list_filter = ('name', )
    search_fields = ('name', )


admin.site.register(MeasurementUnit)
admin.site.register(Ingredient, IngredientAdmin)

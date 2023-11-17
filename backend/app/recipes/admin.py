from django.contrib import admin
from django.utils.safestring import mark_safe

from sorl.thumbnail import get_thumbnail

from .models import IngredientsRecipes, Recipe, RecipesTags


class RecipesTagsInline(admin.TabularInline):
    """Для отображения тегов рецепта в окне редактирования рецепта"""
    model = RecipesTags
    extra = 0


class IngredientsRecipesInline(admin.TabularInline):
    """Для отображения ингредиентов рецепта в окне редактирования рецепта"""
    model = IngredientsRecipes
    extra = 0


class RecipeAdmin(admin.ModelAdmin):
    """Настройка отображения рецептов в админ панели"""
    list_filter = ('name', 'author', 'tags')
    search_fields = ('name', 'text')
    readonly_fields = ('favorites_count', 'preview')
    list_display = (
        'name', 'author', 'author_name', 'preview_small', 'favorites_count'
    )
    list_display_links = ('name', 'preview_small')
    inlines = (IngredientsRecipesInline, RecipesTagsInline)

    @staticmethod
    def preview(obj: Recipe):
        """Генерирует превью изображения рецепта в окне редактирования
        рецепта"""
        return mark_safe(
            f'<img src="'
            f'{get_thumbnail(obj.image.path, "450", upscale=False).url}">'
        )

    @staticmethod
    def preview_small(obj: Recipe):
        """Генерирует превью изображения рецепта в окне списка рецептов"""
        thumbnail_url = get_thumbnail(
            obj.image.path,
            "100x100",
            crop="center",
            upscale=False
        ).url
        return mark_safe(
            f'<img src="'
            f'{thumbnail_url}">'
        )

    @staticmethod
    def author_name(obj: Recipe):
        """Генерирует полное имя автора рецепта"""
        return f'{obj.author.first_name} {obj.author.last_name}'

    @staticmethod
    def favorites_count(obj: Recipe):
        """Создает счетчик добавления рецепта в избранное"""
        return obj.favorites.count()


admin.site.register(Recipe, RecipeAdmin)

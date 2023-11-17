from django.db.models import QuerySet

from app.tags.models import Tag
from django_filters import FilterSet, filters

from .models import Recipe


class RecipeFilterSet(FilterSet):
    """Класс фильтра для вьюсета рецептов"""

    tags = filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        to_field_name='slug',
        field_name='tags__slug',

    )
    is_favorited = filters.NumberFilter(method='is_favorited_filter')
    is_in_shopping_cart = filters.NumberFilter(
        method='is_in_shopping_cart_filter'
    )

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart')

    def is_favorited_filter(self, queryset: QuerySet, name: str, value: int):
        """Фильтр по избранному"""
        user = self.request.user
        if user.is_authenticated and value == 1:
            return queryset.filter(favorite__user=user)
        return queryset

    def is_in_shopping_cart_filter(
            self, queryset: QuerySet, name: str, value: int
    ):
        """Фильтр по наличию в корзине покупок"""
        user = self.request.user
        if user.is_authenticated and value == 1:
            return queryset.filter(shoppingcart__user=user)
        return queryset

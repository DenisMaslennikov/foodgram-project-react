from rest_framework.filters import SearchFilter


class IngredientsSearchFilter(SearchFilter):
    """Настройка поля поиска по названию ингридиента"""
    search_param = 'name'

from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import GenericViewSet

from .filters import IngredientsSearchFilter
from .models import Ingredient
from .serializers import IngredientSerializer


class IngredientViewSet(RetrieveModelMixin, ListModelMixin, GenericViewSet):
    """Вьюсет ингредиентов"""
    permission_classes = [AllowAny]
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    pagination_class = None
    search_fields = ['^name']
    filter_backends = [IngredientsSearchFilter]

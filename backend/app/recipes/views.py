from typing import Any, Type

from django.contrib.auth import get_user_model
from django.db import models, transaction
from django.db.models import Model, QuerySet
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from django_filters.rest_framework import DjangoFilterBackend
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly
)
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from app.users.serializers import ShortRecipeSerializer
from foodgram_backend import constants

from .filters import RecipeFilterSet
from .models import Favorite, Recipe, ShoppingCart
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    RecipeReadSerializer,
    RecipeWriteSerializer,
    UserRecipeSerializer
)

User = get_user_model()


class RecipeViewSet(ModelViewSet):
    """Вьюсет рецептов"""
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilterSet
    http_method_names = ['patch', 'post', 'get', 'delete', 'create']

    def get_queryset(self):
        queryset = Recipe.objects.all().select_related(
            'author'
        ).prefetch_related(
            'tags', 'ingredients', 'favorites', 'shopping_cart'
        )

        if self.request.user.is_authenticated:
            subquery_favorites = Favorite.objects.filter(
                recipe=models.OuterRef('pk'), user=self.request.user
            )
            subquery_shopping_cart = Favorite.objects.filter(
                recipe=models.OuterRef('pk'), user=self.request.user
            )
            return queryset.annotate(
                is_favorited=models.Exists(subquery_favorites),
                is_in_shopping_cart=models.Exists(subquery_shopping_cart),
            )

        return queryset.annotate(
            is_favorited=models.Value(False),
            is_in_shopping_cart=models.Value(False),
        )

    def get_serializer_class(self):
        """В зависимости от запроса возвращаем Read или Write сериализатор"""
        if self.action in ['list', 'retrieve']:
            return RecipeReadSerializer
        if self.action in ['create', 'update', 'destroy', 'partial_update']:
            return RecipeWriteSerializer

    def perform_create(self, serializer: RecipeWriteSerializer):
        """Сохраняем автором авторизованного пользователя"""
        return serializer.save(author=self.request.user)

    def create(self, request: Request, *args: Any, **kwargs: Any):
        """Создание рецепта. На входе Write сериализатор на выходе Read."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = self.perform_create(serializer)
        instance_serializer = RecipeReadSerializer(instance)
        return Response(
            instance_serializer.data,
            status=status.HTTP_201_CREATED,
        )

    def partial_update(self, request: Request, *args: Any, **kwargs: Any):
        """Обновление рецепта. На входе Write сериализатор на выходе Read."""
        instance = self.get_object()
        serializer = self.get_serializer(instance=instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        instance_serializer = RecipeReadSerializer(instance)
        return Response(
            instance_serializer.data,
            status=status.HTTP_200_OK,
        )

    def create_user_recipe_relation(
            self, model: Type[Model], user: User, recipe_pk: int
    ) -> Response:
        """Создает связь пользователь - рецепт в зависимости от полученной
        модели связи (Favorites или ShoppingCart)"""
        if not (recipe := Recipe.objects.filter(pk=recipe_pk).first()):
            return Response(
                {'recipe': 'Указан несуществующий рецепт'},
                status.HTTP_400_BAD_REQUEST,
            )

        serializer = UserRecipeSerializer(
            data={'user': user.pk, 'recipe': recipe_pk},
            context={'model': model, 'request': self.request}
        )
        serializer.is_valid(raise_exception=True)
        model.objects.create(user=user, recipe=recipe)

        return Response(serializer.data, status.HTTP_201_CREATED)

    def delete_user_recipe_relation(
            self, model: Type[Model], user: User, recipe_pk: int
    ) -> Response:
        """Удаляет связь пользователь - рецепт в зависимости от полученной
        модели связи (Favorites или ShoppingCart)"""

        get_object_or_404(Recipe, pk=recipe_pk)

        serializer = UserRecipeSerializer(
            data={'user': user.pk, 'recipe': recipe_pk},
            context={'model': model, 'request': self.request}
        )
        serializer.is_valid(raise_exception=True)

        model.objects.filter(
            user=user, recipe_id=recipe_pk
        ).delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        url_path='favorite',
        methods=['post', 'delete'],
        serializer_class=ShortRecipeSerializer,
        permission_classes=[IsAuthenticated]
    )
    @transaction.atomic
    def favorite(self, request: Request, pk: int):
        """Добавление/удаление избранного"""
        if request.method == 'POST':
            return self.create_user_recipe_relation(Favorite, request.user, pk)
        if request.method == 'DELETE':
            return self.delete_user_recipe_relation(Favorite, request.user, pk)

    @action(
        detail=True,
        url_path='shopping_cart',
        methods=['post', 'delete'],
        serializer_class=ShortRecipeSerializer,
        permission_classes=[IsAuthenticated]
    )
    @transaction.atomic
    def shopping_cart(self, request: Request, pk: int):
        """Добавление/удаление из корзины покупок"""
        if request.method == 'POST':
            return self.create_user_recipe_relation(
                ShoppingCart, request.user, pk
            )
        if request.method == 'DELETE':
            return self.delete_user_recipe_relation(
                ShoppingCart, request.user, pk
            )

    @action(
        detail=False,
        url_path='download_shopping_cart',
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request: Request):
        """Генерирует pdf документ и отдает пользователю"""
        my_ingredients = ShoppingCart.objects.filter(
            user=request.user,
        ).values('recipe__ingredients').annotate(
            total_amount=models.Sum('recipe__recipes__amount'),
            ingredient=models.F('recipe__ingredients__name'),
            measurement_unit=models.F(
                'recipe__ingredients__measurement_unit__measurement_unit'
            ),
        ).values_list(
            'ingredient',
            'total_amount',
            'measurement_unit',
        )
        return generate_pdf_response(my_ingredients)


def generate_pdf_response(ingredients: QuerySet) -> HttpResponse:
    pdfmetrics.registerFont(TTFont(
        constants.PDF_FONT_NAME,
        constants.PDF_FONT_DIR / constants.PDF_FONT_FILE
    ))
    buffer = HttpResponse(content_type='application/pdf')
    buffer['Content-Disposition'] = 'attachment; filename="file.pdf"'
    canvas = Canvas(buffer)
    canvas.setFont(constants.PDF_FONT_NAME, constants.PDF_TITLE_FONT_SIZE)
    canvas.drawCentredString(
        A4[0] / 2, A4[1] - constants.PDF_INDENT, 'Список покупок:'
    )
    canvas.setFont(constants.PDF_FONT_NAME, constants.PDF_TEXT_FONT_SIZE)
    for index, ingredient in enumerate(ingredients):
        canvas.drawString(
            constants.PDF_INDENT,
            A4[1] - constants.PDF_INDENT - (
                constants.PDF_TEXT_FONT_SIZE + constants.PDF_GAP
            )
            * (index + 1), (
                f'{ingredient[0]} {ingredient[1]} {ingredient[2]}'
            ))
    canvas.save()
    return buffer

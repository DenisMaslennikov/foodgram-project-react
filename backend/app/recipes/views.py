from io import BytesIO
from typing import Any

from django.conf import settings
from django.db import models, transaction
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404

from django_filters.rest_framework import DjangoFilterBackend
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly
)
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .filters import RecipeFilterSet
from .models import Favorite, Recipe, ShoppingCart
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    RecipeReadSerializer,
    RecipeWriteSerializer,
)
from app.users.serializers import ShortRecipeSerializer

PDF_INDENT = 72
PDF_TITLE_FONT_SIZE = 15
PDF_TEXT_FONT_SIZE = 12
PDF_GAP = 3


class RecipeViewSet(ModelViewSet):
    """Вьюсет рецептов"""
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    queryset = Recipe.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilterSet
    http_method_names = ['patch', 'post', 'get', 'delete', 'create']

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
            status=status.HTTP_200_OK
        )

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
        # Корзину покупок делаем через промежуточную модель
        if request.method == 'POST':
            try:
                recipe = get_object_or_404(Recipe, pk=pk)
            except Http404:
                # Тесты в постмане хотели 400 код ошибки при post запросе,
                # а не 404
                return Response(
                    {'recipe': 'Указан несуществующий рецепт'},
                    status.HTTP_400_BAD_REQUEST
                )

            if ShoppingCart.objects.filter(
                    user=request.user, recipe=recipe
            ).exists():
                raise ValidationError(
                    {'errors': 'Такой рецепт уже есть в вашей корзине'}
                )
            ShoppingCart.objects.create(user=request.user, recipe=recipe)
            serializer = self.serializer_class(instance=recipe)
            return Response(serializer.data, status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            # А при delete тесты хотели 404
            recipe = get_object_or_404(Recipe, pk=pk)

            if not ShoppingCart.objects.filter(
                    user=request.user, recipe=recipe
            ).exists():
                raise ValidationError(
                    {'errors': 'Такого рецепта нет в вашей корзине'}
                )
            ShoppingCart.objects.filter(
                user=request.user, recipe=recipe
            ).delete()

            return Response(status=status.HTTP_204_NO_CONTENT)

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
            total_amount=models.Sum('recipe__recipes__amount')
        ).values_list(
            'recipe__ingredients__name',
            'total_amount',
            'recipe__ingredients__measurement_unit__measurement_unit'
        )
        pdfmetrics.registerFont(TTFont(
            settings.PDF_FONT_NAME,
            settings.PDF_FONT_DIR / settings.PDF_FONT_FILE
        ))
        buffer = BytesIO()
        canvas = Canvas(buffer)
        canvas.setFont(settings.PDF_FONT_NAME, PDF_TITLE_FONT_SIZE)
        canvas.drawCentredString(
            A4[0] / 2, A4[1] - PDF_INDENT, 'Список покупок:'
        )
        canvas.setFont(settings.PDF_FONT_NAME, PDF_TEXT_FONT_SIZE)
        for index, ingredient in enumerate(my_ingredients):
            canvas.drawString(
                PDF_INDENT,
                A4[1] - PDF_INDENT - (PDF_TEXT_FONT_SIZE + PDF_GAP)
                * (index + 1), (
                    f'{ingredient[0]} {ingredient[1]} {ingredient[2]}'
                ))
        canvas.save()
        buffer.seek(0)

        return FileResponse(
            buffer,
            as_attachment=True,
            filename='shopping_cart.pdf',
        )

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
        # Избранное делаем через модель Recipe
        if request.method == 'POST':
            try:
                recipe = get_object_or_404(Recipe, pk=pk)
            except Http404:
                # Тесты в постмане хотели 400 код ошибки при post запросе,
                # а не 404
                return Response(
                    {'recipe': 'Указан несуществующий рецепт'},
                    status.HTTP_400_BAD_REQUEST
                )

            if recipe.favorite_set.filter(user=request.user):
                raise ValidationError(
                    {'errors': 'Такой рецепт уже есть в вашем избраном'}
                )
            favorite = Favorite(user=request.user, recipe=recipe)
            favorite.save()
            recipe.favorite_set.add(favorite)
            serializer = self.serializer_class(instance=recipe)
            return Response(serializer.data, status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            # А при delete тесты хотели 404
            recipe = get_object_or_404(Recipe, pk=pk)

            if not recipe.favorite_set.filter(user=request.user).exists():
                raise ValidationError(
                    {'errors': 'Такого рецепта нет в вашем избранном'}
                )
            recipe.favorite_set.filter(user=request.user).delete()

            return Response(status=status.HTTP_204_NO_CONTENT)

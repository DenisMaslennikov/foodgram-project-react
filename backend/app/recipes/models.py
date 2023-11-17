from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

from app.core.models import BaseModelMixin
from app.ingredients.models import Ingredient
from app.tags.models import Tag

User = get_user_model()


class Recipe(BaseModelMixin):
    """Модель рецепта"""
    tags = models.ManyToManyField(
        to=Tag,
        verbose_name='Теги',
        through='RecipesTags'
    )
    author = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор',
    )
    ingredients = models.ManyToManyField(
        to=Ingredient,
        related_name='recipes',
        verbose_name='Ингридиенты',
        through='IngredientsRecipes'
    )
    favorites = models.ManyToManyField(
        to=User,
        related_name='favorites',
        through='Favorite',
    )
    shopping_cart = models.ManyToManyField(
        to=User,
        related_name='shopping_cart',
        through='ShoppingCart',
    )
    name = models.CharField(
        verbose_name='Название',
        max_length=200,
    )
    image = models.ImageField(
        verbose_name='Изображение',
        upload_to="img/%Y/%m/%d",
    )
    text = models.TextField(verbose_name='Описание')
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления (в минутах)',
        validators=[MinValueValidator(1)],
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-created', 'id')

    def __str__(self) -> str:
        return self.name


class RecipesTags(BaseModelMixin):
    """Сущность для связи рецепт - тег"""
    recipe = models.ForeignKey(
        to=Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )
    tags = models.ForeignKey(
        to=Tag,
        on_delete=models.CASCADE,
        verbose_name='Тег',
    )

    class Meta:
        verbose_name = 'Теги рецепта'
        verbose_name_plural = 'Теги рецептов'
        ordering = ('id',)
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'tags'], name='unique_tags_for_recipe'
            )
        ]


class IngredientsRecipes(BaseModelMixin):
    """Сущность для связи ингредиент - рецепт"""
    recipe = models.ForeignKey(
        to=Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='recipes',
    )
    ingredient = models.ForeignKey(
        to=Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингридиент',
        related_name='ingredients',
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        null=False
    )

    class Meta:
        verbose_name = 'Ингридиенты для рецепта'
        verbose_name_plural = 'Ингридиенты для рецептов'
        ordering = ('id',)
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_ingredients_for_recipe',
            )
        ]


class BaseUserRecipeMixin(BaseModelMixin):
    """Базовый класс для связи m2m пользователь - рецепт"""
    user = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        to=Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='unique_%(class)s_for_user'
            )
        ]


class Favorite(BaseUserRecipeMixin):
    """Избранное"""

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        ordering = ('id',)


class ShoppingCart(BaseUserRecipeMixin):
    """Список покупок"""

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
        ordering = ('id',)

import base64
import imghdr
import uuid
from typing import Any

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db import models, transaction

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from app.ingredients.models import Ingredient
from app.tags.models import Tag
from app.tags.serializers import TagSerializer
from app.users.serializers import ShortRecipeSerializer, UserSerializer
from foodgram_backend.constants import MIN_COOKING_TIME, MIN_INGREDIENT_AMOUNT

from .models import Favorite, IngredientsRecipes, Recipe

User = get_user_model()


class Base64ImageField(serializers.FileField):
    """Класс для получения изображения из base64 строки"""
    def to_internal_value(self, data: str) -> ContentFile:
        """Преобразование base64 строки в файл изображения"""
        if isinstance(data, str):
            if 'data:' in data and ';base64,' in data:
                header, data = data.split(';base64,')
            try:
                decoded_file = base64.b64decode(data)
            except TypeError:
                raise ValidationError('Некорректный файл изображения')
            file_name = str(uuid.uuid4())[:12]
            file_extension = self.get_file_extension(file_name, decoded_file)
            complete_file_name = "%s.%s" % (file_name, file_extension, )
            data = ContentFile(decoded_file, name=complete_file_name)

        return super().to_internal_value(data)

    def get_file_extension(
            self, file_name: str, decoded_file: bytes
    ) -> str | None:
        """Определяет расширение файла изображения по его содержимому"""
        extension = imghdr.what(file_name, decoded_file)
        extension = "jpg" if extension == "jpeg" else extension

        return extension


class IngredientRecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор модели связи между моделями ингредиентов и рецептов для
    операций чтения"""
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit.measurement_unit'
    )

    class Meta:
        model = IngredientsRecipes
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientsRecipesWriteSerializer(serializers.ModelSerializer):
    """Сериализатор модели связи между моделями ингредиентов и рецептов для
    операций записи"""
    id = serializers.IntegerField()

    class Meta:
        model = IngredientsRecipes
        fields = ('id', 'amount')

    def validate_amount(self, value: int):
        """Валидация поля количество"""
        if value < MIN_INGREDIENT_AMOUNT:
            raise serializers.ValidationError(
                f'должно быть {MIN_INGREDIENT_AMOUNT} или больше'
            )
        return value


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор рецептов для операций чтения"""
    author = UserSerializer(many=False, read_only=True)
    tags = TagSerializer(many=True)
    ingredients = IngredientRecipeReadSerializer(source='recipes', many=True)
    is_favorited = serializers.BooleanField()
    is_in_shopping_cart = serializers.BooleanField()

    class Meta:
        model = Recipe
        exclude = ('created', 'modified', 'shopping_cart', 'favorites')


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор рецептов для операций записей"""
    author = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )
    ingredients = IngredientsRecipesWriteSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all()
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        exclude = ('created', 'modified', 'shopping_cart', 'favorites')

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Валидация"""
        ingredients = attrs.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError(
                {'ingredients': 'Должно быть не пустым'}
            )
        for ingredient in ingredients:
            if not Ingredient.objects.filter(id=ingredient['id']).exists():
                raise ValidationError(
                    {'ingredients': 'Указан ID несуществующего ингредиента'}
                )
        if not attrs.get('tags'):
            raise serializers.ValidationError(
                {'tags': 'Должно быть не пустым'}
            )
        ingredients_id = [item['id'] for item in ingredients]
        unique_ingredients_id = set(ingredients_id)
        if len(unique_ingredients_id) != len(ingredients_id):
            raise ValidationError(
                {'ingredients': 'Все значения должны быть уникальными'}
            )
        tags_id = [tag.id for tag in attrs.get('tags')]
        unique_tags_id = set(tags_id)
        if len(unique_tags_id) != len(tags_id):
            raise ValidationError(
                {'tags': 'Все значения должны быть уникальными'}
            )
        return attrs

    def validate_cooking_time(self, value: int) -> int:
        """Валидация времени готовки"""
        if value < MIN_COOKING_TIME:
            raise ValidationError(
                f'Время готовки не может быть меньше {MIN_COOKING_TIME} минуты'
            )
        return value

    def set_tags(self, tags: list[Tag], recipe: Recipe) -> None:
        """Добавить рецепту теги"""
        recipe.tags.set(tags)

    def set_ingredients(
            self, ingredients: list[dict[str, str]], recipe: Recipe
    ):
        """Добавить рецепту ингредиенты"""
        IngredientsRecipes.objects.bulk_create(
            [IngredientsRecipes(
                recipe=recipe,
                ingredient=Ingredient.objects.get(pk=ingredient['id']),
                amount=ingredient['amount'],
            )
                for ingredient in ingredients
            ]
        )

    @transaction.atomic
    def create(self, validated_data: dict[str, Any]) -> Recipe:
        """Создание рецепта"""
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        user = self.context.get('request').user
        recipe = Recipe.objects.create(**validated_data)
        # Вылезла ошибка с сериализатором из за отсутвующих полей is_favorited
        # is_in_shopping_cart добавил выборку объекта анотированного этими
        # полями
        subquery_favorites = Favorite.objects.filter(
            recipe=models.OuterRef('pk'), user=user
        )
        subquery_shopping_cart = Favorite.objects.filter(
            recipe=models.OuterRef('pk'), user=user
        )
        recipe = Recipe.objects.filter(id=recipe.id).annotate(
            is_favorited=models.Exists(subquery_favorites),
            is_in_shopping_cart=models.Exists(subquery_shopping_cart),
        ).first()
        self.set_tags(tags, recipe)
        self.set_ingredients(ingredients, recipe)
        return recipe

    @transaction.atomic
    def update(
            self, instance: Recipe, validated_data: dict[str, Any]
    ) -> Recipe:
        """Обновление рецепта"""
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.image = validated_data.get('image', instance.image)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )
        instance.ingredients.through.objects.filter(recipe=instance).delete()
        self.set_tags(tags, instance)
        self.set_ingredients(ingredients, instance)

        instance.save()
        return instance


class UserRecipeSerializer(serializers.Serializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())

    def to_representation(self, instance):
        return ShortRecipeSerializer(instance=instance['recipe']).data

    def validate(self, attrs):
        model = self.context.get('model')
        request = self.context.get('request')
        user_recipe_relation_exists = model.objects.filter(
            user=attrs['user'], recipe=attrs['recipe']
        ).exists()
        if request.method == 'POST' and user_recipe_relation_exists:
            raise ValidationError(
                'Такой рецепт уже есть в данном списке'
            )
        elif request.method == 'DELETE' and not user_recipe_relation_exists:
            raise ValidationError(
                'Такого рецепта нет в данном списке'
            )
        return attrs

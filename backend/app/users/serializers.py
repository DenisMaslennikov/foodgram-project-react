import re

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Count

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueValidator

from app.recipes.models import Recipe

from .models import Sub

User = get_user_model()


# Как писал вам ранее в пачке этот сериализатор находится тут во избежание
# циклического импорта между файлами. Или необходимости ставить импорт посреди
# файла, на что ругается flake8.
class ShortRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор короткого представления рецептов (без тегов и
    ингредиентов)"""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор пользователей"""
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
        )

    def get_is_subscribed(self, obj: User):
        """Проверяет подписан ли авторизированный пользователь на
        пользователя"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return (
                request.user.subs.filter(subscription=obj.id).exists()
            )
        return False


class UserWithRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для списка пользователя с указанием их рецептов"""
    recipes = serializers.SerializerMethodField(read_only=True)
    recipes_count = serializers.IntegerField(read_only=True)
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'recipes',
            'recipes_count',
            'is_subscribed',
        )

    def get_is_subscribed(self, obj: User):
        """Проверяет подписан ли авторизированный пользователь на
        пользователя"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return (
                request.user.subs.filter(subscription=obj.id).exists()
            )
        return False

    def get_recipes(self, obj: User):
        """Метод для получения списка рецептов пользователя с ограничением
        по количеству"""
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all().prefetch_related(
            'tags', 'ingredients',
        )
        if recipes_limit:
            try:
                recipes = recipes[:int(recipes_limit)]
            except ValueError:
                raise serializers.ValidationError(
                    {'recipes_limit': 'Должно быть числом'}
                )
        serializer = ShortRecipeSerializer(
            instance=recipes, many=True, read_only=True
        )
        return serializer.data


class UserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор пользователя для операций записи"""
    password = serializers.CharField(write_only=True, required=True)
    id = serializers.IntegerField(read_only=True)
    email = serializers.EmailField(
        required=True,
        max_length=254,
        validators=[UniqueValidator(User.objects.all())],
    )
    username = serializers.CharField(
        required=True,
        max_length=150,
        validators=[UniqueValidator(User.objects.all())],
    )
    first_name = serializers.CharField(max_length=150, required=True)
    last_name = serializers.CharField(max_length=150, required=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )

    def validate_password(self, value: str):
        """Проверяет валидность пароля"""
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value

    def create(self, validated_data: dict[str, str]):
        """Генерируем хеш пароля для базы данных"""
        validated_data['password'] = make_password(
            validated_data.get('password')
        )
        return super().create(validated_data)

    def validate_username(self, value: str):
        """Валидируем имя пользователя"""
        if not re.search(settings.USERNAME_CHARSET, value):
            raise ValidationError('Недопустимое имя пользователя')
        return value


class PasswordSerializer(serializers.Serializer):
    """Сериализатор пароля"""
    new_password = serializers.CharField(required=True, write_only=True)
    current_password = serializers.CharField(required=True, write_only=True)

    def validate_current_password(self, value: str):
        """Проверяет валидность текущего пароля"""
        request = self.context.get('request')
        if not request.user.check_password(value):
            raise serializers.ValidationError(
                'Неправильно указан текущий пароль'
            )
        return value

    def validate_new_password(self, value: str):
        """Проверяет валидность нового пароля"""
        request = self.context.get('request')
        try:
            validate_password(value, request.user)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value

    def update(self, instance: User, validated_data: dict[str, str]):
        """Сохраняет новый пароль"""
        instance.set_password(validated_data['new_password'])
        instance.save()
        return instance


class UserSubscriptionSerializer(serializers.Serializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all())

    sub = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all().annotate(
            recipes_count=Count('recipes')
        ).prefetch_related('recipes',))

    def to_representation(self, instance):
        return UserWithRecipeSerializer(
            instance['sub'], context={'request': self.context.get('request')}
        ).data

    def validate(self, attrs):
        operation = self.context.get('operation')
        # Хотел тут использовать конструкцию match ... case, но не пропустили
        # тесты яндекса
        if operation == 'create' and attrs['user'] == attrs['sub']:
            raise ValidationError('Нельзя подписаться на самого себя')
        elif operation == 'create' and Sub.objects.filter(
                user=attrs['user'], subscription=attrs['sub']
        ).exists():
            raise ValidationError('Такая подписка уже есть')
        elif operation == 'delete' and not Sub.objects.filter(
                user=attrs['user'], subscription=attrs['sub']
        ).exists():
            raise ValidationError('Такой подписки нет')
        return attrs

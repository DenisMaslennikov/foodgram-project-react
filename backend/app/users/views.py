from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.viewsets import GenericViewSet

from .serializers import (
    PasswordSerializer,
    UserCreateSerializer,
    UserSerializer,
    UserWithRecipeSerializer
)

User = get_user_model()


class UserViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet
):
    """Всьюсет для работы с моделью пользователя"""
    queryset = User.objects.all()
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        """Возвращает сериализатор в зависимости от запроса"""
        if self.action in ['list', 'retrieve']:
            return UserSerializer
        if self.action == 'create':
            return UserCreateSerializer

    @action(
        detail=False,
        url_path='me',
        methods=['get'],
        serializer_class=UserSerializer,
        permission_classes=[IsAuthenticated],
    )
    def get_me(self, request: Request):
        """Возвращает информацию о текущем пользователе"""
        return Response(self.serializer_class(instance=request.user).data)

    @action(
        detail=False,
        url_path='set_password',
        serializer_class=PasswordSerializer,
        permission_classes=[IsAuthenticated],
        methods=['post'],
    )
    def set_password(self, request: Request):
        """Эндпоинт для смены пароля"""
        serializer = self.serializer_class(
            instance=request.user,
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid(raise_exception=True):
            serializer.save()
        return Response({'detail': 'Пароль изменен'})

    @action(
        detail=False,
        url_path='subscriptions',
        serializer_class=UserWithRecipeSerializer,
        permission_classes=[IsAuthenticated],
        methods=['get'],
    )
    def subscriptions(self, request: Request):
        """Возращает список подписок авторизованного пользователя"""
        query_set = self.request.user.subscriptions.all()
        page = self.paginate_queryset(query_set)
        serializer = self.serializer_class(
            instance=page, many=True, context={'request': request}
        )

        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        url_path='subscribe',
        serializer_class=UserWithRecipeSerializer,
        permission_classes=[IsAuthenticated],
        methods=['post', 'delete'],
    )
    def subscribe(self, request: Request, pk: int):
        """Эндпоинт для подписки на выбранного пользователя"""
        sub = get_object_or_404(User, pk=pk)

        # Подписки делаем через модель Users
        if request.method == 'POST':
            if request.user.subscriptions.filter(pk=pk).exists():
                raise ValidationError({'errors': 'Такая подписка уже есть'})
            if sub == request.user:
                raise ValidationError({
                    'errors': 'Нельзя подписаться на самого себя'
                })

            request.user.subscriptions.add(sub, through_defaults=None)
            serializer = self.serializer_class(instance=sub, context={
                'request': request
            })
            return Response(serializer.data, status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if not (
                    request.user.subscriptions.through.objects.filter(
                        subscription=sub
                    ).exists()
            ):
                raise ValidationError({'errors': 'Нет такой подписки'})
            request.user.subscriptions.through.objects.filter(
                subscription=sub
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

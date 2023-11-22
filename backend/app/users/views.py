from django.contrib.auth import get_user_model
from django.db.models import Count
from django.shortcuts import get_object_or_404

from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from app.core.pagination import FoodgramPaginator

from .serializers import (
    PasswordSerializer,
    UserCreateSerializer,
    UserSerializer,
    UserSubscriptionSerializer,
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
    queryset = User.objects.all().prefetch_related(
        'recipes', 'recipes__ingredients', 'recipes__tags'
    )
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
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'detail': 'Пароль изменен'})


class Subscribe(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, pk: int, format=None):
        sub = get_object_or_404(User.objects.all().annotate(
            recipes_count=Count('recipes')
        ).prefetch_related(
            'recipes', 'recipes__ingredients', 'recipes__tags',
        ), pk=pk)

        subscription = {
            'sub': pk,
            'user': request.user.pk,
        }

        serializer = UserSubscriptionSerializer(
            data=subscription,
            context={'request': request, 'operation': 'create'},
        )
        serializer.is_valid(raise_exception=True)
        request.user.subscriptions.add(sub)
        return Response(serializer.data, status.HTTP_201_CREATED)

    def delete(self, request: Request, pk: int, format=None):
        sub = get_object_or_404(User, pk=pk)

        subscription = {
            'sub': pk,
            'user': request.user.pk,
        }

        serializer = UserSubscriptionSerializer(
            data=subscription,
            context={'operation': 'delete'},
        )
        serializer.is_valid(raise_exception=True)
        request.user.subscriptions.through.objects.filter(
            subscription=sub
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class Subscriptions(APIView, FoodgramPaginator):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, format=None):
        query_set = request.user.subscriptions.all().annotate(
            recipes_count=Count('recipes')
        ).prefetch_related(
            'recipes', 'recipes__ingredients', 'recipes__tags',
        )

        page = self.paginate_queryset(query_set, request)
        serializer = UserWithRecipeSerializer(
            instance=page, many=True, context={'request': request}
        )

        return self.get_paginated_response(serializer.data)

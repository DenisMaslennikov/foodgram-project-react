from app.recipes.models import Recipe
from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.request import Request


class IsAuthorOrReadOnly(BasePermission):
    """Права для автора или только чтение"""
    def has_object_permission(
            self, request: Request, view, obj: Recipe
    ):
        """Проверяет права на объект у пользователя"""
        if request.method in SAFE_METHODS:
            return True
        return obj.author == request.user

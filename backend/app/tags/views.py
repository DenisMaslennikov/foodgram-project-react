from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import GenericViewSet

from .models import Tag
from .serializers import TagSerializer


class TagViewSet(RetrieveModelMixin, ListModelMixin, GenericViewSet):
    """Вьюсет тегов"""
    permission_classes = [AllowAny]
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    pagination_class = None

from django.db import models

from app.core.models import BaseModelMixin
from pytils.translit import slugify


class Tag(BaseModelMixin):
    """Модель тегов"""
    name = models.CharField(
        verbose_name='Название',
        max_length=200,
        unique=True,
        null=False,
    )
    color = models.CharField(
        verbose_name='Цвет',
        max_length=7,
        null=True,
    )
    slug = models.SlugField(
        verbose_name='слаг',
        max_length=200,
        unique=True,
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name', 'created')

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        """Сохранение тега, если слаг не указан генерим его из имени тега"""
        if not self.slug:
            max_slug_length = self._meta.get_field("slug").max_length
            self.slug = slugify(self.name)[:max_slug_length]
        super().save(*args, **kwargs)

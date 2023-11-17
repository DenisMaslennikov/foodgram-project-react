from django.db import models


class BaseModelMixin(models.Model):
    """Базовая модель для всех моделей"""
    created = models.DateTimeField(
        verbose_name="Создано",
        auto_now_add=True,
        auto_now=False,
    )
    modified = models.DateTimeField(
        verbose_name="Изменено",
        auto_now=True,
        auto_now_add=False,
    )

    class Meta:
        abstract = True

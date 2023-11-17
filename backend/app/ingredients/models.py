from django.db import models

from app.core.models import BaseModelMixin


class MeasurementUnit(BaseModelMixin):
    """Модель единицы измерения"""
    measurement_unit = models.CharField(
        verbose_name='Единица измерения',
        max_length=200,
        unique=True,
    )

    class Meta:
        verbose_name = 'Единица измерения'
        verbose_name_plural = 'Единицы измерения'
        ordering = ('id',)

    def __str__(self) -> str:
        return self.measurement_unit


class Ingredient(BaseModelMixin):
    """Модель ингредиентов"""
    measurement_unit = models.ForeignKey(
        to=MeasurementUnit,
        on_delete=models.CASCADE,
        verbose_name='Единица измерения'
    )
    name = models.CharField(
        verbose_name='Название',
        max_length=200,
    )

    class Meta:
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'
        ordering = ('id',)
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient',
            )
        ]

    def __str__(self) -> str:
        return self.name

    def callable_measurement_unit(self):
        """Для админки. Возвращает единицу измерения ингредиента."""
        return self.measurement_unit.measurement_unit
    callable_measurement_unit.short_description = 'Единица измерения'

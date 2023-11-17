from rest_framework import serializers

from .models import Ingredient


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов"""
    measurement_unit = serializers.CharField(
        source='measurement_unit.measurement_unit'
    )

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')

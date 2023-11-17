from django.core.management.base import BaseCommand
from django.db import transaction

from orjson import loads

from app.ingredients.models import Ingredient, MeasurementUnit


class Command(BaseCommand):
    """Команда для загрузки фикстур из json файла в модель"""
    help = "load fixtures from json file into model"

    def add_arguments(self, parser):
        """Извлекаем аргументы из строки команды"""
        parser.add_argument("path", nargs="+", type=str)

    @transaction.atomic
    def handle(self, *args, **options):
        """Сохраняем в модель данные из json файла"""
        with open(options.get('path')[0], 'rb') as data:
            ingredients = loads(data.read())
        measurement_unit = {value['measurement_unit'] for value in ingredients}
        bulk_measurement_unit = [
            MeasurementUnit(measurement_unit=value)
            for value in measurement_unit
        ]
        MeasurementUnit.objects.bulk_create(bulk_measurement_unit)
        bulk_ingredients = [
            Ingredient(
                name=value['name'],
                measurement_unit=MeasurementUnit.objects.get(
                    measurement_unit=value['measurement_unit']
                )
            )
            for value in ingredients
        ]
        Ingredient.objects.bulk_create(bulk_ingredients)

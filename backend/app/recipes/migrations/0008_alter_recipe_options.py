# Generated by Django 4.2.7 on 2023-11-17 16:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0007_remove_ingredientsrecipes_unique_ingredientsrecipes_for_user_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='recipe',
            options={'ordering': ('-created', 'id'), 'verbose_name': 'Рецепт', 'verbose_name_plural': 'Рецепты'},
        ),
    ]
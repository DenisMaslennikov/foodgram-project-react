from django.urls import include, path

from rest_framework.routers import DefaultRouter

from .views import RecipeViewSet

router = DefaultRouter()
router.register('recipes', RecipeViewSet, basename='Recipes')

urlpatterns = [path('', include(router.urls))]

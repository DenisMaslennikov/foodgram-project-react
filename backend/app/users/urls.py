from django.urls import include, path

from rest_framework.routers import DefaultRouter

from .views import Subscribe, Subscriptions, UserViewSet

router = DefaultRouter()
router.register('users', UserViewSet, basename='Users')

urlpatterns = [
    path('users/<int:pk>/subscribe/', Subscribe.as_view()),
    path('users/subscriptions/', Subscriptions.as_view()),
    path('', include(router.urls)),

]

from django.urls import path, include
from .views import UserHoldingViewSet
from rest_framework.routers import DefaultRouter
router = DefaultRouter()

router.register(r'user-holdings', UserHoldingViewSet, basename='user-holdings')

urlpatterns = [
    path('', include(router.urls)),
]

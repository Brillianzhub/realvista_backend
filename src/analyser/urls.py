from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FinancialTargetViewSet
from . import views
# Create a router and register the viewsets
router = DefaultRouter()
router.register(r'financial-targets', FinancialTargetViewSet,
                basename='financialtarget')

# Define the URL patterns
urlpatterns = [
    path('', include(router.urls)),
    path('add-contribution/<int:target_id>/',
         views.add_contribution, name='add_contribution')
]

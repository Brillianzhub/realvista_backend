from .views import UserOrderViewSet, ProjectOrderViewSet
from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter
router = DefaultRouter()

router.register(r'user-orders', UserOrderViewSet, basename='user-order')
router.register(r'project-orders', ProjectOrderViewSet,
                basename='project-order')

urlpatterns = [
    path('', include(router.urls)),
    path('send-email/', views.send_email_view, name='send_email'),
    path('update-payment-status/', views.update_payment_status,
         name='update-payment-status'),
]

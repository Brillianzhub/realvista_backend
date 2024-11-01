from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_user, name='register'),
    path('verify-email/', views.verify_email, name='verify_email'),
]

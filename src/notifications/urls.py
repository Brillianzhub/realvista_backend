from django.urls import path
from . import views

urlpatterns = [
    path('register-token/', views.register_token, name='register_token'),
    path('unregister-token/', views.delete_token, name='delete_token'),
]

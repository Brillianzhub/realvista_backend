from django.urls import path
from . import views
from rest_framework.authtoken.views import obtain_auth_token



urlpatterns = [
    path('properties/add/', views.add_property, name='add_property'),
    path('api-token-auth/', obtain_auth_token, name='api_token_auth'),

]

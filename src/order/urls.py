from django.urls import path
from . import views

urlpatterns = [
    path('send-email/', views.send_email_view, name='send_email'),
]

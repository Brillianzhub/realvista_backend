from django.urls import path
from .views import submit_contact_message

urlpatterns = [
    path('', submit_contact_message, name='submit_contact_message'),
]

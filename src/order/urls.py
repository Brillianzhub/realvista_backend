from django.urls import path
from . import views

urlpatterns = [
    path('send-email/', views.send_email_view, name='send_email'),
    path('create-order/', views.create_order_view, name="create_order"),
    path('create-order-and-send-email/', views.create_order_and_send_email_view,
         name='create_order_and_send_email')
]

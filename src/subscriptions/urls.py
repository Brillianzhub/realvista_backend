from django.urls import path
from . import views

urlpatterns = [
    path('create-subscription/', views.create_paystack_subscription,
         name='create-subscription'),
    path('cancel-subscription/', views.cancel_paystack_subscription,
         name='cancel-subscription'),
    path("plans/", views.get_subscription_plans,
         name="get_subscription_plans"),
    path('paystack/webhook/', views.paystack_webhook, name='paystack-webhook'),
]

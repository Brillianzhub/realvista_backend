from django.urls import path
from . import views

urlpatterns = [
    path('property-purchase/', views.CreatePropertyPurchaseView.as_view(),
         name='create-property-purchase'),
    path('orders/<str:order_id>/cancel/',
         views.cancel_order, name='cancel_order'),
    path('payment-plans/', views.PaymentPlanListView.as_view(), name='payment-plans'),
    path('installment-payment/', views.InstallmentPaymentCreateView.as_view(),
         name='installment-payment')
]

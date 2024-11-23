from django.urls import path
from .views import CreateDividendAPIView

urlpatterns = [
    path('user-dividends/', CreateDividendAPIView.as_view(), name='create-dividend'),
]

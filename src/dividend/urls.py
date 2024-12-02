from .views import CreateDividendAPIView, UserDividendsAPIView
from django.urls import path


urlpatterns = [
    path('create-dividend/', CreateDividendAPIView.as_view(), name='create-dividend'),
    path('user-dividends/', UserDividendsAPIView.as_view(),
         name='user-dividends'),
]

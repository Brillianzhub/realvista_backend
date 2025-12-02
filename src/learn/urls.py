from django.urls import path
from .views import LearnListAPIView, LearnDetailAPIView, LearnRecentAPIView, LearnIncrementViewAPIView

urlpatterns = [
    path('list/', LearnListAPIView.as_view(), name='learn-list'),
    path('recent/', LearnRecentAPIView.as_view(), name='learn-recent'),
    path('<slug:slug>/', LearnDetailAPIView.as_view(), name='learn-detail'),
    path('<slug:slug>/increment-view/',
         LearnIncrementViewAPIView.as_view(), name='learn-increment-view'),
]

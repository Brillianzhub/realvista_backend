from django.urls import path
from .views import LatestApprovedFeedbackList, FeedbackCreateView

urlpatterns = [
    path('', LatestApprovedFeedbackList.as_view(), name='latest-feedbacks'),
    path('submit-feedback/', FeedbackCreateView.as_view(), name='submit-feedback'),
]

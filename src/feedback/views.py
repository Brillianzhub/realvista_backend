from rest_framework import generics
from rest_framework.permissions import AllowAny
from .models import Feedback
from .serializers import FeedbackSerializer
from rest_framework import generics, permissions


class LatestApprovedFeedbackList(generics.ListAPIView):
    serializer_class = FeedbackSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Feedback.objects.filter(is_approved=True).order_by('-created_at')[:5]


class FeedbackCreateView(generics.CreateAPIView):
    serializer_class = FeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

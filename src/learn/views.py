from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q, F
from .models import Learn
from .serializers import LearnSerializer
from rest_framework.permissions import AllowAny


class LearnListAPIView(APIView):
    """
    GET /api/learn/
    Optional query params:
    - category: filter by category (?category=Real Estate)
    - search: search title or description (?search=invest)
    - ordering: order by field (?ordering=view_count or -created_at)
    """
    permission_classes = [AllowAny]

    def get(self, request):
        queryset = Learn.objects.all()

        # Filter by category
        category = request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__iexact=category)

        # Search functionality
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )

        # Ordering
        ordering = request.query_params.get('ordering', '-created_at')
        queryset = queryset.order_by(ordering)

        serializer = LearnSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class LearnDetailAPIView(APIView):
    """
    GET /api/learn/<slug:slug>/
    Retrieve a single lesson using the slug field.
    """
    permission_classes = [AllowAny]

    def get(self, request, slug):
        try:
            lesson = Learn.objects.get(slug=slug)
        except Learn.DoesNotExist:
            return Response({'detail': 'Lesson not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = LearnSerializer(lesson)
        return Response(serializer.data, status=status.HTTP_200_OK)


class LearnRecentAPIView(APIView):
    """
    GET /api/learn/recent/
    Retrieve 5 most recent lessons.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        recent_lessons = Learn.objects.order_by('-created_at')[:5]
        serializer = LearnSerializer(recent_lessons, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class LearnIncrementViewAPIView(APIView):
    """
    POST /api/learn/<slug:slug>/increment-view/
    Increments the view count for a lesson when a user engages with a video.
    """
    permission_classes = [AllowAny]

    def post(self, request, slug):
        try:
            lesson = Learn.objects.get(slug=slug)
        except Learn.DoesNotExist:
            return Response({'detail': 'Lesson not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Use F() to safely increment in a single DB query
        lesson.view_count = F('view_count') + 1
        lesson.save(update_fields=['view_count'])
        lesson.refresh_from_db(fields=['view_count'])

        return Response(
            {'message': 'View count incremented.',
                'view_count': lesson.view_count},
            status=status.HTTP_200_OK
        )

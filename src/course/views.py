from rest_framework.filters import SearchFilter
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from .serializers import CourseSerializer, UserProgressSerializer
from .models import Course, Module, Payment
from rest_framework.decorators import api_view
from django.shortcuts import get_object_or_404
from .models import Course, CourseEnrollment
from rest_framework.permissions import IsAuthenticated
from .serializers import CourseEnrollmentSerializer
from .models import Review
from .serializers import ReviewSerializer
from realvista_backend.utility import record_user_progress
from .models import UserProgress
from .serializers import UserProgressSerializer
from .models import Review, Vote
import requests
import random
import string
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
import uuid
import hashlib
import hmac
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from rest_framework.permissions import AllowAny
from .models import Payment, CourseEnrollment
import websocket
import socketio
from django.core.asgi import get_asgi_application
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from .models import Learn
from .serializers import LearnSerializer


class LearnListAPIView(APIView):
    """
    GET /api/learn/
    Optional query params:
    - category: filter by category (?category=Real Estate)
    - search: search title or description (?search=invest)
    - ordering: order by field (?ordering=view_count or -created_at)
    """

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

    def get(self, request):
        recent_lessons = Learn.objects.order_by('-created_at')[:5]
        serializer = LearnSerializer(recent_lessons, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


PAYSTACK_SECRET_KEY = settings.PAYSTACK_SECRET_KEY


class CoursePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class CourseListView(ListAPIView):
    queryset = Course.objects.prefetch_related('modules').all()
    serializer_class = CourseSerializer
    pagination_class = CoursePagination
    filter_backends = [SearchFilter]
    search_fields = ['title', 'description', 'modules__title']


class CourseDetailView(APIView):
    def get(self, request, course_id, *args, **kwargs):
        try:
            course = Course.objects.prefetch_related(
                'modules__lessons__questions__options'
            ).get(pk=course_id)

            serializer = CourseSerializer(course, context={'request': request})

            return Response(serializer.data, status=status.HTTP_200_OK)

        except Course.DoesNotExist:
            return Response({'error': 'Course not found'}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RecordUserProgressView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        module_id = request.data.get('module_id')
        score = request.data.get('score')
        total = request.data.get('total')

        if not all([module_id, score, total]):
            return Response(
                {"error": "module_id, score, and total are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = request.user
        module = get_object_or_404(Module, id=module_id)

        try:
            progress = record_user_progress(user, module, score, total)
            return Response(
                {
                    "message": "Progress recorded successfully.",
                    "progress": {
                        "id": progress.id,
                        "user": progress.user.name,
                        "module": progress.module.title,
                        "score": progress.score,
                        "total": progress.total,
                        "passed": progress.passed,
                        "date_completed": progress.date_completed
                    }
                },
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FetchUserProgressView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        progress_records = UserProgress.objects.filter(
            user=user).order_by('-date_completed')

        if not progress_records.exists():
            return Response(
                {"message": "No progress records found for this user."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = UserProgressSerializer(progress_records, many=True)
        return Response(
            {
                "message": "Progress records fetched successfully.",
                "progress": serializer.data
            },
            status=status.HTTP_200_OK
        )


class EnrollCourseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, course_id):
        user = request.user
        course = get_object_or_404(Course, pk=course_id)

        if CourseEnrollment.objects.filter(user=user, course=course).exists():
            return Response(
                {"error": "You are already enrolled in this course."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            enrollment = CourseEnrollment.objects.create(
                user=user, course=course)

            serializer = CourseEnrollmentSerializer(enrollment)
            return Response(
                {
                    "message": f"You have successfully enrolled in the course: {course.title}",
                    "enrollment": serializer.data,
                },
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {"error": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CreateOrUpdateReviewView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, course_id):
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Response(
                {"error": "Course not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        review, created = Review.objects.get_or_create(
            user=request.user,
            course=course,
            defaults={'rating': request.data.get(
                'rating'), 'comment': request.data.get('comment')}
        )

        if not created:
            serializer = ReviewSerializer(
                review, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            serializer = ReviewSerializer(review)
            return Response(serializer.data, status=status.HTTP_201_CREATED)


class CourseReviewsView(APIView):

    def get(self, request, course_id):

        reviews = Review.objects.filter(
            course_id=course_id).order_by('-created_at')

        serializer = ReviewSerializer(
            reviews, many=True, context={'request': request})

        return Response(serializer.data, status=status.HTTP_200_OK)


class UpvoteReviewView(APIView):
    def post(self, request, review_id):
        review = Review.objects.get(id=review_id)
        user = request.user

        existing_vote = Vote.objects.filter(user=user, review=review).first()

        if existing_vote:
            if existing_vote.vote_type == 'upvote':
                existing_vote.delete()
            else:
                existing_vote.vote_type = 'upvote'
                existing_vote.save()
        else:
            Vote.objects.create(user=user, review=review, vote_type='upvote')

        serializer = ReviewSerializer(review)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DownvoteReviewView(APIView):
    def post(self, request, review_id):
        review = Review.objects.get(id=review_id)
        user = request.user

        existing_vote = Vote.objects.filter(user=user, review=review).first()

        if existing_vote:
            if existing_vote.vote_type == 'downvote':
                existing_vote.delete()
            else:
                existing_vote.vote_type = 'downvote'
                existing_vote.save()
        else:
            Vote.objects.create(user=user, review=review, vote_type='downvote')

        serializer = ReviewSerializer(review)
        return Response(serializer.data, status=status.HTTP_200_OK)


def generate_transaction_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))


def create_payment_instance(user, course):
    reference = str(uuid.uuid4())

    payment = Payment.objects.create(
        user=user,
        course=course,
        amount=course.price,
        currency=course.currency,
        status="pending",
        transaction_id=reference,
        payment_method="Paystack",
    )
    return payment


def create_enrollment_instance(user, course):
    enrollment, created = CourseEnrollment.objects.get_or_create(
        user=user,
        course=course,
        defaults={"is_active": False}
    )
    return enrollment


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initialize_payment(request, course_id):
    user = request.user
    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        return Response({"error": "Course not found"}, status=status.HTTP_404_NOT_FOUND)

    if course.is_free:
        return Response({"message": "This course is free. No payment required."}, status=status.HTTP_400_BAD_REQUEST)

    if course.price is None:
        return Response({"error": "Course price is not set"}, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        payment = create_payment_instance(user, course)
        create_enrollment_instance(user, course)

    total_amount = int(course.price * 100)

    paystack_url = "https://api.paystack.co/transaction/initialize"
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "email": user.email,
        "amount": total_amount,
        "currency": course.currency,
        "reference": payment.transaction_id,
        "callback_url": "https://realvistaproperties.com/payment-success",
        "metadata": {
            "course_id": course.id,
            "payment_id": payment.id
        },
    }

    response = requests.post(paystack_url, json=data, headers=headers)
    if response.status_code == 200:
        return Response(response.json(), status=status.HTTP_200_OK)
    return Response({"error": "Payment initialization failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Replace with your Socket.IO server URL
SOCKETIO_SERVER_URL = 'http://localhost:9000'

# Create a Socket.IO client
sio = socketio.Client()


def send_socket_message(transaction_id, status):
    """Send payment status update to the frontend via Socket.IO."""
    try:
        if not sio.connected:
            sio.connect(SOCKETIO_SERVER_URL)
        sio.emit('payment_status_update', {
            'transaction_id': transaction_id,
            'status': status,
        })
        print(f"Sent Socket.IO message: {status}")
    except Exception as sio_error:
        print(f"Socket.IO error: {sio_error}")


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def paystack_webhook(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=400)

    try:
        event_data = json.loads(request.body)
        print("Received Paystack Webhook:", event_data)

        # Extract relevant data
        # reference = event_data["data"].get("reference", "unknown-reference")
        # status = event_data["data"].get("status", "unknown-status")

        reference = "test-reference-id",
        status = "completed",

        # Send the socket message
        send_socket_message(reference, status)

        return JsonResponse({"message": "Webhook processed successfully"}, status=200)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

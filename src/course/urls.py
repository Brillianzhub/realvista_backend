from django.urls import path
from .views import CourseListView, CourseDetailView
from . import views

urlpatterns = [

    path('courses/', CourseListView.as_view(), name='course-list'),
    path('courses/<int:course_id>/',
         CourseDetailView.as_view(), name='course-detail'),
    path('record-progress/', views.RecordUserProgressView.as_view(),
         name='record_progress'),
    path('fetch-progress/', views.FetchUserProgressView.as_view(),
         name='fetch-progress'),
    path('enroll/<int:course_id>/',
         views.EnrollCourseView.as_view(), name='enroll_course'),
    path('review/<int:course_id>/',
         views.CreateOrUpdateReviewView.as_view(), name='create-or-update-review'),
    path('fetch-reviews/<int:course_id>/',
         views.CourseReviewsView.as_view(), name='course-reviews'),
    path('reviews/<int:review_id>/upvote/',
         views.UpvoteReviewView.as_view(), name='upvote-review'),
    path('reviews/<int:review_id>/downvote/',
         views.DownvoteReviewView.as_view(), name='downvote-review'),
    path('payment/initiate/<int:course_id>/',
         views.initialize_payment, name='initiate-payment'),
    path('payment/webhook/', views.paystack_webhook, name='paystack-webhook'),
]

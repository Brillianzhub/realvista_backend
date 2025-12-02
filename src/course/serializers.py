from .models import Review, Vote
from .models import Payment
from .models import Review
from .models import Course
from rest_framework import serializers
from .models import Course, Module, Lesson, Question, Option, CourseEnrollment, UserProgress


from rest_framework import serializers
from .models import UserProgress, User, Module


from rest_framework import serializers
from .models import Learn


class LearnSerializer(serializers.ModelSerializer):
    class Meta:
        model = Learn
        fields = [
            'id',
            'title',
            'slug',
            'description',
            'category',
            'youtube_url',
            'youtube_id',
            'thumbnail_url',
            'duration',
            'view_count',
            'created_at',
        ]
        read_only_fields = ['slug', 'youtube_id',
                            'thumbnail_url', 'created_at']


class CourseEnrollmentSerializer(serializers.ModelSerializer):
    progress_percentage = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CourseEnrollment
        fields = ['id', 'user', 'course', 'enrolled_at',
                  'is_active', 'completed', 'progress_percentage']

    def get_progress_percentage(self, obj):
        return obj.progress_percentage


class OptionSerializers(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = ['id', 'text', 'is_correct']


class QuestionSerialzers(serializers.ModelSerializer):
    options = OptionSerializers(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'text', 'order', 'options']


class LessonSerializer(serializers.ModelSerializer):
    questions = QuestionSerialzers(many=True, read_only=True)

    class Meta:
        model = Lesson
        fields = ['id', 'title', 'content', 'image',
                  'order', 'video_url', 'questions']


class ModuleSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Module
        fields = ['id', 'title', 'description', 'image',
                  'order', 'lessons']


class ModuleProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = ['id', 'title', 'description', 'image', 'order']


class UserProgressSerializer(serializers.ModelSerializer):
    module = ModuleProgressSerializer(read_only=True)

    class Meta:
        model = UserProgress
        fields = ['id', 'user', 'module', 'score',
                  'total', 'passed', 'date_completed']
        read_only_fields = ['id', 'user', 'date_completed']


class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    user_avatar = serializers.SerializerMethodField()
    upvotes = serializers.SerializerMethodField()
    downvotes = serializers.SerializerMethodField()
    user_vote = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ['id', 'user_name', 'rating', 'grade', 'comment',
                  'created_at', 'updated_at', 'upvotes', 'downvotes', 'user_vote', 'user_avatar']

    def get_user_name(self, obj):
        return obj.user.name

    def get_user_avatar(self, obj):
        profile = getattr(obj.user, 'profile', None)
        if profile and profile.avatar:
            return profile.avatar.url  # Return the avatar URL if it exists
        return None  # Return None if no profile or no avatar

    def get_upvotes(self, obj):
        return obj.votes.filter(vote_type='upvote').count()

    def get_downvotes(self, obj):
        return obj.votes.filter(vote_type='downvote').count()

    def get_user_vote(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            vote = obj.votes.filter(user=request.user).first()
            if vote:
                return vote.vote_type
        return None


class PaymentSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "user",
            "user_email",
            "course",
            "amount",
            "currency",
            "payment_method",
            "status",
            "transaction_id",
            "created_at",
        ]
        read_only_fields = ["transaction_id", "created_at"]


class CourseSerializer(serializers.ModelSerializer):
    modules = ModuleSerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField(read_only=True)
    enrollments = CourseEnrollmentSerializer(many=True, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)
    enrollment_count = serializers.SerializerMethodField(
        read_only=True)

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'description', 'image', 'created_at', 'updated_at',
            'duration', 'price', 'currency', 'is_free', 'language', 'level', 'instructor', 'prerequisites',
            'learning_outcomes', 'category', 'is_active', 'modules',
            'average_rating', 'enrollments', 'payments', 'status', 'reviews', 'enrollment_count'
        ]

    def get_average_rating(self, obj):
        return obj.average_rating

    def get_enrollment_count(self, obj):
        return obj.enrollment_count

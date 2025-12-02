import re
from django.utils.text import slugify
from django.conf import settings
from django.db import models
from accounts.models import User
from datetime import datetime
from django.core.validators import MinValueValidator, MaxValueValidator
from realvista_backend.currencies import CURRENCY_DATA


def upload_to(instance, filename):
    now = datetime.now().strftime("%Y/%m/%d/")
    return f"course_images/{now}{filename}"


def upload_to(instance, filename):
    now = datetime.now().strftime("%Y/%m/%d/")
    return f"course_images/{now}{filename}"


class Course(models.Model):

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
    ]

    CURRENCY_CHOICES = [(key, label) for key, label in CURRENCY_DATA.items()]

    title = models.CharField(max_length=255, unique=True)
    description = models.TextField()
    image = models.ImageField(upload_to=upload_to, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='draft',
        help_text="Status of the course (Draft or Published)"
    )
    duration = models.DurationField(
        help_text="Duration of the course", null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2,
                                null=True, blank=True, help_text="Price of the course")
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='NGN',
        help_text="Currency for the premium courses."
    )
    is_free = models.BooleanField(
        default=False, help_text="Is the course free?")
    language = models.CharField(
        max_length=50, default="English", help_text="Language of the course")
    level = models.CharField(
        max_length=20,
        choices=[("Beginner", "Beginner"), ("Intermediate",
                                            "Intermediate"), ("Advanced", "Advanced")],
        default="Beginner",
        help_text="Difficulty level of the course"
    )
    instructor = models.CharField(
        max_length=255, null=True, blank=True, help_text="Name of the course instructor")
    prerequisites = models.TextField(
        null=True, blank=True, help_text="Prerequisites for the course")
    learning_outcomes = models.TextField(
        null=True, blank=True, help_text="What students will learn from the course")
    category = models.CharField(max_length=100, null=True, blank=True,
                                help_text="Category of the course (e.g., Programming, Design, Business)")
    is_active = models.BooleanField(
        default=True, help_text="Is the course currently active?")

    def __str__(self):
        return self.title

    @property
    def enrollment_count(self):
        return self.enrollments.count()

    @property
    def average_rating(self):
        reviews = self.reviews.all()
        if reviews.exists():
            return round(reviews.aggregate(models.Avg('rating'))['rating__avg'], 2)
        return 0.0


class Module(models.Model):
    course = models.ForeignKey(
        Course, related_name='modules', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to=upload_to, null=True, blank=True)
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.title} - {self.course.title}"


class Lesson(models.Model):
    module = models.ForeignKey(
        Module, related_name='lessons', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to=upload_to, null=True, blank=True)
    content = models.TextField()
    order = models.PositiveIntegerField()
    video_url = models.URLField(blank=True, null=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.title} - {self.module.title}"


class Question(models.Model):
    lesson = models.ForeignKey(
        Lesson, related_name='questions', on_delete=models.CASCADE)
    text = models.TextField()
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Question {self.order}: {self.text[:50]}"


class Option(models.Model):
    question = models.ForeignKey(
        Question, related_name='options', on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"Option: {self.text} (Correct: {self.is_correct})"


class CourseEnrollment(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(
        default=True, help_text="Is the enrollment currently active?")
    completed = models.BooleanField(
        default=False, help_text="Has the user completed the course?")

    class Meta:
        unique_together = ('user', 'course')

    def __str__(self):
        return f"{self.user.name} enrolled in {self.course.title}"

    @property
    def progress_percentage(self):

        total_modules = self.course.modules.count()
        if total_modules == 0:
            return 0
        completed_modules = UserProgress.objects.filter(
            user=self.user,
            module__course=self.course,
        ).count()
        return round((completed_modules / total_modules) * 100, 2)


class UserProgress(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='progress')
    module = models.ForeignKey(
        Module, related_name='progress', on_delete=models.CASCADE)
    score = models.IntegerField(
        default=0, help_text="Score achieved by the user in this module")
    total = models.IntegerField(
        default=0, help_text="Total score possible for this module")
    passed = models.BooleanField(
        default=False, help_text="Did the user pass this module?")
    date_completed = models.DateTimeField(
        null=True, blank=True, help_text="Date when the module was completed")

    class Meta:
        unique_together = ('user', 'module')

    def __str__(self):
        return f"{self.user.name}'s progress in {self.module.title}"


class Review(models.Model):
    GRADE_CHOICES = [
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('average', 'Average'),
        ('below_average', 'Below Average'),
        ('poor', 'Poor'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='user_review')
    course = models.ForeignKey(
        'Course', related_name='reviews', on_delete=models.CASCADE)
    rating = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)])
    grade = models.CharField(
        max_length=15, choices=GRADE_CHOICES, default='average')
    comment = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Review for {self.course.title} by {self.user.name}"


class Vote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    review = models.ForeignKey(
        'Review', on_delete=models.CASCADE, related_name='votes')
    vote_type = models.CharField(max_length=10, choices=[(
        'upvote', 'Upvote'), ('downvote', 'Downvote')])

    class Meta:
        unique_together = ('user', 'review')


class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name="payments", help_text="User who made the payment"
                             )
    course = models.ForeignKey('Course', on_delete=models.CASCADE,
                               related_name="payments", help_text="The course that was paid for"
                               )
    amount = models.DecimalField(
        max_digits=10, decimal_places=2,
        help_text="Amount paid for the course"
    )
    currency = models.CharField(
        max_length=3,
        choices=[(key, label) for key, label in CURRENCY_DATA.items()],
        default='NGN',
        help_text="Currency used for the payment"
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Current status of the payment"
    )
    transaction_id = models.CharField(
        max_length=255,
        unique=True,
        help_text="Unique transaction ID from the payment gateway"
    )
    payment_method = models.CharField(
        max_length=50,
        help_text="Payment method used (e.g., Credit Card, PayPal, Bank Transfer)"
    )
    created_at = models.DateTimeField(
        auto_now_add=True, help_text="Time when the payment was initiated")
    updated_at = models.DateTimeField(
        auto_now=True, help_text="Last update time of the payment status")

    def __str__(self):
        return f"{self.user} - {self.course} - {self.status}"

    class Meta:
        ordering = ['-created_at']


class Learn(models.Model):
    CATEGORY_CHOICES = [
        ('Real Estate', 'Real Estate'),
        ('Finance', 'Finance'),
        ('Investment', 'Investment'),
    ]

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    youtube_url = models.URLField()
    youtube_id = models.CharField(
        max_length=50, blank=True, null=True, editable=False)
    thumbnail_url = models.URLField(blank=True, null=True, editable=False)
    duration = models.CharField(max_length=20, blank=True, null=True)
    view_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Learn Resource"
        verbose_name_plural = "Learn Resources"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Auto-generate slug if missing
        if not self.slug:
            self.slug = slugify(self.title)

        # Extract YouTube video ID
        if self.youtube_url:
            video_id = self.extract_youtube_id()
            if video_id:
                self.youtube_id = video_id
                self.thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"

        super().save(*args, **kwargs)

    def extract_youtube_id(self):
        """
        Extracts the YouTube video ID from various URL formats.
        Supports:
        - https://www.youtube.com/watch?v=XXXX+  
        - https://youtu.be/XXXX
        - https://www.youtube.com/embed/XXXX
        """
        pattern = r"(?:v=|youtu\.be/|embed/)([A-Za-z0-9_-]{11})"
        match = re.search(pattern, self.youtube_url)
        return match.group(1) if match else None

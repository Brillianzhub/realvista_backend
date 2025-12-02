from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from accounts.models import User
from datetime import datetime


def upload_to(instance, filename):
    now = datetime.now().strftime("%Y/%m/%d/")
    return f"user_images/{now}{filename}"


class Agent(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='agent_profile')
    avatar = models.ImageField(upload_to=upload_to, null=True, blank=True)
    agency_name = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Real Estate Agency")
    agency_address = models.TextField(
        blank=True, null=True, verbose_name="Agency Address")
    phone_number = models.CharField(
        max_length=20, verbose_name="Contact Number")
    whatsapp_number = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="WhatsApp Number")
    experience_years = models.PositiveIntegerField(
        default=0, verbose_name="Years of Experience")
    preferred_contact_mode = models.CharField(
        max_length=20,
        choices=[('phone', 'Phone'), ('whatsapp',
                                      'WhatsApp'), ('email', 'Email')],
        default='phone',
        verbose_name="Preferred Mode of Contact"
    )
    verified = models.BooleanField(
        default=False, verbose_name="Verified Agent")
    featured = models.BooleanField(
        default=False, verbose_name="Featured Agent")
    bio = models.TextField(
        null=True, blank=True, help_text="A short biography or personal description")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.name} - {self.agency_name}"


class AgentRating(models.Model):
    RATING_CHOICES = [
        (1, '1 - Poor'),
        (2, '2 - Fair'),
        (3, '3 - Average'),
        (4, '4 - Good'),
        (5, '5 - Excellent'),
    ]

    agent = models.ForeignKey(
        Agent,
        on_delete=models.CASCADE,
        related_name='ratings',
        verbose_name="Agent being rated"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='agent_ratings',
        verbose_name="User who rated"
    )
    rating = models.PositiveSmallIntegerField(
        choices=RATING_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Rating (1-5 stars)"
    )
    review = models.TextField(
        blank=True,
        null=True,
        verbose_name="Detailed review"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('agent', 'user')
        ordering = ['-created_at']
        verbose_name = "Agent Rating"
        verbose_name_plural = "Agent Ratings"

    def __str__(self):
        return f"{self.user.name}'s {self.rating}-star rating for {self.agent.user.name}"


# from django.conf import settings

def verification_upload_to(instance, filename):
    return f"verifications/agent_{instance.agent.id}/{filename}"


class AgentVerification(models.Model):
    agent = models.OneToOneField(
        'Agent',
        on_delete=models.CASCADE,
        related_name='verification'
    )
    id_card = models.ImageField(upload_to=verification_upload_to)
    photo = models.ImageField(upload_to=verification_upload_to)
    business_registration = models.FileField(
        upload_to=verification_upload_to,
        null=True,
        blank=True,
        help_text="Optional business registration document"
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed = models.BooleanField(default=False)
    approved = models.BooleanField(default=False)
    rejection_reason = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Verification for {self.agent.user.name}"

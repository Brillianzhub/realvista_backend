from django.core.validators import MinValueValidator
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid
from django.utils import timezone
import threading
from datetime import datetime, timedelta
from django.conf import settings
from phonenumber_field.modelfields import PhoneNumberField
from django.contrib.auth.models import User
from django.utils.timezone import now, timedelta
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from datetime import datetime


def upload_to(instance, filename):
    now = datetime.now().strftime("%Y/%m/%d/")
    return f"user_images/{now}{filename}"


class UserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    name = models.CharField(max_length=255)
    first_name = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(unique=True)
    auth_provider = models.CharField(max_length=50, default='email')
    is_email_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)
    is_identity_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_agent = models.BooleanField(default=False, verbose_name="Is Agent")
    date_joined = models.DateTimeField(auto_now_add=True)
    google_id = models.CharField(max_length=50, null=True, blank=True)
    apple_id = models.CharField(max_length=100, null=True, blank=True)

    referral_code = models.CharField(
        max_length=12, unique=True, blank=True, null=True)
    referrer = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='referred_users'
    )
    total_referral_earnings = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal(0)
    )

    def update_referral_earnings(self, amount):
        self.total_referral_earnings += amount
        self.save()

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = uuid.uuid4().hex[:12]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email


class UserToken(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE,  related_name="token")
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_expired(self):
        return now() > self.expires_at


class Profile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to=upload_to, null=True, blank=True)
    phone_number = PhoneNumberField(unique=True, null=True, blank=True)
    whatsapp_number = models.CharField(max_length=15, null=True, blank=True)
    country_of_residence = models.CharField(
        max_length=100, null=True, blank=True)
    state = models.CharField(
        max_length=100, help_text="State where the property is located")
    city = models.CharField(max_length=100, null=True, blank=True)
    street = models.CharField(max_length=255, null=True, blank=True)
    house_number = models.CharField(max_length=20, null=True, blank=True)
    postal_code = models.CharField(max_length=20, null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.name}'s Profile"


class UserPreference(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='preferences')

    contact_by_email = models.BooleanField(default=True)
    contact_by_whatsapp = models.BooleanField(default=False)
    contact_by_phone = models.BooleanField(default=False)

    def __str__(self):
        return f"Preferences for {self.user.name}"

    class Meta:
        verbose_name = "User Preference"
        verbose_name_plural = "User Preferences"


class PasswordResetOTP(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="password_reset_otps")
    otp = models.CharField(max_length=5)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_valid(self):
        return timezone.now() < self.expires_at

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=10)
        super().save(*args, **kwargs)
        self.schedule_deletion()

    def schedule_deletion(self):
        delay = (self.expires_at - timezone.now()).total_seconds()
        threading.Timer(delay, self.delete_expired).start()

    @classmethod
    def delete_expired(cls):
        cls.objects.filter(expires_at__lt=timezone.now()).delete()

    def __str__(self):
        return f"OTP for {self.user.email} (Expires: {self.expires_at})"


class Referral(models.Model):
    referrer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='referrals_made')
    referred_user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='referral')
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.referrer == self.referred_user:
            raise ValidationError("A user cannot refer themselves.")

        if self._is_referral_cycle(self.referrer, self.referred_user):
            raise ValidationError("A referral cycle is not allowed.")

    @classmethod
    def _is_referral_cycle(cls, referrer, referred_user):
        current_user = referrer
        while Referral.objects.filter(referred_user=current_user).exists():
            current_referral = Referral.objects.filter(
                referred_user=current_user).first()
            if not current_referral:
                break
            if current_referral.referrer == referred_user:
                return True
            current_user = current_referral.referrer
        return False


class AdminProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='admin_profile'
    )
    role = models.CharField(max_length=50, choices=[
        ('super_admin', 'Super Admin'),
        ('moderator', 'Moderator'),
        ('content_manager', 'Content Manager'),
    ])
    access_level = models.PositiveSmallIntegerField(default=1)
    permissions = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} ({self.role})"


class ReferralPayout(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('processed', 'Processed'),
    ]

    PAYMENT_METHODS = [
        ('bank', 'Bank Transfer'),
        # ('mobile_money', 'Mobile Money'),
        # ('paypal', 'PayPal'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='payouts')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[
                                 MinValueValidator(Decimal('10.00'))])
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    account_details = models.TextField()
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.status == 'processed' and not self.processed_at:
            self.processed_at = timezone.now()
        super().save(*args, **kwargs)

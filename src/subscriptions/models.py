from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.db import models
from accounts.models import User


class SubscriptionPlan(models.Model):
    FREE = "free"
    BASIC = 'basic'
    PREMIUM = 'premium'
    ENTERPRISE = 'enterprise'

    PLAN_CHOICES = [
        (FREE, 'Free'),
        (BASIC, 'Basic'),
        (PREMIUM, 'Premium'),
        (ENTERPRISE, 'Enterprise'),
    ]

    name = models.CharField(max_length=100, choices=PLAN_CHOICES, unique=True)

    features = models.TextField(blank=True)
    color = models.CharField(max_length=7, default="#94a3b8")
    popular = models.BooleanField(default=False)
    image = models.URLField(
        max_length=500,
        default="https://images.unsplash.com/photo-1579621970563-ebec7560ff3e..."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.get_name_display()

    @property
    def features_list(self):
        if self.features:
            return self.features.split(", ")
        return []

    class Meta:
        verbose_name = _("Subscription Plan")
        verbose_name_plural = _("Subscription Plans")


class PlanDuration(models.Model):
    MONTHLY = 'monthly'
    SIX_MONTHS = 'six_months'
    YEARLY = 'yearly'

    DURATION_CHOICES = [
        (MONTHLY, 'Monthly'),
        (SIX_MONTHS, 'Six Months'),
        (YEARLY, 'Yearly'),
    ]

    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.CASCADE,
        related_name='durations'
    )
    paystack_plan_code = models.CharField(
        max_length=100, unique=True, null=True, blank=True)
    duration_type = models.CharField(
        max_length=20,
        choices=DURATION_CHOICES,
        default=MONTHLY
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00
    )
    currency = models.CharField(
        max_length=3,
        choices=[
            ("NGN", "Naira"),
            ("USD", "US Dollar"),
            ("EUR", "Euro"),
        ],
        default="NGN"
    )
    discount_percentage = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('plan', 'duration_type')

    def __str__(self):
        return f"{self.plan.get_name_display()} - {self.get_duration_type_display()}"

    @property
    def discounted_price(self):
        return self.price * (100 - self.discount_percentage) / 100


class UserSubscription(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="subscription")
    plan = models.ForeignKey(
        PlanDuration, on_delete=models.SET_NULL, null=True, blank=True)
    subscription_code = models.CharField(
        max_length=100, unique=True, null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ("active", "Active"),
        ("cancelled", "Cancelled"),
        ("expired", "Expired"),
    ], default="active")
    next_payment_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.plan.plan} - {self.status}"


class SubscriptionCancellation(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="cancellations")
    subscription = models.ForeignKey(
        "UserSubscription", on_delete=models.CASCADE, related_name="cancellations")
    reason = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.reason}"


class ReferralEarning(models.Model):
    referrer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='referral_earnings')
    referred_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='earnings_generated')
    subscription = models.ForeignKey(
        UserSubscription, on_delete=models.CASCADE)
    amount_earned = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.referrer.email} earned {self.amount_earned} from {self.referred_user.email}'s subscription"


class Payment(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("success", "Success"),
        ("failed", "Failed"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="subscription_payments")
    plan = models.ForeignKey(
        SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reference = models.CharField(max_length=100, unique=True)
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default="pending")
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.plan.name} - {self.status}"

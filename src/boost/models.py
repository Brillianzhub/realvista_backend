from django.db import models
from accounts.models import User
from market.models import MarketProperty
from django.utils import timezone


class BoostPackage(models.Model):
    name = models.CharField(max_length=50)
    duration_days = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.name} ({self.duration_days} days - ${self.price})"


class BoostOrder(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("failed", "Failed"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="boost_orders")
    property = models.ForeignKey(
        MarketProperty, on_delete=models.CASCADE, related_name="boost_orders")
    package = models.ForeignKey(BoostPackage, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    starts_at = models.DateTimeField(default=timezone.now)
    ends_at = models.DateTimeField(blank=True, null=True)

    is_active = models.BooleanField(default=False)
    payment_status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default="pending"
    )
    transaction_reference = models.CharField(
        max_length=100, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.ends_at and self.package:
            self.ends_at = self.starts_at + \
                timezone.timedelta(days=self.package.duration_days)
        if self.payment_status == "paid":
            self.is_active = True
        else:
            self.is_active = False
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Boost for {self.property.title} by {self.user.email} - {self.package.name} [{self.payment_status}]"

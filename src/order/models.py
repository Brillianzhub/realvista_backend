import random
import string
from django.db import models
from accounts.models import User
from django.utils import timezone  # Correct import


def generate_order_reference():
    """Generates a unique order reference number."""
    prefix = "RV"  # Example: Prefix for "Realvista"
    random_string = ''.join(random.choices(
        string.ascii_uppercase + string.digits, k=6))
    return f"{prefix}-{random_string}-{int(timezone.now().timestamp())}"


class Order(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('not_paid', 'Not Paid'),
        ('paid', 'Paid'),
        ('payment_confirm', 'Payment Confirmed'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='orders')
    project_name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='not_paid'
    )
    order_reference = models.CharField(
        max_length=50, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.order_reference:
            self.order_reference = generate_order_reference()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order {self.order_reference} - {self.project_name} - {self.user.name}"

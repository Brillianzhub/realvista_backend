import math
from django.core.mail import send_mail
from django.db import models
from django.conf import settings
import uuid
from accounts.models import User
from market.models import MarketProperty
from decimal import Decimal, ROUND_HALF_UP
from datetime import timedelta
from django.utils import timezone
from django.template.loader import render_to_string


class PaymentPlan(models.Model):
    PLAN_CHOICES = [
        ('one_time', 'One Time Payment'),
        ('3_months', '3 Months Payment'),
        ('6_months', '6 Months Payment'),
        ('12_months', '12 Months Payment'),
    ]

    name = models.CharField(max_length=20, choices=PLAN_CHOICES, unique=True)
    duration_months = models.PositiveIntegerField(editable=False)
    interest_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00)

    def save(self, *args, **kwargs):
        duration_mapping = {
            'one_time': 0,
            '3_months': 3,
            '6_months': 6,
            '12_months': 12,
        }
        self.duration_months = duration_mapping.get(self.name, 0)
        super().save(*args, **kwargs)

    def __str__(self):
        return dict(self.PLAN_CHOICES).get(self.name, self.name)


class PropertyPurchase(models.Model):
    STATUS_CHOICES = [
        ('created', 'Created'),
        ('canceled', 'Canceled'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed Payment'),
    ]

    id = models.CharField(primary_key=True, max_length=8,
                          unique=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    property = models.ForeignKey(MarketProperty, on_delete=models.CASCADE)
    payment_plan = models.ForeignKey(PaymentPlan, on_delete=models.CASCADE)
    amount_paid = models.DecimalField(
        max_digits=15, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=10, editable=False)
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='created')
    created_at = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(
        max_digits=15, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = uuid.uuid4().hex[:8]
        self.total_amount = self.total_payable_amount()
        self.currency = self.property.currency
        super().save(*args, **kwargs)

    def total_payable_amount(self):
        interest = (self.property.price *
                    self.payment_plan.interest_rate) / Decimal(100)
        return self.property.price + interest

    def monthly_installment(self):
        if self.payment_plan.duration_months > 0:
            return math.ceil(self.total_amount / self.payment_plan.duration_months)
        return math.ceil(self.total_amount)

    def remaining_balance(self):
        return self.total_amount - Decimal(self.amount_paid)

    def apply_payment(self, amount):
        amount = Decimal(amount)
        if self.status == 'completed':
            raise ValueError("Payment already completed for this purchase.")

        if amount <= 0:
            raise ValueError("Payment amount must be greater than zero.")

        if amount > self.remaining_balance():
            raise ValueError("Payment amount exceeds the remaining balance.")

        self.amount_paid += amount

        if self.remaining_balance() == Decimal(0):
            self.status = 'completed'

        self.save()

    def calculate_refund(self):
        total_paid = self.amount_paid
        deduction = total_paid * Decimal(0.10)
        refund_amount = total_paid - deduction
        return refund_amount.quantize(Decimal('1'), rounding=ROUND_HALF_UP)

    def cancel_order(self):
        if self.status in ['completed']:
            raise ValueError("Cannot cancel a completed order.")

        self.status = 'canceled'
        self.save()

        refund = self.calculate_refund()
        return refund

    @staticmethod
    def cancel_expired_orders():
        expiration_date = timezone.now() - timedelta(days=7)
        expired_orders = PropertyPurchase.objects.filter(
            status='created', created_at__lt=expiration_date)

        for order in expired_orders:
            order.status = 'canceled'
            order.save()

            context = {'user': order.user, 'property': order.property}
            subject = "Your Order Has Been Canceled"
            html_message = render_to_string(
                'emails/order_canceled.html', context)
            send_mail(
                subject,
                '',
                f"Realvista <{settings.DEFAULT_FROM_EMAIL}>",
                [order.user.email],
                html_message=html_message,
            )

        return f"{expired_orders.count()} orders were canceled."

    @staticmethod
    def send_reminder_emails():
        reminder_date = timezone.now() - timedelta(days=5)
        expiring_orders = PropertyPurchase.objects.filter(
            status='created', created_at__lt=reminder_date)

        for order in expiring_orders:
            context = {'user': order.user, 'property': order.property}
            subject = "Reminder: Your Order Will Be Canceled Soon"
            html_message = render_to_string(
                'emails/order_reminder.html', context)
            send_mail(
                subject,
                '',
                f"Realvista <{settings.DEFAULT_FROM_EMAIL}>",
                [order.user.email],
                html_message=html_message,
            )

        return f"{expiring_orders.count()} reminder emails sent."

    def __str__(self):
        return f'{self.user} - {self.property} ({self.payment_plan})'


class InstallmentPayment(models.Model):
    purchase = models.ForeignKey(
        PropertyPurchase, on_delete=models.CASCADE, related_name='installments'
    )
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Payment of {self.amount} for {self.purchase}'

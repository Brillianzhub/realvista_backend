from datetime import date, timedelta
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import models
from accounts.models import User
from decimal import Decimal
from realvista_backend.currencies import CURRENCY_DATA


class FinancialTarget(models.Model):

    CURRENCY_CHOICES = [(key, label) for key, label in CURRENCY_DATA.items()]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="financial_targets")
    target_name = models.CharField(
        max_length=255, help_text="Name of the savings goal.")
    target_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal(
        '0.00'), help_text="Total savings goal.")
    current_savings = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal(
        '0.00'), help_text="Amount saved so far.")
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='NGN',
        verbose_name="Currency"
    )
    start_date = models.DateField(
        null=True, blank=True,
        help_text="The date when savings start.")
    end_date = models.DateField(
        null=True, blank=True, help_text="The target completion date.")
    timeframe = models.PositiveIntegerField(
        help_text="The timeframe for achieving the target in years."
    )
    achieved_at = models.DateField(
        null=True, blank=True, help_text="Date when the target was achieved.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def calculate_progress_percentage(self):
        if self.target_amount and self.target_amount > 0:
            return (self.current_savings / self.target_amount) * 100
        return 0

    def calculate_remaining_amount(self):
        if self.target_amount:
            return max(self.target_amount - self.current_savings, Decimal('0.00'))
        return Decimal('0.00')

    def calculate_months_remaining(self):
        today = date.today()
        if not self.end_date or today > self.end_date:
            return 0
        months_remaining = (self.end_date.year - today.year) * \
            12 + self.end_date.month - today.month
        return months_remaining

    def calculate_min_monthly_contribution(self):
        remaining_amount = self.calculate_remaining_amount()
        months_remaining = self.calculate_months_remaining()
        return remaining_amount / months_remaining if months_remaining > 0 else remaining_amount

    def mark_as_achieved(self):
        if self.current_savings >= self.target_amount and not self.achieved_at:
            self.achieved_at = date.today()
            self.save()

    def save(self, *args, **kwargs):
        if not self.start_date:
            self.start_date = date.today()

        if self.timeframe and not self.end_date:
            self.end_date = self.start_date + \
                timedelta(days=self.timeframe * 30 * 12)

        if self.current_savings >= self.target_amount and not self.achieved_at:
            self.mark_as_achieved()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.target_name} (Target: {self.target_amount})"


class Contribution(models.Model):

    CURRENCY_CHOICES = [(key, label) for key, label in CURRENCY_DATA.items()]

    target = models.ForeignKey(
        FinancialTarget, on_delete=models.CASCADE, related_name="contributions")
    amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal(
        '0.00'), help_text="Amount of the contribution.")
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='NGN',
        verbose_name="Currency"
    )
    date = models.DateField(help_text="Date of the contribution.")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Contribution of {self.amount} {self.target.currency} on {self.date} for {self.target.target_name}"


@receiver(post_save, sender=Contribution)
def update_savings_on_save(sender, instance, created, **kwargs):
    if created:
        instance.target.current_savings += instance.amount
        instance.target.save()


@receiver(post_delete, sender=Contribution)
def update_savings_on_delete(sender, instance, **kwargs):
    instance.target.current_savings -= instance.amount
    instance.target.save()

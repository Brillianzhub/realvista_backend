from django.db import models
from accounts.models import User


class Device(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='devices')
    token = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.token


class EmailNotification(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='email_notification', null=True, blank=True
    )
    email = models.EmailField(unique=True, null=True, blank=True)
    receive_email_notifications = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.user:
            return f"Email notifications for {self.user.email}"
        return f"Email notifications for {self.email}"


class Lead(models.Model):
    full_name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20)
    company_name = models.CharField(max_length=150, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name


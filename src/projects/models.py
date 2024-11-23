from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
import random
import string
from django.utils import timezone


def generate_random_number(length=8):
    return ''.join(random.choices('0123456789', k=length))


def generate_project_reference():
    prefix = "RV"
    random_string = ''.join(random.choices(
        string.ascii_uppercase + string.digits, k=6))
    return f"{prefix}-{random_string}-{int(timezone.now().timestamp())}"


class Project(models.Model):
    PROJECT_TYPES = [
        ('House', 'House'),
        ('Land', 'Land'),
    ]

    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Open', 'Open'),
        ('Closed', 'Closed'),
    ]

    CURRENCY_CHOICES = [
        ('NGN', 'NGN'),
        ('EUR', 'EUR'),
        ('USD', 'USD'),
    ]

    name = models.CharField(max_length=200, unique=True)
    project_reference = models.CharField(
        max_length=20, unique=True, editable=False, null=True, blank=True)
    description = models.TextField()
    budget = models.DecimalField(
        max_digits=15, decimal_places=2)
    cost_per_slot = models.DecimalField(
        max_digits=10, decimal_places=2)
    num_slots = models.PositiveIntegerField(blank=True, null=True)
    location = models.CharField(max_length=255)
    type_of_project = models.CharField(max_length=20, choices=PROJECT_TYPES)
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='Draft')
    currency = models.CharField(
        max_length=10, choices=CURRENCY_CHOICES, default="NGN")
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.name

    @property
    def total_cost(self):
        return self.num_slots * self.cost_per_slot


@receiver(pre_save, sender=Project)
def set_num_slots_and_reference(sender, instance, **kwargs):
    if instance.num_slots is None:
        instance.num_slots = round(instance.budget / instance.cost_per_slot)

    if not instance.project_reference:
        location_prefix = instance.location[:2].upper(
        ) if instance.location else "XX"
        random_number = generate_random_number(length=8)
        instance.project_reference = f"RV-{location_prefix}{random_number}"


class ProjectImage(models.Model):
    project = models.ForeignKey(
        Project, related_name='images', on_delete=models.CASCADE)
    image_url = models.URLField()

    def __str__(self):
        return f"Image for {self.project.name}"

from django.db import models


class Project(models.Model):
    PROJECT_TYPES = [
        ('SOLAR', 'Solar'),
        ('WIND', 'Wind'),
        ('REAL_ESTATE', 'Real Estate'),
        ('AGRICULTURE', 'Agriculture'),
        ('TECH', 'Technology'),
        # Add more project types as needed
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('closed', 'Closed'),
    ]

    name = models.CharField(max_length=200, unique=True)
    description = models.TextField()
    budget = models.DecimalField(
        max_digits=15, decimal_places=2)
    cost_per_slot = models.DecimalField(
        max_digits=10, decimal_places=2)
    num_slots = models.PositiveIntegerField()
    location = models.CharField(max_length=255)
    type_of_project = models.CharField(max_length=20, choices=PROJECT_TYPES)
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.name

    @property
    def total_cost(self):
        return self.num_slots * self.cost_per_slot


class ProjectImage(models.Model):
    project = models.ForeignKey(
        Project, related_name='images', on_delete=models.CASCADE)
    image_url = models.URLField()

    def __str__(self):
        return f"Image for {self.project.name}"

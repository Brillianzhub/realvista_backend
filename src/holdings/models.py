from django.db import models
from accounts.models import User
from projects.models import Project


# Create your models here.
class Holding(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='holdings')
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='holdings')
    slots = models.PositiveIntegerField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    payment_confirmed = models.BooleanField(default=False)

    def __str__(self):
        return f"Holding for {self.project.name} - {self.user.name}"

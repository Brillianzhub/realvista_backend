from django.db import models

from django.db import models
from accounts.models import User


class Feedback(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='feedbacks')
    position = models.CharField(max_length=100)
    company = models.CharField(max_length=100)
    feedback = models.TextField()
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.name} - {self.company}"

    @property
    def avatar(self):
        return getattr(self.user.profile, 'avatar', None)

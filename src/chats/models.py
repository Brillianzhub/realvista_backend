from django.db import models
from enterprise.models import CorporateEntity

class ChatMessage(models.Model):
    message_id = models.CharField(
        max_length=255, unique=True, help_text="Unique identifier for the message from the frontend"
    )
    group = models.ForeignKey(
        CorporateEntity, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=255)
    text = models.TextField()
    timestamp = models.DateTimeField()
    reply_to = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL, related_name='replies'
    )
    image = models.URLField(
        max_length=500, null=True, blank=True, help_text="URL of the sender's profile avatar"
    )

    def __str__(self):
        return f"Message by {self.sender} in group {self.group.group_id}: {self.text[:30]}"
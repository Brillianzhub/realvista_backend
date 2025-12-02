from rest_framework import serializers
from .models import ChatMessage


class ChatMessageSerializer(serializers.ModelSerializer):
    reply_to_text = serializers.CharField(
        source='reply_to.text', read_only=True)
    reply_to_sender = serializers.CharField(
        source='reply_to.sender', read_only=True)

    class Meta:
        model = ChatMessage
        fields = ['message_id', 'group', 'image', 'sender', 'text',
                  'timestamp', 'reply_to', 'reply_to_text', 'reply_to_sender']

from django.contrib import admin
from .models import ChatMessage

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('message_id', 'sender', 'group', 'timestamp', 'text_preview', 'reply_to')
    search_fields = ('message_id', 'sender', 'group__name', 'text')
    list_filter = ('group', 'timestamp')
    ordering = ('-timestamp',)
    
    def text_preview(self, obj):
        return obj.text[:50]  # Show the first 50 characters of the message text
    text_preview.short_description = 'Message Preview'

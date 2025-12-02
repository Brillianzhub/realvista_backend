from django.contrib import admin
from .models import ContactMessage


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('fullname', 'email', 'phone_number', 'created_at')
    search_fields = ('fullname', 'email', 'phone_number')
    readonly_fields = ('created_at',)

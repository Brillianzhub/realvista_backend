from .models import EmailNotification
from django.contrib import admin
from .models import Device, Lead


class DeviceAdmin(admin.ModelAdmin):
    list_display = ('user', 'token', 'created_at')
    list_display_links = ('user', 'token')
    search_fields = ('user__name', 'token')


admin.site.register(Device, DeviceAdmin)


@admin.register(EmailNotification)
class EmailNotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'receive_email_notifications', 'created_at')
    search_fields = ('user__email',)
    list_filter = ('receive_email_notifications',)


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'phone_number',
                    'company_name', 'created_at')
    list_filter = ('company_name', 'created_at')
    search_fields = ('full_name', 'email', 'phone_number', 'company_name')
    ordering = ('-created_at',)

    # Optional: Make some fields read-only (timestamps)
    readonly_fields = ('created_at',)

    # Optional: Improve detail view layout
    fieldsets = (
        ("Basic Information", {
            "fields": ("full_name", "email", "phone_number")
        }),
        ("Company Details", {
            "fields": ("company_name", "address")
        }),
        ("Additional Notes", {
            "fields": ("notes",)
        }),
        ("Metadata", {
            "fields": ("created_at",),
        }),
    )

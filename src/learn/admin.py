from django.contrib import admin
from .models import Learn


@admin.register(Learn)
class LearnAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'youtube_id',
                    'duration', 'view_count', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('title', 'description')
    readonly_fields = ('slug', 'youtube_id', 'thumbnail_url', 'created_at')
    ordering = ('-created_at',)
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'category', 'youtube_url', 'duration', 'view_count')
        }),
        ('Auto-Generated Info', {
            'fields': ('slug', 'youtube_id', 'thumbnail_url', 'created_at'),
        }),
    )

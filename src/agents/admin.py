from .models import AgentVerification
from .models import AgentRating
from django.contrib import admin
from .models import Agent


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ('user', 'agency_name',
                    'phone_number', 'verified')
    search_fields = ('user__name', 'agency_name')
    list_filter = ('verified', 'preferred_contact_mode')


@admin.register(AgentRating)
class AgentRatingAdmin(admin.ModelAdmin):
    list_display = ('agent', 'user', 'rating', 'created_at', 'updated_at')
    list_filter = ('rating', 'created_at', 'agent')
    search_fields = ('agent__user__name', 'user__name', 'review')
    raw_id_fields = ('agent', 'user')  # Better for performance with many users
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)


@admin.register(AgentVerification)
class AgentVerificationAdmin(admin.ModelAdmin):
    list_display = ('agent', 'approved', 'reviewed', 'submitted_at')
    list_filter = ('approved', 'reviewed')
    search_fields = ('agent__user__name', 'agent__agency_name')
    readonly_fields = ('submitted_at',)

from django.contrib import admin
from .models import FinancialTarget, Contribution


class ContributionInline(admin.TabularInline):
    model = Contribution
    extra = 1
    readonly_fields = ('created_at',)


@admin.register(FinancialTarget)
class FinancialTargetAdmin(admin.ModelAdmin):
    list_display = ('target_name', 'user', 'target_amount', 'current_savings',
                    'start_date', 'end_date', 'calculate_progress_percentage')

    # Add filters for easier navigation
    list_filter = ('start_date', 'end_date', 'user')

    # Enable searching by goal name or user
    search_fields = ('target_name', 'user__username')

    # Read-only fields (calculated properties)
    readonly_fields = (
        'calculate_progress_percentage', 'calculate_remaining_amount', 'calculate_months_remaining',
        'created_at', 'updated_at', 'minimum_monthly_contribution'
    )

    # Fields grouping for the detail view
    fieldsets = (
        ('Goal Details', {
            'fields': ('user', 'target_name', 'currency', 'target_amount', 'current_savings')
        }),
        ('Timeline', {
            'fields': ('start_date', 'end_date', 'timeframe')
        }),
        ('Progress', {
            'fields': (
                'calculate_progress_percentage', 'calculate_remaining_amount', 'calculate_months_remaining',
                'minimum_monthly_contribution', 'achieved_at'  # Add this to the Progress section
            )
        }),
    )

    def minimum_monthly_contribution(self, obj):
        return obj.calculate_min_monthly_contribution()

    minimum_monthly_contribution.admin_order_field = 'minimum_monthly_contribution'
    ordering = ('-created_at',)
    inlines = [ContributionInline]

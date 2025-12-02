from .models import SubscriptionCancellation
from .models import Payment
from .models import ReferralEarning
from django.contrib import admin
from .models import SubscriptionPlan, UserSubscription, PlanDuration


from django.utils.html import format_html


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'popular', 'display_image', 'created_at')
    search_fields = ('name', 'color', 'image')
    list_filter = ('popular',)
    readonly_fields = ('created_at',)

    def display_image(self, obj):
        if obj.image:
            return format_html('<a href="{}" target="_blank"><img src="{}" width="50" height="50" /></a>', obj.image, obj.image)
        return "No Image"
    display_image.short_description = 'Image'


@admin.register(PlanDuration)
class PlanDurationAdmin(admin.ModelAdmin):
    list_display = ('plan', 'duration_type', 'price',
                    'currency', 'discount_percentage', 'is_active')
    list_filter = ('duration_type', 'currency', 'is_active')
    search_fields = ('plan__name',)
    readonly_fields = ()


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan')
    search_fields = ('user__email', 'user__name')
    list_filter = ('plan',)

    def has_add_permission(self, request):
        return True

    def has_change_permission(self, request, obj=None):
        return bool(obj)


@admin.register(ReferralEarning)
class ReferralEarningAdmin(admin.ModelAdmin):
    list_display = ('referrer', 'referred_user',
                    'subscription', 'amount_earned', 'created_at')
    search_fields = ('referrer__email', 'referred_user__email')
    list_filter = ('created_at',)
    ordering = ('-created_at',)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("user", "plan", "amount", "status",
                    "reference", "date_created")
    list_filter = ("status", "plan")
    search_fields = ("user__email", "reference")
    readonly_fields = ("date_created",)

    def get_queryset(self, request):
        """Ensure the admin sees all payments."""
        return super().get_queryset(request).select_related("user", "plan")

    def user(self, obj):
        return obj.user.email

    user.admin_order_field = "user__email"


@admin.register(SubscriptionCancellation)
class SubscriptionCancellationAdmin(admin.ModelAdmin):
    list_display = ("user", "subscription", "reason", "created_at")
    search_fields = ("user__email", "reason")
    list_filter = ("reason", "created_at")

from django.contrib import admin
from .models import PaymentPlan, PropertyPurchase, InstallmentPayment


@admin.register(PaymentPlan)
class PaymentPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'duration_months', 'interest_rate')
    search_fields = ('name',)


@admin.register(PropertyPurchase)
class PropertyPurchaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'property', 'payment_plan',
                    'amount_paid', 'remaining_balance', 'status', 'created_at')
    search_fields = ('id', 'user__username', 'property__title')
    list_filter = ('payment_plan', 'status', 'created_at')


@admin.register(InstallmentPayment)
class InstallmentPaymentAdmin(admin.ModelAdmin):
    list_display = ('purchase', 'amount', 'timestamp')
    search_fields = ('purchase__id',)
    list_filter = ('timestamp',)

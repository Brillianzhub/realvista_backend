from django.contrib import admin
from .models import BoostPackage, BoostOrder


@admin.register(BoostPackage)
class BoostPackageAdmin(admin.ModelAdmin):
    list_display = ("name", "duration_days", "price")
    search_fields = ("name",)
    list_filter = ("duration_days",)


@admin.register(BoostOrder)
class BoostOrderAdmin(admin.ModelAdmin):
    list_display = ("user", "property", "package",
                    "payment_status", "is_active", "starts_at", "ends_at")
    list_filter = ("payment_status", "is_active", "package")
    search_fields = ("user__email", "property__title",
                     "transaction_reference")

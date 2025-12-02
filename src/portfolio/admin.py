from .models import PropertyValueHistory
from .models import PortfolioPropertyFile
from portfolio.models import CurrencyRate
from .models import Expenses
from .models import Income
from django.contrib import admin
from .models import Property, Coordinate, Income, Expenses

from django.contrib import admin
from .models import Property, PortfolioPropertyImage


class PortfolioPropertyImageAdmin(admin.ModelAdmin):
    list_display = ('property', 'image', 'uploaded_at')
    search_fields = ('property__name',)
    list_filter = ('uploaded_at',)
    ordering = ('-uploaded_at',)


admin.site.register(PortfolioPropertyImage, PortfolioPropertyImageAdmin)


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'owner',
        'status',
        'initial_cost',
        'current_value',
        'slot_price',
        'slot_price_current',
        'user_slots',
        'total_slots',
        'available_slots',
        'year_bought',
    )
    list_filter = (
        'property_type',
        'status',
        'currency',
        'year_bought',
        'added_on'
    )
    search_fields = (
        'title',
        'location',
        'owner__username',
        'owner__email',
        'group_property__title'
    )
    readonly_fields = (
        'slot_price',
        'slot_price_current',
        'available_slots',
        'appreciation',
        'percentage_performance',
        'roi',
        'added_on',
    )
    fieldsets = (
        (None, {
            'fields': ('title', 'owner', 'group_property', 'description')
        }),
        ('Property Details', {
            'fields': (
                'address',
                'location',
                'status',
                'property_type',
                'year_bought',
                'area',
                'num_units',
            )
        }),
        ('Financial Details', {
            'fields': (
                'initial_cost',
                'current_value',
                'currency',
                'slot_price',
                'slot_price_current',
                'total_slots',
                'user_slots',
                'available_slots',
                'appreciation',
                'percentage_performance', 'roi'
            )
        }),
        ('Extras', {
            'fields': ('virtual_tour_url', 'added_on')
        }),
    )
    ordering = ('-added_on', 'location', 'title')

    def available_slots(self, obj):
        """Display available slots in the admin."""
        return obj.available_slots()

    def appreciation(self, obj):
        """Display appreciation in the admin."""
        return obj.appreciation()

    appreciation.short_description = "Appreciation (₦)"
    available_slots.short_description = "Available Slots"


admin.site.register(Coordinate)


@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'property',
        'amount',
        'description',
        'date_received'
    )
    list_filter = (
        'date_received',
        'property',
        'user'
    )
    search_fields = (
        'user__username',
        'user__email',
        'property__title',
        'description'
    )
    ordering = (
        '-date_received',
        'user',
        'property'
    )
    readonly_fields = (
        'user',
        'property',
        'amount',
        'date_received'
    )


@admin.register(Expenses)
class ExpensesAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'property',
        'amount',
        'description',
        'date_incurred'
    )
    list_filter = (
        'date_incurred',
        'property',
        'user'
    )
    search_fields = (
        'user__username',
        'user__email',
        'property__title',
        'description'
    )
    ordering = (
        '-date_incurred',
        'user',
        'property'
    )
    readonly_fields = (
        'user',
        'property',
        'amount',
        'date_incurred'
    )


class CurrencyRateAdmin(admin.ModelAdmin):
    list_display = ('currency_code', 'rate', 'base', 'description')
    search_fields = ('currency_code', 'base')
    ordering = ('currency_code',)
    list_filter = ('currency_code', 'base')
    list_editable = ('rate',)


admin.site.register(CurrencyRate, CurrencyRateAdmin)


@admin.register(PortfolioPropertyFile)
class PortfolioPropertyFileAdmin(admin.ModelAdmin):
    list_display = ('property', 'name', 'file', 'file_type', 'uploaded_at')
    search_fields = ('property__title', 'name', 'file')
    list_filter = ('uploaded_at',)

    def file_type(self, obj):
        return obj.file_type()
    file_type.short_description = "File Type"


@admin.register(PropertyValueHistory)
class PropertyValueHistoryAdmin(admin.ModelAdmin):
    list_display = ('property', 'value', 'recorded_at')
    list_filter = ('recorded_at', 'property')
    search_fields = ('property__title',)
    ordering = ('-recorded_at',)

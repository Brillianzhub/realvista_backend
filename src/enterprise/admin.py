from .models import ReleasedSlot
from .models import GroupCoordinate
from .models import InvitationToken
from django.contrib import admin
from .models import CorporateEntity, GroupPropertyFile, CorporateEntityMember, Payment, GroupSlotAllocation, GroupProperty, GroupIncome, GroupExpenses, GroupPropertyImage


class GroupPropertyImageAdmin(admin.ModelAdmin):
    list_display = ('property', 'image', 'uploaded_at')
    search_fields = ('property__name',)
    list_filter = ('uploaded_at',)
    ordering = ('-uploaded_at',)


admin.site.register(GroupPropertyImage, GroupPropertyImageAdmin)


@admin.register(CorporateEntity)
class CorporateEntityAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'group_id', 'created_at')


@admin.register(CorporateEntityMember)
class CorporateEntityMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'corporate_entity', 'role', 'joined_at')


@admin.register(GroupProperty)
class GroupPropertyAdmin(admin.ModelAdmin):
    list_display = ('title', 'group_owner', 'property_type',
                    'status', 'total_slots', 'slot_price', 'slot_price_current', 'current_value', 'added_on')
    list_filter = ('property_type', 'status', 'group_owner')
    search_fields = ('title', 'location', 'address', 'group_owner__name')
    ordering = ('-added_on',)
    readonly_fields = ('appreciation_display', 'available_slots')

    def appreciation_display(self, obj):
        return obj.appreciation() if obj.appreciation() is not None else "N/A"
    appreciation_display.short_description = "Appreciation"

    def available_slots(self, obj):
        return obj.available_slots()


@admin.register(GroupIncome)
class GroupIncomeAdmin(admin.ModelAdmin):
    list_display = ('property', 'amount', 'date_received', 'description')
    list_filter = ('date_received',)
    search_fields = ('property__title', 'description')


@admin.register(GroupExpenses)
class GroupExpensesAdmin(admin.ModelAdmin):
    list_display = ('property', 'amount', 'date_incurred', 'description')
    list_filter = ('date_incurred',)
    search_fields = ('property__title', 'description')


@admin.register(GroupSlotAllocation)
class GroupSlotAllocationAdmin(admin.ModelAdmin):
    list_display = ('id', 'property', 'user',
                    'slots_owned', 'total_cost', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('property__title', 'user__username', 'user__email')
    ordering = ('-created_at',)
    readonly_fields = ('total_cost',)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'booking', 'user', 'amount_paid',
                    'payment_date', 'payment_status', 'transaction_id')
    list_filter = ('payment_status', 'payment_date')
    search_fields = ('booking__property__title',
                     'user__username', 'transaction_id')
    ordering = ('-payment_date',)
    readonly_fields = ('amount_paid', 'transaction_id')


@admin.register(InvitationToken)
class InvitationTokenAdmin(admin.ModelAdmin):
    list_display = ("token", "email", "corporate_entity",
                    "role", "created_at", "expires_at", "is_expired")
    list_filter = ("corporate_entity", "role", "expires_at")
    search_fields = ("email", "token")
    readonly_fields = ("created_at", "is_expired")

    def is_expired(self, obj):
        return obj.is_expired()
    is_expired.boolean = True


@admin.register(GroupPropertyFile)
class GroupPropertyFileAdmin(admin.ModelAdmin):
    list_display = ('property', 'name', 'file', 'file_type', 'uploaded_at')
    search_fields = ('property__title', 'name', 'file')
    list_filter = ('uploaded_at',)

    def file_type(self, obj):
        return obj.file_type()
    file_type.short_description = "File Type"


admin.site.register(GroupCoordinate)


@admin.register(ReleasedSlot)
class ReleasedSlotAdmin(admin.ModelAdmin):
    list_display = ('user', 'property', 'group',
                    'number_of_slots', 'released_at', 'is_available')
    list_filter = ('is_available', 'released_at')
    search_fields = ('user__email', 'property__name', 'group__name')

# from .models import Referral
from .models import ReferralPayout
from .models import AdminProfile
from .models import Referral
from .models import PasswordResetOTP
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, UserToken, Profile, UserPreference


class UserPreferenceInline(admin.StackedInline):
    model = UserPreference
    can_delete = False
    verbose_name_plural = 'User Preferences'
    fk_name = 'user'


class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'name', 'has_profile',
                    'is_email_verified', 'is_active', 'is_agent', 'is_staff', 'date_joined')
    list_filter = ('is_email_verified', 'is_phone_verified', 'is_active',
                   'is_staff', 'auth_provider')
    search_fields = ('email', 'name')
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal Info'), {
         'fields': ('name', 'first_name', 'referral_code', 'referrer', 'total_referral_earnings')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff',
         'is_superuser', 'is_agent', 'groups', 'user_permissions')}),
        (_('Verification'), {
         'fields': ('is_email_verified', 'is_phone_verified', 'is_identity_verified')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
        (_('Authentication Provider'), {'fields': ('auth_provider',)}),
    )

    readonly_fields = ('date_joined', 'last_login')

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'first_name', 'password1', 'password2'),
        }),
    )

    inlines = [UserPreferenceInline]

    def has_profile(self, obj):
        return Profile.objects.filter(user=obj).exists()

    has_profile.boolean = True
    has_profile.short_description = "Has Profile"


admin.site.register(User, UserAdmin)
admin.site.register(UserToken)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'avatar', 'phone_number', 'country_of_residence')
    search_fields = ('user__email', 'phone_number')


@admin.register(PasswordResetOTP)
class PasswordResetOTPAdmin(admin.ModelAdmin):
    list_display = ('user', 'otp', 'created_at',
                    'expires_at', 'is_valid_display')
    search_fields = ('user__email', 'otp')
    list_filter = ('expires_at',)
    ordering = ('-created_at',)

    def is_valid_display(self, obj):
        return obj.is_valid()
    is_valid_display.boolean = True
    is_valid_display.short_description = "Valid"


class ReferralAdmin(admin.ModelAdmin):
    list_display = ('referrer', 'referred_user', 'created_at')
    list_filter = ('created_at', 'referrer')
    search_fields = ('referrer__email', 'referred_user__email')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)


admin.site.register(Referral, ReferralAdmin)


@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'access_level', 'created_at']
    search_fields = ['user__email', 'role']


@admin.register(ReferralPayout)
class ReferralPayoutAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'payment_method',
                    'status', 'created_at')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('user__email', 'account_details')
    list_editable = ('status',)
    readonly_fields = ('created_at', 'processed_at')
    fieldsets = (
        ('Payout Information', {
            'fields': ('user', 'amount', 'status')
        }),
        ('Payment Details', {
            'fields': ('payment_method', 'account_details')
        }),
        ('Dates', {
            'fields': ('created_at', 'processed_at')
        }),
        ('Admin Notes', {
            'fields': ('admin_notes',),
            'classes': ('collapse',)
        }),
    )
    # actions = ['approve_selected', 'reject_selected', 'mark_as_processed']

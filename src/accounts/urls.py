from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('register_user/', views.register_user, name='register'),
    path('register_google_user/', views.google_sign_in, name='google_sign_in'),
    path('login/apple/', views.apple_sign_in, name='apple_sign_in'),

    path('logout/', views.logout_view, name='logout'),
    path('signin/', views.login_view, name='signin'),
    path('current-user/', views.get_current_user, name='get_current_user'),
    path('verify-email/<int:user_id>/', views.verify_email, name='verify-email'),
    path('resend_token/', views.resend_token, name='resend_token'),
    path('verify-phone/', views.verify_phone, name='verify-phone'),
    path('change-password/', views.ChangePasswordView.as_view(),
         name='change-password'),
    path('submit-referral/', views.submit_referrer_code,
         name='submit_referrer_code'),
    path('password-reset/', views.update_password_reset,
         name='update_password_reset'),
    path('verify-otp/', views.verify_otp,
         name='verify-otp'),
    path('request-password-reset/', views.request_password_reset,
         name='request_password_reset'),
    path('profile/create/', views.user_profile, name='create-profile'),
    path('delete-account/', views.delete_account, name='delete_account'),
    path('user/preferences/', views.UserPreferenceUpdateView.as_view(),
         name='user-preference-update'),
    path('admin-profile/', views.AdminProfileDetailView.as_view(),
         name='admin-profile-detail'),
    path('referrals/payout/',
         views.ReferralPayoutView.as_view(), name='referral-payout'),

    path('referrals/payouts-requests/',
         views.AdminPayoutManagementView.as_view(), name='admin-payout-list'),
    path('referrals/payouts-requests/<int:payout_id>/',
         views.AdminPayoutManagementView.as_view(), name='admin-payout-detail'),
]

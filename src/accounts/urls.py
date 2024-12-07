from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('register_user/', views.register_user, name='register'),
    path('google-signin/', views.google_sign_in, name='google_sign_in'),
    path('logout/', views.logout_view, name='logout'),
    path('signin/', views.login_view, name='signin'),
    path('current-user/', views.get_current_user, name='get_current_user'),
    path('verify-email/<int:user_id>/', views.verify_email, name='verify-email'),
    path('resend_token/', views.resend_token, name='resend_token'),

    path('password-reset/', views.update_password_reset,
         name='update_password_reset'),

    path('request-password-reset/', views.request_password_reset,
         name='request_password_reset'),

    path('delete-account/', views.delete_account, name='delete_account'),

]

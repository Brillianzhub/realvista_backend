from django.urls import path
from . import views

urlpatterns = [
    path('register_user/', views.register_user, name='register'),
    path('google-signin/', views.google_sign_in, name='google_sign_in'),
    path('logout/', views.logout_view, name='logout'),
    path('signin/', views.login_view, name='signin'),
    path('current-user/', views.get_current_user, name='get_current_user'),

    # path('verify-email/', views.verify_email, name='verify_email'),
]

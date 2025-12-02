from django.urls import path
from . import views

urlpatterns = [
    path('register-token/', views.register_token, name='register_token'),
    path('unregister-token/', views.delete_token, name='delete_token'),
    path('send-notification/', views.send_notification, name='send-notification'),
    path('send-general-notification/', views.send_general_notification_view,
         name='send-general-notification'),
    path('groups/<uuid:group_id>/devices/',
         views.get_group_members_devices, name='group_members_devices'),
    path('groups/<uuid:group_id>/admin-devices/',
         views.get_group_admins_devices, name='group_admin_devices'),
    path('get_device/', views.get_device, name='get_device'),
    path('get_user_device/', views.get_user_device, name='get_user_device'),
    path('email-notifications/subscribe/', views.subscribe_email_notifications,
         name='subscribe_email_notifications'),
    path('email-notifications/unsubscribe/', views.unsubscribe_email_notifications,
         name='unsubscribe_email_notifications'),
    path('email-notifications/send/', views.send_email_to_subscribed_users,
         name='send_email_to_subscribed_users'),
    path('create-lead/', views.create_lead, name='create-lead'),
    path('leads/', views.get_all_leads, name='get-all-leads'),
    path('lead/update/<int:pk>/', views.update_lead, name='update-lead'),
    path('lead/delete/<int:pk>/', views.delete_lead, name='delete-lead'),
]

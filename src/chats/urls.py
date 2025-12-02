from django.urls import path
from . import views

urlpatterns = [
    path('messages/', views.ChatMessageView.as_view(),
         name='create_message'),
    path('retrieve-messages/', views.GroupChatMessagesView.as_view(),
         name='retrieve-messages'),
]

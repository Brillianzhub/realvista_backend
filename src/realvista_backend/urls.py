
from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('send-notification/', views.send_push_notification,
         name='send_notification'),
    path('accounts/', include('accounts.urls')),
    path('portfolio/', include('portfolio.urls')),
    path('projects/', include('projects.urls')),
    path('order/', include('order.urls')),
    path('dividends/', include('dividend.urls')),
    path('holdings/', include('holdings.urls')),
    path('notifications/', include('notifications.urls'))
]

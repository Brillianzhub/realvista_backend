
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('portfolio/', include('portfolio.urls')),
    path('projects/', include('projects.urls')),
    path('order/', include('order.urls')),
]


from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('send-notification/', views.send_push_notification,
         name='send_notification'),
    path('update-currency-rates/', views.UpdateCurrencyRatesView.as_view(),
         name='update-currency-rates'),
    path('currencies/', views.CurrencyRateListView.as_view(), name='currency-rates'),
    path('homepage-stats/', views.HomePageStatsView.as_view(), name='homepage-stats'),
    path('accounts/', include('accounts.urls')),
    path('portfolio/', include('portfolio.urls')),
    path('projects/', include('projects.urls')),
    path('order/', include('order.urls')),
    path('dividends/', include('dividend.urls')),
    path('holdings/', include('holdings.urls')),
    path('notifications/', include('notifications.urls')),
    path('market/', include('market.urls')),
    path('purchases/', include('purchases.urls')),
    path('subscriptions/', include('subscriptions.urls')),
    path('course/', include('course.urls')),
    path('contact-us/', include('contact.urls')),
    path('enterprise/', include('enterprise.urls')),
    path('analyser/', include('analyser.urls')),
    path('trends/', include('trends.urls')),
    path('agents/', include('agents.urls')),
    path('boost/', include('boost.urls')),
    path('feedbacks/', include('feedback.urls')),
    path('chats/', include('chats.urls')),
]

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views


urlpatterns = [
    # Trends (read-only for published)
    path('reports/',
         views.ReportViewSet.as_view({'get': 'list'}), name='trend-list'),
    path('reports/<slug:slug>/',
         views.ReportViewSet.as_view({'get': 'retrieve'}), name='trend-detail'),

    path('reports/<slug:slug>/increment-views/',
         views.increment_report_views, name='increment-report-views'),

    # Custom action: increment view count
    path('reports/<slug:slug>/update-views/',
         views.ReportViewSet.as_view({'patch': 'update_views'}), name='trend-update-views'),

    path('get-all-reports/', views.ReportListAPIView.as_view(),
         name='get-all-reports'),
    path('create-trend/', views.create_or_update_report,
         name='create-trend'),
    path('update-trend/<int:pk>/',
         views.create_or_update_report, name='update-trend'),
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('toggle-publish/<int:pk>/',
         views.TogglePublishView.as_view(), name='toggle-publish'),
]

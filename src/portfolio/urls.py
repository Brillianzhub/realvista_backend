from django.urls import path
from . import views
from rest_framework.authtoken.views import obtain_auth_token


urlpatterns = [
    path('properties/add/', views.add_or_update_property, name='add_property'),
    path('property/add-income/', views.add_income, name='add-income'),
    path('property/add-expenses/', views.add_expenses, name='add-expenses'),
    path('delete-property/<int:property_id>/',
         views.delete_property, name='delete-property'),
    path('api-token-auth/', obtain_auth_token, name='api_token_auth'),
    path('properties/', views.get_user_properties, name='get_user_properties'),
    path('user-performance/', views.user_portfolio_summary,
         name='user_portfolio_summary'),


    path('user-property/add-income/',
         views.AddIncomeView.as_view(), name='add-api-income'),
    path('user-property/add-expense/',
         views.AddExpenseView.as_view(), name='add-expense'),
    path('portfolio-analysis/', views.PortfolioAnalysisAPIView.as_view(),
         name='portfolio-analysis'),
    path('property/coordinates/', views.CoordinateBulkCreateAPIView.as_view(),
         name='coordinate-bulk-create'),
    path('upload-portfolio-image/', views.PortfolioPropertyImageUploadView.as_view(),
         name='upload-portfolio-image'),
    path('upload-file-portfolio/', views.PortfolioPropertyFileUploadView.as_view(),
         name='upload-file-portfolio'),

    path('delete-file/<int:file_id>/',
         views.PropertyFileDeleteView.as_view(), name='delete-file'),
    path("coordinate/<int:coordinate_id>/delete/",
         views.delete_coordinate, name="delete-coordinate"),
]

# projects/urls.py
from django.urls import path
from .views import ProjectListView, ProjectDetailView

urlpatterns = [
    path('projects_list/', ProjectListView.as_view(),
         name='project-list'),  # List all projects
    path('<int:id>/', ProjectDetailView.as_view(),
         name='project-detail'),  # Retrieve a project by ID
]

# projects/views.py
from rest_framework import generics
from .models import Project
from .serializers import ProjectSerializer



class ProjectListView(generics.ListAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer


class ProjectDetailView(generics.RetrieveAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    lookup_field = 'id'  # Allows retrieving by project ID

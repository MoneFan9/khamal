from rest_framework import generics, permissions
from .models import Project
from .serializers import ProjectSerializer

class ProjectListCreateAPIView(generics.ListCreateAPIView):
    """
    API view to list and create projects.
    """
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # Automatically set the owner to the current user
        serializer.save(owner=self.request.user)

from .models import Deployment
from .serializers import DeploymentSerializer

class DeploymentListCreateAPIView(generics.ListCreateAPIView):
    """
    API view to list and create deployments.
    """
    queryset = Deployment.objects.all()
    serializer_class = DeploymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(project__owner=self.request.user)

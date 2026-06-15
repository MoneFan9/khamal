from rest_framework import generics, permissions
from .models import Project, Deployment
from .serializers import ProjectSerializer, DeploymentSerializer

class ProjectListCreateAPIView(generics.ListCreateAPIView):
    """
    API view to list and create projects.
    """
    queryset = Project.objects.select_related('owner').only(
        'name', 'owner__username', 'created_at', 'updated_at', 'domain'
    )
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # Automatically set the owner to the current user
        serializer.save(owner=self.request.user)

class DeploymentListCreateAPIView(generics.ListCreateAPIView):
    """
    API view to list and create deployments.
    """
    queryset = Deployment.objects.select_related('project').only(
        'project__name', 'status', 'container_id', 'container_port', 'hot_reload', 'created_at', 'updated_at',
        'project__id' # Required for select_related consistency
    )
    serializer_class = DeploymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Optimization: Reuse optimized queryset with only()
        return self.queryset.filter(project__owner=self.request.user)

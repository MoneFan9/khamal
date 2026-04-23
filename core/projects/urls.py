from django.urls import path
from .api_views import ProjectListCreateAPIView, DeploymentListCreateAPIView

urlpatterns = [
    path('', ProjectListCreateAPIView.as_view(), name='project-list-create'),
    path('deployments/', DeploymentListCreateAPIView.as_view(), name='deployment-list-create'),
]

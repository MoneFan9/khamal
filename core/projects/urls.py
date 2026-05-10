from django.urls import path
from .api_views import ProjectListCreateAPIView, DeploymentListCreateAPIView, LogSageAnalysisAPIView
from .views import deployment_logs_view

urlpatterns = [
    path('', ProjectListCreateAPIView.as_view(), name='project-list-create'),
    path('deployments/', DeploymentListCreateAPIView.as_view(), name='deployment-list-create'),
    path('deployments/<int:deployment_id>/logs/', deployment_logs_view, name='deployment-logs'),
    path('deployments/<int:deployment_id>/analyze/', LogSageAnalysisAPIView.as_view(), name='deployment-analyze'),
]

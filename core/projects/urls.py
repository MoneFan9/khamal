from django.urls import path
from .api_views import ProjectListCreateAPIView

urlpatterns = [
    path('', ProjectListCreateAPIView.as_view(), name='project-list-create'),
]

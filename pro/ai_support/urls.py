from django.urls import path
from .api_views import AIDiagnosticAPIView

urlpatterns = [
    path("diagnose/", AIDiagnosticAPIView.as_view(), name="ai-diagnose"),
]

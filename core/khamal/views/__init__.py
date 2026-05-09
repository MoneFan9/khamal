from django.shortcuts import render
from projects.models import Project

def home(request):
    """
    Main dashboard view.
    """
    projects = []
    if request.user.is_authenticated:
        projects = Project.objects.filter(owner=request.user).prefetch_related('deployments')

    return render(request, "dashboard.html", {"projects": projects})

from django.shortcuts import render
from django.db.models import Prefetch
from projects.models import Project, Deployment

def home(request):
    """
    Main dashboard view.
    """
    projects = []
    if request.user.is_authenticated:
        projects = Project.objects.filter(owner=request.user).only(
            'name', 'domain', 'description', 'updated_at'
        ).prefetch_related(
            Prefetch(
                'deployments',
                queryset=Deployment.objects.only('status', 'project_id')
            )
        )

    return render(request, "dashboard.html", {"projects": projects})

from django.shortcuts import render
from django.db.models import Prefetch
from projects.models import Project, Deployment

def home(request):
    """
    Main dashboard view.
    """
    projects = []
    if request.user.is_authenticated:
        # Optimization: Use .only() to fetch only required fields and limit memory usage.
        # Prefetch deployments with only required fields as well.
        projects = Project.objects.filter(owner=request.user).only(
            'name', 'domain', 'description', 'updated_at'
        ).prefetch_related(
            Prefetch(
                'deployments',
                queryset=Deployment.objects.only('status', 'project_id', 'created_at')
            )
        )

    return render(request, "dashboard.html", {"projects": projects})

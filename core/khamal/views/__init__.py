from django.shortcuts import render
from projects.models import Project

def home(request):
    """
    Main dashboard view.
    """
    projects = []
    stats = {
        'total': 0,
        'running': 0,
        'failed': 0,
    }
    if request.user.is_authenticated:
        projects = Project.objects.filter(owner=request.user).prefetch_related('deployments')
        stats['total'] = projects.count()

        # Optimized to avoid N+1 queries by using prefetched data
        for project in projects:
            # deployments is prefetched, .all() uses the pre-fetched list
            deployments = project.deployments.all()
            last_deployment = deployments[0] if deployments else None
            if last_deployment:
                if last_deployment.status == 'RUNNING':
                    stats['running'] += 1
                elif last_deployment.status == 'FAILED':
                    stats['failed'] += 1

    return render(request, "dashboard.html", {
        "projects": projects,
        "stats": stats
    })

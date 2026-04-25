from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Deployment

@login_required
def deployment_logs_view(request, deployment_id):
    deployment = get_object_or_404(Deployment, id=deployment_id, project__owner=request.user)
    return render(request, 'projects/deployment_logs.html', {'deployment': deployment})

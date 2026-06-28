import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'khamal.settings.development')
django.setup()

from accounts.models import User
from projects.models import Project, Deployment

# Create superuser
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'adminpassword')

# Create some projects
u = User.objects.get(username='admin')
p1, _ = Project.objects.get_or_create(
    name="Site E-commerce",
    owner=u,
    description="Une boutique en ligne moderne propulsée par Khamal.",
    domain="shop.khamal.local"
)
Deployment.objects.get_or_create(project=p1, status='RUNNING')

p2, _ = Project.objects.get_or_create(
    name="API Analytics",
    owner=u,
    description="Service d'analyse de données en temps réel.",
    domain="api.khamal.local"
)
Deployment.objects.get_or_create(project=p2, status='FAILED')

p3, _ = Project.objects.get_or_create(
    name="Blog Personnel",
    owner=u,
    description="Mon blog technique.",
    domain="blog.khamal.local"
)
# No deployment for p3

from pro.white_label.models import WhiteLabelConfiguration
WhiteLabelConfiguration.objects.get_or_create(
    name="Khamal Blue",
    custom_css="body { background-color: #f0f7ff !important; } .btn-primary { background: linear-gradient(to r, #2563eb, #1d4ed8) !important; }",
    is_active=True
)

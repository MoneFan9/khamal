import os
from .views import home
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

# Get hidden admin URL from environment, default to 'admin'
ADMIN_URL = os.environ.get('ADMIN_URL', 'admin')

urlpatterns = [
    path("api/projects/", include("projects.urls")),
    path(f"{ADMIN_URL}/", admin.site.urls),
    path("", home, name="home"),
]

# Only include pro URLs if the package is available and apps are installed
pro_apps = ["pro.white_label", "pro.servers", "pro.ai_support"]
is_pro_available = all(app in settings.INSTALLED_APPS for app in pro_apps)

if is_pro_available:
    urlpatterns += [
        path("api/servers/", include("pro.servers.urls")),
        path("api/pro/ai-support/", include("pro.ai_support.urls")),
    ]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

from .views import home
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("api/projects/", include("projects.urls")),
    path("api/servers/", include("pro.servers.urls")),
    path("api/pro/ai-support/", include("pro.ai_support.urls")),
    path("admin/", admin.site.urls),
    path("", home, name="home"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import ServerViewSet

router = DefaultRouter()
router.register(r'', ServerViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

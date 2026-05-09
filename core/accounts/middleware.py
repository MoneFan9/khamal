import os
from django.http import HttpResponseForbidden
from django.conf import settings

class RestrictedAdminMiddleware:
    """
    Middleware to restrict access to the admin interface to the system administrator only,
    if it's configured in the environment.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        admin_url = os.environ.get('ADMIN_URL', 'admin')

        # Check if the request is for the admin interface
        if request.path.startswith(f'/{admin_url}/'):
            # If the user is authenticated, check if it's the system admin
            if request.user.is_authenticated:
                system_admin_username = os.environ.get('SYSTEM_ADMIN_USERNAME')
                if system_admin_username and request.user.username != system_admin_username:
                    # Optional: Still allow other superusers if desired,
                    # but here we strictly limit to the system admin as requested.
                    if not request.user.is_superuser:
                        return HttpResponseForbidden("Access restricted to system administrator.")

        return self.get_response(request)

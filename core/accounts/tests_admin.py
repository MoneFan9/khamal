import os
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from accounts.middleware import RestrictedAdminMiddleware
from django.http import HttpResponse

User = get_user_model()

class AdminSecurityTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='regular_user', password='password')
        self.sys_admin = User.objects.create_superuser(username='khamal_master', password='password', email='admin@khamal.internal')

        # Mock get_response
        self.get_response = lambda request: HttpResponse("OK")
        self.middleware = RestrictedAdminMiddleware(self.get_response)

    def test_admin_access_restricted_to_sys_admin(self):
        # Set environment variables as they would be in production
        os.environ['ADMIN_URL'] = 'secret-admin'
        os.environ['SYSTEM_ADMIN_USERNAME'] = 'khamal_master'

        # 1. Regular user tries to access admin
        request = self.factory.get('/secret-admin/login/')
        request.user = self.user
        response = self.middleware(request)
        self.assertEqual(response.status_code, 403)

        # 2. System admin tries to access admin
        request = self.factory.get('/secret-admin/login/')
        request.user = self.sys_admin
        response = self.middleware(request)
        self.assertEqual(response.status_code, 200)

        # 3. Accessing non-admin path
        request = self.factory.get('/')
        request.user = self.user
        response = self.middleware(request)
        self.assertEqual(response.status_code, 200)

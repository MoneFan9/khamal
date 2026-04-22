from django.test import TestCase
from django.contrib.auth import get_user_model

class UserModelTest(TestCase):
    def test_create_user(self):
        User = get_user_model()
        user = User.objects.create_user(username="testuser", password="password123")
        self.assertEqual(user.username, "testuser")
        self.assertTrue(user.check_password("password123"))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        User = get_user_model()
        admin_user = User.objects.create_superuser(username="admin", password="password123", email="admin@test.com")
        self.assertEqual(admin_user.username, "admin")
        self.assertTrue(admin_user.is_active)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)

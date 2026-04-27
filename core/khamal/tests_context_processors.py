from django.test import TestCase, override_settings
from unittest.mock import patch
from khamal.context_processors import pro_status

class ContextProcessorsTests(TestCase):
    def test_pro_status_enabled(self):
        """Test pro_status when all apps are in INSTALLED_APPS and pro directory exists."""
        pro_apps = ["pro.white_label", "pro.servers", "pro.ai_support"]
        with override_settings(INSTALLED_APPS=pro_apps):
            with patch('os.path.exists', return_value=True):
                result = pro_status(None)
                self.assertTrue(result['is_pro_loaded'])

    def test_pro_status_missing_apps(self):
        """Test pro_status when some apps are missing from INSTALLED_APPS."""
        with override_settings(INSTALLED_APPS=["pro.white_label"]):
            with patch('os.path.exists', return_value=True):
                result = pro_status(None)
                self.assertFalse(result['is_pro_loaded'])

    def test_pro_status_missing_directory(self):
        """Test pro_status when apps are present but pro directory does not exist."""
        pro_apps = ["pro.white_label", "pro.servers", "pro.ai_support"]
        with override_settings(INSTALLED_APPS=pro_apps):
            with patch('os.path.exists', return_value=False):
                result = pro_status(None)
                self.assertFalse(result['is_pro_loaded'])

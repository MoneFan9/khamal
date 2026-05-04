from django.test import TestCase
from pro.white_label.models import WhiteLabelConfiguration

class WhiteLabelExtendedTests(TestCase):
    def test_configuration_str(self):
        config = WhiteLabelConfiguration.objects.create(name="Custom Branding", is_active=True)
        self.assertEqual(str(config), "Custom Branding")

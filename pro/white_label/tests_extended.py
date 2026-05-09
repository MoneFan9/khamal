from django.test import TestCase
from pro.white_label.models import WhiteLabelConfiguration

class WhiteLabelExtendedTests(TestCase):

    def test_white_label_singleton_active(self):
        # Create first active config
        config1 = WhiteLabelConfiguration.objects.create(name="Config 1", is_active=True)
        self.assertTrue(config1.is_active)

        # Create second active config
        config2 = WhiteLabelConfiguration.objects.create(name="Config 2", is_active=True)
        self.assertTrue(config2.is_active)

        # Refresh config1 and check it's deactivated
        config1.refresh_from_db()
        self.assertFalse(config1.is_active)

        # Create a third inactive config
        config3 = WhiteLabelConfiguration.objects.create(name="Config 3", is_active=False)
        self.assertFalse(config3.is_active)

        # Activate config3
        config3.is_active = True
        config3.save()

        config2.refresh_from_db()
        self.assertFalse(config2.is_active)
        self.assertTrue(config3.is_active)

    def test_str_method(self):
        config = WhiteLabelConfiguration(name="My Theme")
        self.assertEqual(str(config), "My Theme")

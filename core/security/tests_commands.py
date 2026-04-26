from io import StringIO
from django.core.management import call_command
from django.test import SimpleTestCase
from unittest.mock import patch

class USBGuardSetupCommandTests(SimpleTestCase):

    @patch("security.management.commands.usbguard_setup.USBGuardManager")
    def test_usbguard_setup_success(self, mock_manager):
        mock_manager.is_installed.return_value = True
        mock_manager.generate_policy.return_value = "new policy"
        mock_manager.apply_policy.return_value = True

        out = StringIO()
        call_command("usbguard_setup", stdout=out)

        self.assertIn("USBGuard setup successfully with current devices allowed.", out.getvalue())
        mock_manager.apply_policy.assert_called_with("new policy")

    @patch("security.management.commands.usbguard_setup.USBGuardManager")
    def test_usbguard_setup_not_installed(self, mock_manager):
        mock_manager.is_installed.return_value = False

        out = StringIO()
        call_command("usbguard_setup", stderr=out)

        self.assertIn("USBGuard is not installed", out.getvalue())
        mock_manager.generate_policy.assert_not_called()

    @patch("security.management.commands.usbguard_setup.USBGuardManager")
    def test_usbguard_setup_apply_failure(self, mock_manager):
        mock_manager.is_installed.return_value = True
        mock_manager.generate_policy.return_value = "new policy"
        mock_manager.apply_policy.return_value = False

        out = StringIO()
        call_command("usbguard_setup", stderr=out)

        self.assertIn("Failed to apply USBGuard policy", out.getvalue())

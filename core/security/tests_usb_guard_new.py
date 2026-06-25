import pytest
from unittest.mock import patch
from core.security.usb_guard import USBGuardManager

@pytest.mark.django_db
class TestUSBGuardExtra:

    @patch("subprocess.Popen")
    def test_apply_policy_generic_exception(self, mock_popen):
        mock_popen.side_effect = Exception("Unexpected error")

        result = USBGuardManager.apply_policy("allow all")
        assert result is False

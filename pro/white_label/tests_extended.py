"""
PROPRIETARY AND CONFIDENTIAL
This file is part of the Khamal Pro package.
Copyright (c) 2026 Khamal(MoneFan9). All rights reserved.
"""

from django.test import TestCase
from pro.white_label.models import WhiteLabelConfiguration

class WhiteLabelExtendedTests(TestCase):
    def test_str_method(self):
        config = WhiteLabelConfiguration(name="Branding Config")
        assert str(config) == "Branding Config"

    def test_save_is_active_false(self):
        """Test saving a configuration with is_active=False doesn't deactivate others."""
        config1 = WhiteLabelConfiguration.objects.create(name="Active", is_active=True)
        config2 = WhiteLabelConfiguration.objects.create(name="Inactive", is_active=False)

        config1.refresh_from_db()
        assert config1.is_active is True
        assert config2.is_active is False

"""
PROPRIETARY AND CONFIDENTIAL
This file is part of the Khamal Pro package.
Copyright (c) 2026 Khamal(MoneFan9). All rights reserved.
"""

from django.test import TestCase, RequestFactory
from pro.white_label.models import WhiteLabelConfiguration
from pro.white_label.context_processors import white_label

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

    def test_white_label_context_processor(self):
        factory = RequestFactory()
        request = factory.get("/")

        # No config
        context = white_label(request)
        assert context["white_label_config"] is None

        # With active config
        config = WhiteLabelConfiguration.objects.create(name="Enterprise", is_active=True)
        context = white_label(request)
        assert context["white_label_config"] == config

"""
PROPRIETARY AND CONFIDENTIAL
This file is part of the Khamal Pro package.
Copyright (c) 2026 Khamal(MoneFan9). All rights reserved.
"""

from django.test import TestCase, RequestFactory
from .models import WhiteLabelConfiguration
from .context_processors import white_label

class WhiteLabelTests(TestCase):
    def setUp(self):
        self.config1 = WhiteLabelConfiguration.objects.create(
            name="Config 1",
            custom_css="body { background: red; }",
            is_active=True
        )
        self.factory = RequestFactory()

    def test_singleton_active(self):
        """Test that only one configuration can be active at a time."""
        config2 = WhiteLabelConfiguration.objects.create(
            name="Config 2",
            is_active=True
        )
        self.config1.refresh_from_db()
        self.assertFalse(self.config1.is_active)
        self.assertTrue(config2.is_active)

    def test_context_processor(self):
        """Test that the context processor returns the active configuration."""
        request = self.factory.get("/")
        context = white_label(request)
        self.assertEqual(context["white_label_config"], self.config1)

    def test_no_active_config(self):
        """Test context processor when no config is active."""
        self.config1.is_active = False
        self.config1.save()
        request = self.factory.get("/")
        context = white_label(request)
        self.assertIsNone(context["white_label_config"])

    def test_str_representation(self):
        self.assertEqual(str(self.config1), "Config 1")

    def test_save_not_active(self):
        config2 = WhiteLabelConfiguration.objects.create(name="Config 2", is_active=False)
        self.config1.refresh_from_db()
        self.assertTrue(self.config1.is_active)
        self.assertFalse(config2.is_active)

    def test_switch_active_config(self):
        """Test switching active status from one config to another."""
        config2 = WhiteLabelConfiguration.objects.create(name="Config 2", is_active=False)
        self.assertTrue(self.config1.is_active)

        config2.is_active = True
        config2.save()

        self.config1.refresh_from_db()
        self.assertFalse(self.config1.is_active)
        self.assertTrue(config2.is_active)

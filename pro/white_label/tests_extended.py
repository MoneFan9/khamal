"""
PROPRIETARY AND CONFIDENTIAL
This file is part of the Khamal Pro package.
Copyright (c) 2026 Khamal(MoneFan9). All rights reserved.
"""

import pytest
from pro.white_label.models import WhiteLabelConfiguration

@pytest.mark.django_db
def test_str_method():
    config = WhiteLabelConfiguration(name="Branding Config")
    assert str(config) == "Branding Config"

@pytest.mark.django_db
def test_save_is_active_false():
    """Test saving a configuration with is_active=False doesn't deactivate others."""
    config1 = WhiteLabelConfiguration.objects.create(name="Active", is_active=True)
    config2 = WhiteLabelConfiguration.objects.create(name="Inactive", is_active=False)

    config1.refresh_from_db()
    assert config1.is_active is True
    assert config2.is_active is False

@pytest.mark.django_db
def test_white_label_css_injection_order(client):
    """
    Test that the White Label custom CSS is injected after the base styles.
    """
    custom_css = ".custom-class { color: red; }"
    WhiteLabelConfiguration.objects.create(
        name="Test Config",
        custom_css=custom_css,
        is_active=True
    )

    response = client.get("/")
    html = response.content.decode()

    # Check that Tailwind CDN is before custom CSS
    tailwind_index = html.find("cdn.tailwindcss.com")
    custom_css_index = html.find(custom_css)

    assert tailwind_index != -1
    assert custom_css_index != -1
    assert tailwind_index < custom_css_index
    assert '<style id="white-label-css">' in html

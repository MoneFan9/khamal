import pytest
from pro.white_label.models import WhiteLabelConfiguration

@pytest.mark.django_db
def test_white_label_singleton_active():
    # Create first active config
    config1 = WhiteLabelConfiguration.objects.create(name="Config 1", is_active=True)
    assert config1.is_active is True

    # Create second active config, should deactivate first
    config2 = WhiteLabelConfiguration.objects.create(name="Config 2", is_active=True)
    config1.refresh_from_db()
    assert config1.is_active is False
    assert config2.is_active is True

    # Update first to be active again
    config1.is_active = True
    config1.save()
    config2.refresh_from_db()
    assert config1.is_active is True
    assert config2.is_active is False

def test_white_label_str():
    config = WhiteLabelConfiguration(name="My Config")
    assert str(config) == "My Config"

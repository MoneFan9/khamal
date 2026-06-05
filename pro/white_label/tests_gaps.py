import pytest
from pro.white_label.models import WhiteLabelConfiguration

@pytest.mark.django_db
class TestWhiteLabelGaps:

    def test_white_label_configuration_save_active_switch(self):
        # Coverage for white_label/models.py:23-26
        config1 = WhiteLabelConfiguration.objects.create(name="Config 1", is_active=True)
        config2 = WhiteLabelConfiguration.objects.create(name="Config 2", is_active=False)

        assert config1.is_active is True
        assert config2.is_active is False

        # Activate config2, config1 should be deactivated
        config2.is_active = True
        config2.save()

        config1.refresh_from_db()
        assert config1.is_active is False
        assert config2.is_active is True

    def test_white_label_configuration_str(self):
        # Coverage for white_label/models.py:29
        config = WhiteLabelConfiguration(name="My Brand")
        assert str(config) == "My Brand"

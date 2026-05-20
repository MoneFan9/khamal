import pytest
from unittest.mock import MagicMock
from projects.docker_client import HardenedDockerClient

class TestDockerHardeningNew:
    def test_hardened_client_blocks_internal_access(self):
        mock_client = MagicMock()
        hardened = HardenedDockerClient(mock_client)

        with pytest.raises(PermissionError) as excinfo:
            _ = hardened._client
        assert "Security Policy Violation" in str(excinfo.value)

        with pytest.raises(PermissionError) as excinfo:
            _ = hardened.api
        assert "Security Policy Violation" in str(excinfo.value)

    def test_hardened_collection_blocks_internal_access(self):
        from projects.docker_client import HardenedContainerCollection
        mock_collection = MagicMock()
        hardened_coll = HardenedContainerCollection(mock_collection)

        with pytest.raises(PermissionError) as excinfo:
            _ = hardened_coll._collection
        assert "Security Policy Violation" in str(excinfo.value)

        with pytest.raises(PermissionError) as excinfo:
            _ = hardened_coll.api
        assert "Security Policy Violation" in str(excinfo.value)

    def test_hardened_client_blocks_privileged_in_images_pull(self):
        mock_client = MagicMock()
        hardened = HardenedDockerClient(mock_client)

        with pytest.raises(PermissionError) as excinfo:
            hardened.images.pull("alpine", privileged=True)
        assert "forbidden Docker parameter 'privileged'" in str(excinfo.value)

    def test_hardened_client_blocks_cap_add_in_networks_create(self):
        mock_client = MagicMock()
        hardened = HardenedDockerClient(mock_client)

        with pytest.raises(PermissionError) as excinfo:
            hardened.networks.create("my-net", cap_add=["NET_ADMIN"])
        assert "forbidden Docker parameter 'cap_add'" in str(excinfo.value)

    def test_hardened_client_blocks_devices_in_volumes_create(self):
        mock_client = MagicMock()
        hardened = HardenedDockerClient(mock_client)

        with pytest.raises(PermissionError) as excinfo:
            hardened.volumes.create("my-vol", devices=["/dev/sda:/dev/sda"])
        assert "forbidden Docker parameter 'devices'" in str(excinfo.value)

    def test_hardened_client_attribute_delegation(self):
        mock_client = MagicMock()
        mock_client.version.return_value = {"Version": "1.41"}
        hardened = HardenedDockerClient(mock_client)

        # Test delegation via __getattr__
        assert hardened.version() == {"Version": "1.41"}

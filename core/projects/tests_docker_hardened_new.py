import unittest
from unittest.mock import MagicMock, patch
from core.projects.docker_client import HardenedDockerClient, HardenedContainerCollection

class TestHardenedDockerClient(unittest.TestCase):
    def setUp(self):
        self.mock_client = MagicMock()
        self.hardened_client = HardenedDockerClient(self.mock_client)

    def test_block_direct_client_access(self):
        with self.assertRaises(PermissionError) as cm:
            _ = self.hardened_client._client
        self.assertIn("Direct access to low-level Docker API", str(cm.exception))

    def test_block_api_access(self):
        with self.assertRaises(PermissionError) as cm:
            _ = self.hardened_client.api
        self.assertIn("Direct access to low-level Docker API", str(cm.exception))

    def test_delegation_to_client(self):
        self.mock_client.version.return_value = {"Version": "1.2.3"}
        self.assertEqual(self.hardened_client.version(), {"Version": "1.2.3"})

    def test_containers_is_hardened(self):
        self.assertIsInstance(self.hardened_client.containers, HardenedContainerCollection)

class TestHardenedContainerCollection(unittest.TestCase):
    def setUp(self):
        self.mock_collection = MagicMock()
        self.hardened_collection = HardenedContainerCollection(self.mock_collection)

    def test_run_allowed_params(self):
        self.hardened_collection.run("alpine", command="echo hello", detach=True)
        self.mock_collection.run.assert_called_once_with("alpine", command="echo hello", detach=True)

    def test_create_allowed_params(self):
        self.hardened_collection.create("alpine", ports={'80/tcp': 8080})
        self.mock_collection.create.assert_called_once_with("alpine", ports={'80/tcp': 8080})

    def test_block_privileged(self):
        with self.assertRaises(PermissionError) as cm:
            self.hardened_collection.run("alpine", privileged=True)
        self.assertIn("Use of forbidden Docker parameter 'privileged'", str(cm.exception))

    def test_block_cap_add(self):
        with self.assertRaises(PermissionError) as cm:
            self.hardened_collection.create("alpine", cap_add=["NET_ADMIN"])
        self.assertIn("Use of forbidden Docker parameter 'cap_add'", str(cm.exception))

    def test_all_forbidden_params(self):
        forbidden_params = [
            'privileged', 'cap_add', 'security_opt', 'userns_mode',
            'pid_mode', 'group_add', 'oom_kill_disable', 'devices',
            'device_cgroup_rules'
        ]
        for param in forbidden_params:
            with self.subTest(param=param):
                with self.assertRaises(PermissionError):
                    self.hardened_collection.run("alpine", **{param: True})

    def test_forbidden_param_falsey(self):
        # Should NOT raise if value is Falsey
        self.hardened_collection.run("alpine", privileged=False)
        self.hardened_collection.run("alpine", cap_add=None)

    def test_recursive_check(self):
        # Nested parameters that should be blocked
        nested_params = {
            "name": "test",
            "host_config": {
                "privileged": True
            }
        }
        # Note: the current implementation checks keys exactly.
        # In Docker API, it's often 'Privileged' but the check is for 'privileged'.
        # Let's test with the keys defined in the code.
        with self.assertRaises(PermissionError) as cm:
            self.hardened_collection.run("alpine", extra_options={"privileged": True})
        self.assertIn("privileged", str(cm.exception))

    def test_recursive_check_none_dict(self):
        # Test _recursive_check with a non-dict value (it should just return)
        self.hardened_collection._check_security_params({"a": 1})
        # If it reaches here, it passed

    def test_delegation_to_collection(self):
        self.mock_collection.list.return_value = []
        self.assertEqual(self.hardened_collection.list(), [])

    def test_getattribute_special_cases(self):
        # Test that _collection, run, create, _check_security_params are accessed via super()
        # This is mostly to ensure we don't have infinite recursion
        self.assertIsNotNone(self.hardened_collection._collection)
        self.assertIsNotNone(self.hardened_collection.run)
        self.assertIsNotNone(self.hardened_collection.create)
        self.assertIsNotNone(self.hardened_collection._check_security_params)

    @patch("core.projects.docker_client.docker.DockerClient")
    @patch("core.projects.docker_client.settings")
    def test_get_docker_client(self, mock_settings, mock_docker_client):
        from core.projects.docker_client import get_docker_client
        mock_settings.DOCKER_URL = "tcp://127.0.0.1:2375"
        client = get_docker_client()
        self.assertIsInstance(client, HardenedDockerClient)
        mock_docker_client.assert_called_once_with(base_url="tcp://127.0.0.1:2375")

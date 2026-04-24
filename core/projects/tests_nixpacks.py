from django.test import TestCase
from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch, MagicMock, AsyncMock
import json
from .nixpacks import build_image, plan_build, NixpacksError, parse_nixpacks_plan, NixpacksPlan

class NixpacksServiceTest(IsolatedAsyncioTestCase):

    @patch('asyncio.create_subprocess_exec')
    async def test_build_image_success(self, mock_exec):
        # Mock process
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"Build success", b"")
        mock_process.returncode = 0
        mock_exec.return_value = mock_process

        result = await build_image("/path/to/source", image_name="test-image", envs={"KEY": "VALUE"})

        self.assertEqual(result, "Build success")
        mock_exec.assert_called_once()
        args, _ = mock_exec.call_args
        self.assertIn("nixpacks", args)
        self.assertIn("build", args)
        self.assertIn("/path/to/source", args)
        self.assertIn("--name", args)
        self.assertIn("test-image", args)
        self.assertIn("--env", args)
        self.assertIn("KEY=VALUE", args)

    @patch('asyncio.create_subprocess_exec')
    async def test_build_image_failure(self, mock_exec):
        # Mock process failure
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"Build error")
        mock_process.returncode = 1
        mock_exec.return_value = mock_process

        with self.assertRaises(NixpacksError) as cm:
            await build_image("/path/to/source")

        self.assertIn("Build error", str(cm.exception))

    @patch('asyncio.create_subprocess_exec')
    async def test_plan_build_success(self, mock_exec):
        # Mock process
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b'{"plan": "json"}', b"")
        mock_process.returncode = 0
        mock_exec.return_value = mock_process

        result = await plan_build("/path/to/source", envs={"DEBUG": "1"})

        self.assertEqual(result, '{"plan": "json"}')
        mock_exec.assert_called_once()
        args, _ = mock_exec.call_args
        self.assertIn("plan", args)
        self.assertIn("DEBUG=1", args)

    @patch('asyncio.create_subprocess_exec')
    async def test_plan_build_failure(self, mock_exec):
        # Mock process failure
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"Plan error")
        mock_process.returncode = 1
        mock_exec.return_value = mock_process

        with self.assertRaises(NixpacksError) as cm:
            await plan_build("/path/to/source")

        self.assertIn("Plan error", str(cm.exception))

class NixpacksParserTest(IsolatedAsyncioTestCase):
    def test_parse_valid_plan(self):
        plan_json = json.dumps({
            "providers": ["python"],
            "phases": {
                "setup": {
                    "nixPkgs": ["python311", "gcc"],
                    "nixLibs": ["libpq"],
                    "aptPkgs": ["libssl-dev"]
                },
                "install": {
                    "cmds": ["pip install -r requirements.txt", "pip install ."]
                },
                "build": {
                    "cmds": ["python manage.py collectstatic"]
                },
                "start": {
                    "cmd": "gunicorn khamal.wsgi"
                }
            },
            "variables": {
                "DJANGO_SETTINGS_MODULE": "khamal.settings.production",
                "PORT": 8000
            }
        })

        plan = parse_nixpacks_plan(plan_json)

        self.assertIsInstance(plan, NixpacksPlan)
        self.assertEqual(plan.providers, ["python"])
        self.assertEqual(plan.packages, ["python311", "gcc"])
        self.assertEqual(plan.libraries, ["libpq"])
        self.assertEqual(plan.apt_packages, ["libssl-dev"])
        self.assertEqual(plan.install_cmds, ["pip install -r requirements.txt", "pip install ."])
        self.assertEqual(plan.build_cmds, ["python manage.py collectstatic"])
        self.assertEqual(plan.start_cmd, "gunicorn khamal.wsgi")
        self.assertEqual(plan.variables, {"DJANGO_SETTINGS_MODULE": "khamal.settings.production", "PORT": "8000"})

    def test_parse_minimal_plan(self):
        plan_json = json.dumps({})
        plan = parse_nixpacks_plan(plan_json)

        self.assertEqual(plan.providers, [])
        self.assertEqual(plan.packages, [])
        self.assertEqual(plan.install_cmds, [])
        self.assertEqual(plan.start_cmd, None)

    def test_parse_invalid_json(self):
        with self.assertRaises(NixpacksError):
            parse_nixpacks_plan("invalid json")

    def test_type_guards(self):
        # Test that non-list values are handled gracefully
        plan_json = json.dumps({
            "providers": "python",
            "phases": {
                "setup": {
                    "nixPkgs": None,
                }
            },
            "variables": "not a dict"
        })
        plan = parse_nixpacks_plan(plan_json)
        self.assertEqual(plan.providers, [])
        self.assertEqual(plan.packages, [])
        self.assertEqual(plan.variables, {})

class NixpacksDetectionTest(TestCase):
    def test_postgres_detection(self):
        # Exact match
        plan = NixpacksPlan(packages=["postgresql"])
        self.assertTrue(plan.has_postgres)

        # Substring match (e.g. postgresql-15)
        plan = NixpacksPlan(packages=["postgresql-15"])
        self.assertTrue(plan.has_postgres)

        # Precise match for libpq
        plan = NixpacksPlan(libraries=["libpq"])
        self.assertTrue(plan.has_postgres)

        # Case insensitive
        plan = NixpacksPlan(packages=["PostgreSQL"])
        self.assertTrue(plan.has_postgres)

    def test_redis_detection(self):
        # Redis in libraries (previously bugged)
        plan = NixpacksPlan(libraries=["redis"])
        self.assertTrue(plan.has_redis)

        # Substring match
        plan = NixpacksPlan(packages=["redis-server"])
        self.assertTrue(plan.has_redis)

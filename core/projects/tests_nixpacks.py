import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock
from .nixpacks import build_image, plan_build, NixpacksError, parse_nixpacks_plan, NixpacksPlan

class TestNixpacksService:

    @pytest.mark.asyncio
    @patch('asyncio.create_subprocess_exec')
    async def test_build_image_success(self, mock_exec):
        # Mock process
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"Build success", b"")
        mock_process.returncode = 0
        mock_exec.return_value = mock_process

        result = await build_image("/path/to/source", image_name="test-image", envs={"KEY": "VALUE"})

        assert result == "Build success"
        mock_exec.assert_called_once()
        args, _ = mock_exec.call_args
        assert "nixpacks" in args
        assert "build" in args
        assert "/path/to/source" in args
        assert "--name" in args
        assert "test-image" in args
        assert "--env" in args
        assert "KEY=VALUE" in args

    @pytest.mark.asyncio
    @patch('asyncio.create_subprocess_exec')
    async def test_build_image_failure(self, mock_exec):
        # Mock process failure
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"Build error")
        mock_process.returncode = 1
        mock_exec.return_value = mock_process

        with pytest.raises(NixpacksError) as excinfo:
            await build_image("/path/to/source")
        assert "Build error" in str(excinfo.value)

    @pytest.mark.asyncio
    @patch('asyncio.create_subprocess_exec')
    async def test_plan_build_success(self, mock_exec):
        # Mock process
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b'{"plan": "json"}', b"")
        mock_process.returncode = 0
        mock_exec.return_value = mock_process

        result = await plan_build("/path/to/source", envs={"DEBUG": "1"})

        assert result == '{"plan": "json"}'
        mock_exec.assert_called_once()
        args, _ = mock_exec.call_args
        assert "plan" in args
        assert "DEBUG=1" in args

    @pytest.mark.asyncio
    @patch('asyncio.create_subprocess_exec')
    async def test_plan_build_failure(self, mock_exec):
        # Mock process failure
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"Plan error")
        mock_process.returncode = 1
        mock_exec.return_value = mock_process

        with pytest.raises(NixpacksError) as excinfo:
            await plan_build("/path/to/source")
        assert "Plan error" in str(excinfo.value)

    @pytest.mark.asyncio
    @patch('asyncio.create_subprocess_exec')
    async def test_run_nixpacks_command_unexpected_exception(self, mock_exec):
        mock_exec.side_effect = Exception("Spawn failed")
        from .nixpacks import _run_nixpacks_command
        with pytest.raises(NixpacksError) as excinfo:
            await _run_nixpacks_command(["nixpacks", "build", "."], "Nixpacks build")
        assert "Unexpected error" in str(excinfo.value)

class TestNixpacksParser:
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

        assert isinstance(plan, NixpacksPlan)
        assert plan.providers == ["python"]
        assert plan.packages == ["python311", "gcc"]
        assert plan.libraries == ["libpq"]
        assert plan.apt_packages == ["libssl-dev"]
        assert plan.install_cmds == ["pip install -r requirements.txt", "pip install ."]
        assert plan.build_cmds == ["python manage.py collectstatic"]
        assert plan.start_cmd == "gunicorn khamal.wsgi"
        assert plan.variables == {"DJANGO_SETTINGS_MODULE": "khamal.settings.production", "PORT": "8000"}

    def test_parse_minimal_plan(self):
        plan_json = json.dumps({})
        plan = parse_nixpacks_plan(plan_json)

        assert plan.providers == []
        assert plan.packages == []
        assert plan.install_cmds == []
        assert plan.start_cmd is None

    def test_parse_invalid_json(self):
        with pytest.raises(NixpacksError):
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
        assert plan.providers == []
        assert plan.packages == []
        assert plan.variables == {}

class TestNixpacksDetection:
    def test_postgres_detection(self):
        # Exact match
        plan = NixpacksPlan(packages=["postgresql"])
        assert plan.has_postgres is True

        # Substring match (e.g. postgresql-15)
        plan = NixpacksPlan(packages=["postgresql-15"])
        assert plan.has_postgres is True

        # Precise match for libpq
        plan = NixpacksPlan(libraries=["libpq"])
        assert plan.has_postgres is True

        # Case insensitive
        plan = NixpacksPlan(packages=["PostgreSQL"])
        assert plan.has_postgres is True

    def test_redis_detection(self):
        # Redis in libraries
        plan = NixpacksPlan(libraries=["redis"])
        assert plan.has_redis is True

        # Substring match
        plan = NixpacksPlan(packages=["redis-server"])
        assert plan.has_redis is True

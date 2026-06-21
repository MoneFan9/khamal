import pytest
import json
from unittest.mock import patch, AsyncMock
from core.projects.nixpacks import NixpacksPlan, parse_nixpacks_plan, build_image, plan_build, NixpacksError

@pytest.mark.parametrize("packages,expected", [
    (["postgresql"], True),
    (["libpq-dev"], True),
    (["python", "pg"], True),
    (["python", "requests"], False),
    ([], False),
])
def test_nixpacks_plan_has_postgres(packages, expected):
    plan = NixpacksPlan(packages=packages)
    assert plan.has_postgres == expected

@pytest.mark.parametrize("packages,expected", [
    (["redis"], True),
    (["redis-server"], True),
    (["python", "hiredis"], True),
    (["python", "requests"], False),
    ([], False),
])
def test_nixpacks_plan_has_redis(packages, expected):
    plan = NixpacksPlan(packages=packages)
    assert plan.has_redis == expected

def test_nixpacks_plan_from_dict_none():
    data = {
        "providers": None,
        "phases": {
            "setup": {
                "nixPkgs": None,
                "nixLibs": None,
                "aptPkgs": None
            },
            "install": {
                "cmds": None
            },
            "build": {
                "cmds": None
            },
            "start": {
                "cmd": None
            }
        },
        "variables": None
    }
    plan = NixpacksPlan.from_dict(data)
    assert plan.providers == []
    assert plan.packages == []
    assert plan.libraries == []
    assert plan.apt_packages == []
    assert plan.install_cmds == []
    assert plan.build_cmds == []
    assert plan.start_cmd is None
    assert plan.variables == {}

def test_nixpacks_plan_from_dict():
    data = {
        "providers": ["python"],
        "phases": {
            "setup": {
                "nixPkgs": ["python311", "postgresql"],
                "nixLibs": ["openssl"],
                "aptPkgs": ["curl"]
            },
            "install": {
                "cmds": ["pip install -r requirements.txt"]
            },
            "build": {
                "cmds": ["python manage.py collectstatic"]
            },
            "start": {
                "cmd": "python manage.py runserver"
            }
        },
        "variables": {
            "DEBUG": "False"
        }
    }
    plan = NixpacksPlan.from_dict(data)
    assert plan.providers == ["python"]
    assert plan.packages == ["python311", "postgresql"]
    assert plan.libraries == ["openssl"]
    assert plan.apt_packages == ["curl"]
    assert plan.install_cmds == ["pip install -r requirements.txt"]
    assert plan.build_cmds == ["python manage.py collectstatic"]
    assert plan.start_cmd == "python manage.py runserver"
    assert plan.variables == {"DEBUG": "False"}

def test_parse_nixpacks_plan_valid():
    json_data = json.dumps({
        "phases": {"setup": {"nixPkgs": ["python"]}}
    })
    plan = parse_nixpacks_plan(json_data)
    assert plan.packages == ["python"]

def test_parse_nixpacks_plan_invalid():
    with pytest.raises(NixpacksError) as excinfo:
        parse_nixpacks_plan("invalid-json")
    assert "Invalid JSON" in str(excinfo.value)

@pytest.mark.asyncio
@patch("asyncio.create_subprocess_exec")
async def test_build_image(mock_exec):
    mock_process = AsyncMock()
    mock_process.communicate.return_value = (b"Built successfully", b"")
    mock_process.returncode = 0
    mock_exec.return_value = mock_process

    result = await build_image("./path", image_name="test-image", envs={"KEY": "VAL"})

    assert result == "Built successfully"
    mock_exec.assert_called_once()
    args = mock_exec.call_args[0]
    assert "nixpacks" in args
    assert "build" in args
    assert "./path" in args
    assert "--name" in args
    assert "test-image" in args
    assert "--env" in args
    assert "KEY=VAL" in args

@pytest.mark.asyncio
@patch("asyncio.create_subprocess_exec")
async def test_plan_build(mock_exec):
    mock_process = AsyncMock()
    mock_process.communicate.return_value = (b'{"phases": {}}', b"")
    mock_process.returncode = 0
    mock_exec.return_value = mock_process

    result = await plan_build("./path")
    assert result == '{"phases": {}}'
    mock_exec.assert_called_once()

@pytest.mark.asyncio
@patch("asyncio.create_subprocess_exec")
async def test_run_command_failure(mock_exec):
    mock_process = AsyncMock()
    mock_process.communicate.return_value = (b"", b"Error message")
    mock_process.returncode = 1
    mock_exec.return_value = mock_process

    with pytest.raises(NixpacksError) as excinfo:
        await plan_build("./path")
    assert "Nixpacks plan failed: Error message" in str(excinfo.value)

@pytest.mark.asyncio
@patch("asyncio.create_subprocess_exec")
async def test_run_command_unexpected_failure(mock_exec):
    mock_exec.side_effect = RuntimeError("Something went wrong")

    with pytest.raises(NixpacksError) as excinfo:
        await plan_build("./path")
    assert "Unexpected error: Something went wrong" in str(excinfo.value)

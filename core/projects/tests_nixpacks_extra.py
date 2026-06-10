import pytest
import logging
from unittest.mock import patch
from core.projects.nixpacks import NixpacksPlan

def test_nixpacks_plan_from_dict_unexpected_types(caplog):
    """
    Covers lines 111-113 in core/projects/nixpacks.py (unexpected types in _as_list and _as_dict_str).
    """
    data = {
        "providers": "not-a-list",
        "variables": ["not", "a", "dict"],
        "phases": {
            "setup": {
                "nixPkgs": None,
                "nixLibs": 123, # not a list
                "aptPkgs": None
            }
        }
    }

    with caplog.at_level(logging.WARNING):
        plan = NixpacksPlan.from_dict(data)

    assert plan.providers == []
    assert plan.packages == []
    assert plan.libraries == []
    assert plan.variables == {}

    assert "Expected a list but got str" in caplog.text
    assert "Expected a list but got int" in caplog.text
    assert "Expected a dict but got list" in caplog.text

@pytest.mark.asyncio
@patch("asyncio.create_subprocess_exec")
async def test_run_nixpacks_command_unexpected_exception(mock_exec):
    """
    Covers lines 111-113 in core/projects/nixpacks.py (unexpected exception in _run_nixpacks_command).
    """
    from core.projects.nixpacks import _run_nixpacks_command, NixpacksError

    mock_exec.side_effect = Exception("OS level failure")

    with pytest.raises(NixpacksError) as excinfo:
        await _run_nixpacks_command(["nixpacks", "plan"], "Test prefix")

    assert "Unexpected error: OS level failure" in str(excinfo.value)

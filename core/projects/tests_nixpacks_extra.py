import pytest
import asyncio
from unittest.mock import patch, MagicMock
from projects.nixpacks import _run_nixpacks_command, NixpacksError

@pytest.mark.asyncio
async def test_run_nixpacks_command_unexpected_exception():
    """Covers the unexpected exception block in _run_nixpacks_command."""
    with patch("asyncio.create_subprocess_exec") as mock_exec:
        mock_exec.side_effect = Exception("Surprise!")

        with pytest.raises(NixpacksError) as excinfo:
            await _run_nixpacks_command(["nixpacks", "plan", "."], "Test prefix")

        assert "Unexpected error: Surprise!" in str(excinfo.value)

@pytest.mark.asyncio
async def test_run_nixpacks_command_failed_return_code():
    """Covers non-zero return code in _run_nixpacks_command."""
    mock_process = MagicMock()
    mock_process.returncode = 1

    # In asyncio, communicate() is a coroutine
    async def mock_communicate():
        return b"", b"Detailed error message"

    mock_process.communicate = mock_communicate

    with patch("asyncio.create_subprocess_exec", return_value=mock_process):
        with pytest.raises(NixpacksError) as excinfo:
            await _run_nixpacks_command(["nixpacks", "plan", "."], "Test prefix")

        assert "Test prefix failed: Detailed error message" in str(excinfo.value)

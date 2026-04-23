from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch, MagicMock, AsyncMock
from .nixpacks import build_image, plan_build, NixpacksError

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

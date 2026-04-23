import asyncio
import logging
from typing import List, Optional, Dict

logger = logging.getLogger(__name__)

class NixpacksError(Exception):
    """Custom exception for Nixpacks-related errors."""
    pass

async def build_image(
    path: str,
    image_name: Optional[str] = None,
    envs: Optional[Dict[str, str]] = None,
    extra_args: Optional[List[str]] = None
) -> str:
    """
    Asynchronously invokes the Nixpacks CLI to build an image.

    Args:
        path: Path to the source code.
        image_name: Optional name for the resulting Docker image.
        envs: Optional dictionary of environment variables for the build.
        extra_args: Optional list of additional CLI arguments.

    Returns:
        The standard output of the build command.

    Raises:
        NixpacksError: If the build fails.
    """
    cmd = ["nixpacks", "build", path]

    if image_name:
        cmd.extend(["--name", image_name])

    if envs:
        for key, value in envs.items():
            cmd.extend(["--env", f"{key}={value}"])

    if extra_args:
        cmd.extend(extra_args)

    logger.info(f"Running Nixpacks build: {' '.join(cmd)}")

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode().strip()
            logger.error(f"Nixpacks build failed with return code {process.returncode}: {error_msg}")
            raise NixpacksError(f"Nixpacks build failed: {error_msg}")

        return stdout.decode()

    except Exception as e:
        if not isinstance(e, NixpacksError):
            logger.exception("Unexpected error during Nixpacks build")
            raise NixpacksError(f"Unexpected error: {e}")
        raise

async def plan_build(path: str, envs: Optional[Dict[str, str]] = None) -> str:
    """
    Asynchronously invokes 'nixpacks plan' to get the build configuration.

    Args:
        path: Path to the source code.
        envs: Optional dictionary of environment variables.

    Returns:
        The standard output (JSON plan).
    """
    cmd = ["nixpacks", "plan", path]

    if envs:
        for key, value in envs.items():
            cmd.extend(["--env", f"{key}={value}"])

    logger.info(f"Running Nixpacks plan: {' '.join(cmd)}")

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode().strip()
            logger.error(f"Nixpacks plan failed with return code {process.returncode}: {error_msg}")
            raise NixpacksError(f"Nixpacks plan failed: {error_msg}")

        return stdout.decode()

    except Exception as e:
        if not isinstance(e, NixpacksError):
            logger.exception("Unexpected error during Nixpacks plan")
            raise NixpacksError(f"Unexpected error: {e}")
        raise

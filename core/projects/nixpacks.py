import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

class NixpacksError(Exception):
    """Custom exception for Nixpacks-related errors."""
    pass

@dataclass
class NixpacksPlan:
    providers: List[str] = field(default_factory=list)
    packages: List[str] = field(default_factory=list)
    libraries: List[str] = field(default_factory=list)
    apt_packages: List[str] = field(default_factory=list)
    install_cmds: List[str] = field(default_factory=list)
    build_cmds: List[str] = field(default_factory=list)
    start_cmd: Optional[str] = None
    variables: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NixpacksPlan":
        """
        Creates a NixpacksPlan instance from a dictionary.
        """
        phases = data.get("phases", {})
        setup_phase = phases.get("setup", {})
        install_phase = phases.get("install", {})
        build_phase = phases.get("build", {})
        start_phase = phases.get("start", {})

        def _as_list(value: Any) -> List[str]:
            if isinstance(value, list):
                return [str(v) for v in value]
            if value is None:
                return []
            logger.warning("Expected a list but got %s: %r", type(value).__name__, value)
            return []

        def _as_dict_str(value: Any) -> Dict[str, str]:
            if isinstance(value, dict):
                return {str(k): str(v) for k, v in value.items()}
            if value is None:
                return {}
            logger.warning("Expected a dict but got %s: %r", type(value).__name__, value)
            return {}

        return cls(
            providers=_as_list(data.get("providers")),
            packages=_as_list(setup_phase.get("nixPkgs")),
            libraries=_as_list(setup_phase.get("nixLibs")),
            apt_packages=_as_list(setup_phase.get("aptPkgs")),
            install_cmds=_as_list(install_phase.get("cmds")),
            build_cmds=_as_list(build_phase.get("cmds")),
            start_cmd=start_phase.get("cmd") or data.get("start", {}).get("cmd"), # Fallback for some nixpacks versions
            variables=_as_dict_str(data.get("variables"))
        )

def parse_nixpacks_plan(plan_json: str) -> NixpacksPlan:
    """
    Parses the JSON output of 'nixpacks plan' into a NixpacksPlan object.
    """
    try:
        data = json.loads(plan_json)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Nixpacks plan JSON: {e}")
        raise NixpacksError(f"Invalid JSON: {e}")

    return NixpacksPlan.from_dict(data)

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

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

    @property
    def has_postgres(self) -> bool:
        """Detects if PostgreSQL is required."""
        postgres_pkgs = {"postgresql", "libpq", "libpq-dev", "postgresql-client", "pg"}
        all_pkgs = {p.lower() for p in self.packages + self.libraries + self.apt_packages}
        return bool(all_pkgs & postgres_pkgs) or any("postgresql" in p for p in all_pkgs)

    @property
    def has_redis(self) -> bool:
        """Detects if Redis is required."""
        redis_pkgs = {"redis", "redis-server", "hiredis"}
        all_pkgs = {p.lower() for p in self.packages + self.libraries + self.apt_packages}
        return bool(all_pkgs & redis_pkgs) or any("redis-server" in p for p in all_pkgs)

    @property
    def has_mysql(self) -> bool:
        """Detects if MySQL is required."""
        mysql_pkgs = {"mysql", "mysql-client", "mysql-server", "mysql-common", "libmysqlclient-dev", "default-mysql-client"}
        all_pkgs = {p.lower() for p in self.packages + self.libraries + self.apt_packages}
        return bool(all_pkgs & mysql_pkgs) or any("mysql" in p for p in all_pkgs)

    @property
    def has_mongodb(self) -> bool:
        """Detects if MongoDB is required."""
        mongo_pkgs = {"mongodb", "mongodb-clients", "mongodb-server", "mongodb-org"}
        all_pkgs = {p.lower() for p in self.packages + self.libraries + self.apt_packages}
        return bool(all_pkgs & mongo_pkgs) or any("mongodb" in p for p in all_pkgs)

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

async def _run_nixpacks_command(cmd: List[str], error_prefix: str) -> str:
    """
    Runs a Nixpacks command and handles errors.
    """
    logger.info(f"Running Nixpacks command: {' '.join(cmd)}")
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode().strip()
            logger.error(f"{error_prefix} failed (RC {process.returncode}): {error_msg}")
            raise NixpacksError(f"{error_prefix} failed: {error_msg}")

        return stdout.decode()

    except NixpacksError:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error during {error_prefix}")
        raise NixpacksError(f"Unexpected error: {e}") from e

async def build_image(
    path: str,
    image_name: Optional[str] = None,
    envs: Optional[Dict[str, str]] = None,
    extra_args: Optional[List[str]] = None
) -> str:
    """
    Asynchronously invokes the Nixpacks CLI to build an image.
    """
    env_args = [arg for k, v in (envs or {}).items() for arg in ("--env", f"{k}={v}")]
    name_args = ["--name", image_name] if image_name else []
    cmd = ["nixpacks", "build", path, "--cache", *name_args, *env_args, *(extra_args or [])]

    return await _run_nixpacks_command(cmd, "Nixpacks build")

async def plan_build(path: str, envs: Optional[Dict[str, str]] = None) -> str:
    """
    Asynchronously invokes 'nixpacks plan' to get the build configuration.
    """
    env_args = [arg for k, v in (envs or {}).items() for arg in ("--env", f"{k}={v}")]
    cmd = ["nixpacks", "plan", path, *env_args]

    return await _run_nixpacks_command(cmd, "Nixpacks plan")

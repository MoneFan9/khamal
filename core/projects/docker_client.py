import docker
import os
from django.conf import settings

class HardenedContainerCollection:
    def __init__(self, collection):
        self._collection = collection

    def run(self, *args, **kwargs):
        self._check_security_params(kwargs)
        self._check_volumes(kwargs.get('volumes'))
        return self._collection.run(*args, **kwargs)

    def create(self, *args, **kwargs):
        self._check_security_params(kwargs)
        self._check_volumes(kwargs.get('volumes'))
        return self._collection.create(*args, **kwargs)

    def _check_security_params(self, params):
        forbidden_params = {
            'privileged', 'cap_add', 'security_opt', 'userns_mode',
            'pid_mode', 'group_add', 'oom_kill_disable', 'devices',
            'device_cgroup_rules', 'network_mode', 'ipc_mode', 'uts_mode',
            'sysctls'
        }

        def _recursive_check(d):
            if not isinstance(d, dict):
                return
            for key, value in d.items():
                if key in forbidden_params and value:
                    raise PermissionError(f"Security Policy Violation: Use of forbidden Docker parameter '{key}'")
                if isinstance(value, dict):
                    _recursive_check(value)

        _recursive_check(params)

    def _check_volumes(self, volumes):
        """
        Hardens Docker volumes by blocking mounts to sensitive host paths.
        """
        if not volumes:
            return

        forbidden_paths = {
            '/var/run/docker.sock',
            '/etc/shadow',
            '/etc/sudoers',
            '/root',
        }

        def _is_forbidden(host_path):
            try:
                real_host_path = os.path.realpath(host_path)
                for forbidden in forbidden_paths:
                    if real_host_path == forbidden or real_host_path.startswith(forbidden + os.sep):
                        return True
            except Exception:
                return True # Fail secure
            return False

        if isinstance(volumes, list):
            for vol in volumes:
                if isinstance(vol, str):
                    host_path = vol.split(':')[0]
                    if _is_forbidden(host_path):
                        raise PermissionError(f"Security Policy Violation: Forbidden volume mount '{host_path}'")
        elif isinstance(volumes, dict):
            for host_path in volumes.keys():
                if _is_forbidden(host_path):
                    raise PermissionError(f"Security Policy Violation: Forbidden volume mount '{host_path}'")

    def __getattribute__(self, name):
        if name in ['_collection', 'run', 'create', '_check_security_params', '_check_volumes']:
            return super().__getattribute__(name)
        return getattr(self._collection, name)

class HardenedDockerClient:
    def __init__(self, client):
        self._client = client
        self.containers = HardenedContainerCollection(client.containers)

    def __getattribute__(self, name):
        if name in ['api', '_client']:
             raise PermissionError(f"Security Policy Violation: Direct access to low-level Docker API '{name}' is restricted.")
        return super().__getattribute__(name)

    def __getattr__(self, name):
        return getattr(self._client, name)

def get_docker_client():
    """
    Returns a Docker client connected via the security proxy.

    Architectural Security Note:
    Khamal does NOT connect directly to /var/run/docker.sock for deployment operations.
    Instead, it communicates with 'docker-socket-proxy' (Tecnativa).

    This proxy acts as an Application Level Firewall for the Docker API:
    1. It blocks all requests by default.
    2. We only enable specific read/write capabilities (CONTAINERS, NETWORKS, IMAGES, VOLUMES).
    3. It prevents 'privileged=True' or 'cap_add' escalations at the proxy level.
    4. It binds to 127.0.0.1 to prevent external API exposure.
    """
    client = docker.DockerClient(base_url=settings.DOCKER_URL)
    return HardenedDockerClient(client)

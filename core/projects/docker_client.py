import docker
import os
from django.conf import settings

class HardenedContainerCollection:
    def __init__(self, collection):
        self._collection = collection

    def run(self, *args, **kwargs):
        self._check_security_params(kwargs)
        return self._collection.run(*args, **kwargs)

    def create(self, *args, **kwargs):
        self._check_security_params(kwargs)
        return self._collection.create(*args, **kwargs)

    def _check_security_params(self, params):
        forbidden_params = {
            'privileged', 'cap_add', 'security_opt', 'userns_mode',
            'pid_mode', 'group_add', 'oom_kill_disable', 'devices',
            'device_cgroup_rules', 'network_mode', 'ipc_mode', 'uts_mode',
            'sysctls'
        }

        # Block sensitive volume mounts
        forbidden_mounts = {
            '/var/run/docker.sock',
            '/etc/shadow',
            '/etc/sudoers',
            '/root',
            '/etc/passwd',
            '/etc/docker',
            '/var/lib/docker'
        }

        def _is_forbidden(path):
            try:
                real_path = os.path.realpath(path)
                for forbidden in forbidden_mounts:
                    forbidden_real = os.path.realpath(forbidden)
                    # Check if the path is exactly the forbidden path or a parent/child of it
                    if real_path == forbidden_real or \
                       real_path.startswith(forbidden_real + os.sep) or \
                       forbidden_real.startswith(real_path + os.sep):
                        return True, forbidden
            except Exception:
                pass
            return False, None

        def _check_volumes(volumes):
            if not volumes:
                return

            # volumes can be:
            # 1. a list: ['/host:/container:ro']
            # 2. a dict: {'/host': {'bind': '/container', 'mode': 'ro'}}
            # 3. a list of docker.types.Mount objects

            if isinstance(volumes, list):
                for mount in volumes:
                    if isinstance(mount, str):
                        host_path = mount.split(':')[0]
                    elif hasattr(mount, 'get'): # dictionary-like
                        host_path = mount.get('Source') or mount.get('source')
                    elif hasattr(mount, 'source'): # Mount object
                        host_path = mount.source
                    else:
                        continue

                    forbidden, reason = _is_forbidden(host_path)
                    if forbidden:
                        raise PermissionError(f"Security Policy Violation: Mounting sensitive host path '{host_path}' (resolved to '{reason}') is forbidden.")

            elif isinstance(volumes, dict):
                for host_path in volumes.keys():
                    forbidden, reason = _is_forbidden(host_path)
                    if forbidden:
                        raise PermissionError(f"Security Policy Violation: Mounting sensitive host path '{host_path}' (resolved to '{reason}') is forbidden.")

        def _recursive_check(d):
            if not isinstance(d, dict):
                return
            for key, value in d.items():
                if key in forbidden_params and value:
                    raise PermissionError(f"Security Policy Violation: Use of forbidden Docker parameter '{key}'")

                if key in ('volumes', 'mounts'):
                    _check_volumes(value)

                if isinstance(value, dict):
                    _recursive_check(value)

        _recursive_check(params)

    def __getattribute__(self, name):
        if name in ['_collection', 'run', 'create', '_check_security_params']:
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

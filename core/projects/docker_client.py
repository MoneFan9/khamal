import docker
from django.conf import settings

class HardenedBaseCollection:
    """
    Proxy for Docker SDK collections (containers, images, etc.) that
    enforces security policies on all creation/execution methods.
    """
    def __init__(self, collection):
        self._collection = collection

    def _check_security_params(self, params):
        forbidden_params = {
            'privileged', 'cap_add', 'security_opt', 'userns_mode',
            'pid_mode', 'group_add', 'oom_kill_disable', 'devices',
            'device_cgroup_rules'
        }

        def _recursive_check(d):
            if not isinstance(d, dict):
                return
            for key, value in d.items():
                # 1. Block forbidden parameters
                if key in forbidden_params and value:
                    raise PermissionError(f"Security Policy Violation: Use of forbidden Docker parameter '{key}'")

                # 2. Block sensitive volume mounts (e.g., docker.sock)
                if key in ['volumes', 'mounts'] and value:
                    volumes_str = str(value)
                    if 'docker.sock' in volumes_str or '/var/run' in volumes_str:
                         raise PermissionError(f"Security Policy Violation: Mounting sensitive host paths is forbidden: {key}")

                if isinstance(value, dict):
                    _recursive_check(value)

        _recursive_check(params)

    def __getattribute__(self, name):
        # Prevent recursion and allow access to internal proxy state
        if name in ['_collection', '_check_security_params', '__dict__', '_wrap_result']:
            return object.__getattribute__(self, name)

        # 3. Block access to internal client/collection to prevent bypass
        if name in ['client', 'collection']:
             raise PermissionError(f"Security Policy Violation: Access to underlying Docker SDK objects '{name}' is restricted.")

        attr = getattr(object.__getattribute__(self, '_collection'), name)

        if callable(attr):
            def hardened_method(*args, **kwargs):
                self._check_security_params(kwargs)
                result = attr(*args, **kwargs)
                return self._wrap_result(result)
            return hardened_method

        return attr

    def _wrap_result(self, result):
        # Recursively wrap results if they are lists or iterables
        if isinstance(result, list):
            return [self._wrap_result(item) for item in result]

        # To be overridden by subclasses if results need wrapping (e.g. Container objects)
        return result

class HardenedContainer:
    """
    Proxy for Docker Container objects that ensures methods like exec_run
    cannot be used to escalate privileges.
    """
    def __init__(self, container):
        self._container = container

    def exec_run(self, *args, **kwargs):
        # We reuse the same security check as collections
        proxy = HardenedBaseCollection(None)
        proxy._check_security_params(kwargs)
        return self._container.exec_run(*args, **kwargs)

    def __getattribute__(self, name):
        if name in ['_container', 'exec_run', '__dict__']:
            return object.__getattribute__(self, name)

        # Block access to internal client to prevent bypass
        if name == 'client':
             raise PermissionError("Security Policy Violation: Access to underlying Docker client via Container is restricted.")

        return getattr(object.__getattribute__(self, '_container'), name)

class HardenedContainerCollection(HardenedBaseCollection):
    def _wrap_result(self, result):
        if isinstance(result, list):
            return [self._wrap_result(item) for item in result]

        from docker.models.containers import Container
        if isinstance(result, Container) or (hasattr(result, '__class__') and result.__class__.__name__ == 'Container'):
            return HardenedContainer(result)
        return result

class HardenedDockerClient:
    def __init__(self, client):
        self._client = client
        # Explicitly harden all collections
        self.containers = HardenedContainerCollection(client.containers)
        self.images = HardenedBaseCollection(client.images)
        self.networks = HardenedBaseCollection(client.networks)
        self.volumes = HardenedBaseCollection(client.volumes)
        self.plugins = HardenedBaseCollection(client.plugins)
        self.nodes = HardenedBaseCollection(client.nodes)
        self.services = HardenedBaseCollection(client.services)
        self.swarm = HardenedBaseCollection(client.swarm)
        self.configs = HardenedBaseCollection(client.configs)
        self.secrets = HardenedBaseCollection(client.secrets)

    def __getattribute__(self, name):
        # 1. Prevent access to low-level API or internal client
        if name in ['api', '_client']:
             raise PermissionError(f"Security Policy Violation: Direct access to low-level Docker API '{name}' is restricted.")

        # 2. Return hardened collections if they exist in __dict__
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            pass

        # 3. For any other attribute, try to get it from the internal client
        # and wrap it if it's a collection we missed, or just return it.
        attr = getattr(object.__getattribute__(self, '_client'), name)
        return attr

    def __getattr__(self, name):
        # This is a fallback for attributes not found via __getattribute__
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

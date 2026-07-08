import docker
from django.conf import settings

class HardenedContainer:
    def __init__(self, container):
        self._container = container

    def exec_run(self, *args, **kwargs):
        forbidden_exec_params = {'privileged', 'user'}
        for key in kwargs:
            if key.lower() in forbidden_exec_params and kwargs[key]:
                raise PermissionError(f"Security Policy Violation: Use of forbidden Docker exec parameter '{key}'")
        return self._container.exec_run(*args, **kwargs)

    def __getattribute__(self, name):
        if name in ['_container', 'exec_run']:
            return super().__getattribute__(name)
        return getattr(self._container, name)

class HardenedContainerCollection:
    def __init__(self, collection):
        self._collection = collection

    def run(self, *args, **kwargs):
        self._check_security_params(kwargs)
        container = self._collection.run(*args, **kwargs)
        if hasattr(container, 'exec_run'):
            return HardenedContainer(container)
        return container

    def create(self, *args, **kwargs):
        self._check_security_params(kwargs)
        container = self._collection.create(*args, **kwargs)
        return HardenedContainer(container)

    def get(self, *args, **kwargs):
        container = self._collection.get(*args, **kwargs)
        return HardenedContainer(container)

    def list(self, *args, **kwargs):
        containers = self._collection.list(*args, **kwargs)
        return [HardenedContainer(c) for c in containers]

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
                if key.lower() in forbidden_params and value:
                    raise PermissionError(f"Security Policy Violation: Use of forbidden Docker parameter '{key}'")
                if isinstance(value, dict):
                    _recursive_check(value)

        _recursive_check(params)

    def __getattribute__(self, name):
        if name in ['_collection', 'run', 'create', 'get', 'list', '_check_security_params']:
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

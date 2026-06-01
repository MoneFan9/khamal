import docker
from django.conf import settings

class HardenedContainer:
    def __init__(self, container):
        self._container = container

    def exec_run(self, *args, **kwargs):
        # Prevent privilege escalation in exec_run
        if kwargs.get('privileged'):
            raise PermissionError("Security Policy Violation: 'privileged=True' is forbidden in exec_run")
        return self._container.exec_run(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._container, name)

class HardenedBaseCollection:
    def __init__(self, collection):
        self._collection = collection

    def get(self, *args, **kwargs):
        obj = self._collection.get(*args, **kwargs)
        if isinstance(obj, docker.models.containers.Container):
            return HardenedContainer(obj)
        return obj

    def list(self, *args, **kwargs):
        objs = self._collection.list(*args, **kwargs)
        return [HardenedContainer(o) if isinstance(o, docker.models.containers.Container) else o for o in objs]

    def __getattr__(self, name):
        return getattr(self._collection, name)

class HardenedContainerCollection(HardenedBaseCollection):
    def run(self, *args, **kwargs):
        self._check_security_params(kwargs)
        container = self._collection.run(*args, **kwargs)
        if isinstance(container, docker.models.containers.Container):
            return HardenedContainer(container)
        return container

    def create(self, *args, **kwargs):
        self._check_security_params(kwargs)
        container = self._collection.create(*args, **kwargs)
        if isinstance(container, docker.models.containers.Container):
            return HardenedContainer(container)
        return container

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
                if key in forbidden_params and value:
                    raise PermissionError(f"Security Policy Violation: Use of forbidden Docker parameter '{key}'")

                # Check for sensitive host mounts
                if key == 'volumes' and isinstance(value, dict):
                    for host_path in value.keys():
                        if any(sensitive in host_path for sensitive in ['docker.sock', '/var/run']):
                             raise PermissionError(f"Security Policy Violation: Forbidden host mount detected: {host_path}")

                if isinstance(value, dict):
                    _recursive_check(value)

        _recursive_check(params)

class HardenedDockerClient:
    def __init__(self, client):
        self._client = client
        self.containers = HardenedContainerCollection(client.containers)
        self.networks = HardenedBaseCollection(client.networks)
        self.volumes = HardenedBaseCollection(client.volumes)
        self.images = HardenedBaseCollection(client.images)

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

import docker
from django.conf import settings

class HardenedContainerCollection:
    """
    A security-focused wrapper around Docker's container collection.

    This class intercepts 'run' and 'create' calls to enforce systemic security policies.
    It prevents the use of dangerous parameters that could lead to container escape
    or host compromise.
    """
    def __init__(self, collection):
        self._collection = collection

    def run(self, *args, **kwargs):
        """
        Intercepts container run calls to validate security parameters.
        """
        self._check_security_params(kwargs)
        return self._collection.run(*args, **kwargs)

    def create(self, *args, **kwargs):
        """
        Intercepts container create calls to validate security parameters.
        """
        self._check_security_params(kwargs)
        return self._collection.create(*args, **kwargs)

    def _check_security_params(self, params):
        """
        Validates that no forbidden security-sensitive parameters are used.

        Forbidden parameters include:
        - privileged: Grants all capabilities to the container.
        - cap_add: Allows adding specific dangerous capabilities.
        - devices: Prevents direct access to host hardware devices.
        - security_opt: Prevents overriding default security profiles (AppArmor/Seccomp).
        """
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
                if isinstance(value, dict):
                    _recursive_check(value)

        _recursive_check(params)

    def __getattribute__(self, name):
        # Allow access to our own methods and the wrapped collection
        if name in ['_collection', 'run', 'create', '_check_security_params']:
            return super().__getattribute__(name)
        # Proxy other attribute access to the underlying collection
        return getattr(self._collection, name)

class HardenedDockerClient:
    """
    A hardened version of the DockerClient.

    This client restricts access to low-level APIs and ensures that all container
    operations are routed through the HardenedContainerCollection.
    """
    def __init__(self, client):
        self._client = client
        self.containers = HardenedContainerCollection(client.containers)

    def __getattribute__(self, name):
        """
        Prevents direct access to dangerous low-level attributes.
        """
        if name in ['api', '_client']:
             raise PermissionError(f"Security Policy Violation: Direct access to low-level Docker API '{name}' is restricted.")
        return super().__getattribute__(name)

    def __getattr__(self, name):
        """
        Proxies safe attribute access to the underlying Docker client.
        """
        # We use super().__getattribute__('_client') to bypass our own
        # __getattribute__ check, allowing the proxying to function correctly.
        inner_client = super().__getattribute__('_client')
        return getattr(inner_client, name)

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

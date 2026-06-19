import docker
from django.conf import settings

class HardenedContainerCollection:
    """
    Proxy for the Docker containers collection that enforces security policies.
    It intercepts 'run' and 'create' calls to prevent use of dangerous parameters.
    """
    def __init__(self, collection):
        self._collection = collection

    def run(self, *args, **kwargs):
        self._check_security_params(kwargs)
        return self._collection.run(*args, **kwargs)

    def create(self, *args, **kwargs):
        self._check_security_params(kwargs)
        return self._collection.create(*args, **kwargs)

    def _check_security_params(self, params):
        """
        Recursively checks parameters for forbidden Docker options that could
        lead to host compromise or privilege escalation.
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
        # Ensure we use our hardened versions of run/create
        if name in ['_collection', 'run', 'create', '_check_security_params']:
            return super().__getattribute__(name)
        # Proxy everything else to the underlying collection
        return getattr(self._collection, name)

class HardenedDockerClient:
    """
    A security-focused wrapper around the Docker SDK client.

    Architectural Security Principle:
    We restrict access to low-level APIs ('api', '_client') and wrap high-level
    collections (like 'containers') with hardening logic.
    """
    def __init__(self, client):
        self._client = client
        self.containers = HardenedContainerCollection(client.containers)

    def __getattribute__(self, name):
        # Block direct access to the underlying client or low-level API to prevent bypasses.
        if name in ['api', '_client']:
             raise PermissionError(f"Security Policy Violation: Direct access to low-level Docker API '{name}' is restricted.")
        return super().__getattribute__(name)

    def __getattr__(self, name):
        # Delegate other attribute access to the underlying client
        return getattr(self._client, name)

def get_docker_client():
    """
    Returns a Hardened Docker client.

    Architectural Security Note:
    Khamal does NOT connect directly to /var/run/docker.sock for deployment operations.
    Instead, it communicates with 'docker-socket-proxy' (Tecnativa).

    This proxy acts as an Application Level Firewall for the Docker API:
    1. It blocks all requests by default.
    2. We only enable specific read/write capabilities (CONTAINERS, NETWORKS, IMAGES, VOLUMES).
    3. It prevents 'privileged=True' or 'cap_add' escalations at the proxy level.
    4. It binds to 127.0.0.1 to prevent external API exposure.

    The HardenedDockerClient adds a second layer of defense-in-depth within the application code.
    """
    client = docker.DockerClient(base_url=settings.DOCKER_URL)
    return HardenedDockerClient(client)

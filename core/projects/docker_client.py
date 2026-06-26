import docker
from django.conf import settings

class HardenedContainerCollection:
    """
    Wrapper for Docker's container collection to enforce security policies.
    """
    def __init__(self, collection):
        self._collection = collection

    def run(self, *args, **kwargs):
        """
        Hardened run method that checks for forbidden parameters before execution.
        """
        self._check_security_params(kwargs)
        return self._collection.run(*args, **kwargs)

    def create(self, *args, **kwargs):
        """
        Hardened create method that checks for forbidden parameters before creation.
        """
        self._check_security_params(kwargs)
        return self._collection.create(*args, **kwargs)

    def _check_security_params(self, params):
        """
        Enforces a 'No-Escalation' policy by blocking dangerous Docker parameters.

        Blocked parameters:
        - privileged: Prevents the container from having all host root capabilities.
        - cap_add: Prevents adding specific Linux capabilities.
        - security_opt: Prevents overriding default security profiles (AppArmor, Seccomp).
        - userns_mode: Prevents host user namespace sharing.
        - pid_mode: Prevents host PID namespace sharing.
        - devices: Prevents direct access to host devices.
        """
        forbidden_params = {
            'privileged', 'cap_add', 'security_opt', 'userns_mode',
            'pid_mode', 'group_add', 'oom_kill_disable', 'devices',
            'device_cgroup_rules', 'network_mode', 'ipc_mode', 'uts_mode', 'sysctls'
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
        # Ensure we use our hardened methods if they exist, otherwise proxy to the original collection.
        if name in ['_collection', 'run', 'create', '_check_security_params']:
            return super().__getattribute__(name)
        return getattr(self._collection, name)

class HardenedDockerClient:
    """
    Security-first Docker client wrapper for Project Khamal.

    This client prevents direct access to low-level 'api' and '_client' attributes
    to force use of higher-level, hardened abstractions.
    """
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

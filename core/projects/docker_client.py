import docker
from django.conf import settings

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
    return docker.DockerClient(base_url=settings.DOCKER_URL)

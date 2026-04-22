import docker
from django.conf import settings

def get_docker_client():
    """
    Returns a Docker client connected via the security proxy.
    The proxy (docker-socket-proxy) should be configured to only allow
    the necessary operations (least privilege).
    """
    return docker.DockerClient(base_url=settings.DOCKER_URL)

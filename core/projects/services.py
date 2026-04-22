from .docker_client import get_docker_client
from .models import Project, Deployment
import logging
import docker

logger = logging.getLogger(__name__)

PROXY_NETWORK_NAME = "khamal-proxy"
TRAEFIK_CONTAINER_NAME = "khamal-traefik"
TRAEFIK_IMAGE = "traefik:v3.1"

def ensure_global_proxy():
    """
    Ensures the global Traefik proxy and its network exist.
    """
    client = get_docker_client()

    # Ensure proxy network exists
    try:
        client.networks.get(PROXY_NETWORK_NAME)
    except docker.errors.NotFound:
        logger.info(f"Creating global proxy network: {PROXY_NETWORK_NAME}")
        client.networks.create(
            PROXY_NETWORK_NAME,
            driver="bridge",
            labels={"khamal.managed": "true"}
        )

    # Ensure Traefik container exists and is running
    try:
        container = client.containers.get(TRAEFIK_CONTAINER_NAME)
        if container.status != "running":
            logger.info(f"Starting existing Traefik container: {TRAEFIK_CONTAINER_NAME}")
            container.start()
    except docker.errors.NotFound:
        logger.info(f"Creating and starting Traefik container: {TRAEFIK_CONTAINER_NAME}")
        client.containers.run(
            TRAEFIK_IMAGE,
            name=TRAEFIK_CONTAINER_NAME,
            detach=True,
            restart_policy={"Name": "always"},
            network=PROXY_NETWORK_NAME,
            ports={
                '80/tcp': 80,
                '443/tcp': 443,
                '8080/tcp': 8080
            },
            volumes={
                '/var/run/docker.sock': {'bind': '/var/run/docker.sock', 'mode': 'ro'}
            },
            command=[
                "--api.insecure=true",
                "--providers.docker=true",
                "--providers.docker.exposedbydefault=false",
                f"--providers.docker.network={PROXY_NETWORK_NAME}",
                "--entrypoints.web.address=:80",
                "--entrypoints.websecure.address=:443",
            ],
            labels={"khamal.managed": "true"}
        )

def ensure_project_network(project: Project) -> str:
    """
    Ensures an isolated bridge network exists for the project.
    Returns the network ID.
    """
    client = get_docker_client()

    # If project already has a network_id, check if it still exists
    if project.network_id:
        try:
            client.networks.get(project.network_id)
            return project.network_id
        except Exception:
            logger.warning(f"Network {project.network_id} for project {project.name} not found, recreating.")
            project.network_id = None

    # Create a new bridge network
    # Format: khamal-project-<id>-<name>
    network_name = f"khamal-project-{project.id}-{project.name.replace(' ', '-')}"

    try:
        # Check if network with this name already exists (e.g. from a previous crash)
        networks = client.networks.list(names=[network_name])
        if networks:
            network = networks[0]
        else:
            network = client.networks.create(
                network_name,
                driver="bridge",
                labels={
                    "khamal.project.id": str(project.id),
                    "khamal.managed": "true"
                },
                check_duplicate=True
            )

        project.network_id = network.id
        project.save(update_fields=['network_id'])
        return network.id
    except Exception as e:
        logger.error(f"Failed to create network for project {project.name}: {e}")
        raise

def delete_project_network(project: Project):
    """
    Deletes the isolated bridge network for the project.
    """
    if not project.network_id:
        return

    client = get_docker_client()
    try:
        network = client.networks.get(project.network_id)
        network.remove()
        project.network_id = None
        project.save(update_fields=['network_id'])
    except Exception as e:
        logger.error(f"Failed to delete network {project.network_id} for project {project.name}: {e}")
        project.network_id = None
        project.save(update_fields=['network_id'])

def start_container(deployment: Deployment):
    """
    Starts the container for the deployment.
    """
    if not deployment.container_id:
        logger.error(f"Cannot start deployment {deployment.id}: no container_id")
        return

    client = get_docker_client()
    try:
        deployment.status = Deployment.Status.STARTING
        deployment.save(update_fields=['status'])

        container = client.containers.get(deployment.container_id)
        container.start()

        deployment.status = Deployment.Status.RUNNING
        deployment.save(update_fields=['status'])
    except Exception as e:
        logger.error(f"Failed to start container {deployment.container_id}: {e}")
        deployment.status = Deployment.Status.FAILED
        deployment.save(update_fields=['status'])
        raise

def stop_container(deployment: Deployment):
    """
    Stops the container for the deployment.
    """
    if not deployment.container_id:
        return

    client = get_docker_client()
    try:
        deployment.status = Deployment.Status.STOPPING
        deployment.save(update_fields=['status'])

        container = client.containers.get(deployment.container_id)
        container.stop()

        deployment.status = Deployment.Status.STOPPED
        deployment.save(update_fields=['status'])
    except Exception as e:
        logger.error(f"Failed to stop container {deployment.container_id}: {e}")
        deployment.status = Deployment.Status.FAILED
        deployment.save(update_fields=['status'])
        raise

def restart_container(deployment: Deployment):
    """
    Restarts the container for the deployment.
    """
    if not deployment.container_id:
        return

    client = get_docker_client()
    try:
        deployment.status = Deployment.Status.RESTARTING
        deployment.save(update_fields=['status'])

        container = client.containers.get(deployment.container_id)
        container.restart()

        deployment.status = Deployment.Status.RUNNING
        deployment.save(update_fields=['status'])
    except Exception as e:
        logger.error(f"Failed to restart container {deployment.container_id}: {e}")
        deployment.status = Deployment.Status.FAILED
        deployment.save(update_fields=['status'])
        raise

def remove_container(deployment: Deployment, force=False):
    """
    Removes the container for the deployment.
    """
    if not deployment.container_id:
        return

    client = get_docker_client()
    try:
        container = client.containers.get(deployment.container_id)
        container.remove(force=force)

        deployment.container_id = None
        deployment.status = Deployment.Status.REMOVED
        deployment.save(update_fields=['container_id', 'status'])
    except Exception as e:
        logger.error(f"Failed to remove container {deployment.container_id}: {e}")
        # Even if removal fails from Docker's side (e.g. not found),
        # we might want to clear it from our DB if it's a "force" or cleanup operation.
        raise

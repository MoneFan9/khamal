from .docker_client import get_docker_client
from .models import Project, Deployment
import logging

logger = logging.getLogger(__name__)

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

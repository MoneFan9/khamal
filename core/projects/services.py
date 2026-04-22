from .docker_client import get_docker_client
from .models import Project
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
        # We don't necessarily want to block project deletion if network cleanup fails,
        # but we should log it. Or maybe we should raise?
        # Usually it's better to try to clean up.
        project.network_id = None
        project.save(update_fields=['network_id'])

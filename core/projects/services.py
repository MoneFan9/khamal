from django.conf import settings
from .docker_client import get_docker_client
from .models import Project, Deployment
from local.models import LocalSource
import logging
import docker
import secrets
import time

logger = logging.getLogger(__name__)

PROXY_NETWORK_NAME = "khamal-proxy"
TRAEFIK_CONTAINER_NAME = "khamal-traefik"
TRAEFIK_IMAGE = "traefik:v3.1"

DATABASE_IMAGES = {
    "postgres": "postgres:16",
    "redis": "redis:7-alpine",
}

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

    # Ensure Traefik container exists
    try:
        client.containers.get(TRAEFIK_CONTAINER_NAME)
    except docker.errors.NotFound:
        logger.info(f"Creating global Traefik container: {TRAEFIK_CONTAINER_NAME}")

        command = [
            "--providers.docker=true",
            "--providers.docker.exposedbydefault=false",
            f"--providers.docker.network={PROXY_NETWORK_NAME}",
            "--entrypoints.web.address=:80",
            "--entrypoints.websecure.address=:443",
        ]

        volumes = {
            '/var/run/docker.sock': {'bind': '/var/run/docker.sock', 'mode': 'ro'}
        }

        if settings.KHAMAL_SSL_ENABLED:
            command.extend([
                "--certificatesresolvers.le.acme.email=" + settings.KHAMAL_ACME_EMAIL,
                "--certificatesresolvers.le.acme.storage=" + settings.KHAMAL_ACME_STORAGE,
                "--certificatesresolvers.le.acme.tlschallenge=true",
                "--certificatesresolvers.le.acme.caserver=" + settings.KHAMAL_ACME_CA_SERVER,
                "--entrypoints.web.http.redirections.entryPoint.to=websecure",
                "--entrypoints.web.http.redirections.entryPoint.scheme=https",
            ])
            # Persist certificates
            volumes['khamal-letsencrypt'] = {'bind': '/letsencrypt', 'mode': 'rw'}

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
            volumes=volumes,
            command=command,
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

def get_routing_labels(deployment: Deployment) -> dict:
    """
    Returns the Traefik labels required for routing to this deployment.
    """
    project = deployment.project
    if not project.domain:
        return {"khamal.managed": "true"}

    # Unique names for Traefik router and service
    router_name = f"khamal-router-{deployment.id}"
    service_name = f"khamal-service-{deployment.id}"

    labels = {
        "traefik.enable": "true",
        f"traefik.http.routers.{router_name}.rule": f"Host(`{project.domain}`)",
        f"traefik.http.routers.{router_name}.service": service_name,
        f"traefik.http.services.{service_name}.loadbalancer.server.port": str(deployment.container_port),
        "khamal.managed": "true",
        "khamal.project.id": str(project.id),
        "khamal.deployment.id": str(deployment.id),
    }

    if settings.KHAMAL_SSL_ENABLED:
        labels.update({
            f"traefik.http.routers.{router_name}.entrypoints": "websecure",
            f"traefik.http.routers.{router_name}.tls": "true",
            f"traefik.http.routers.{router_name}.tls.certresolver": "le",
        })
    else:
        labels.update({
            f"traefik.http.routers.{router_name}.entrypoints": "web",
        })

    return labels

def create_deployment_container(deployment: Deployment, image: str):
    """
    Creates and starts a container for the deployment with proper networks and labels.
    """
    client = get_docker_client()
    project = deployment.project

    # 1. Ensure networks exist
    ensure_global_proxy()
    project_network_id = ensure_project_network(project)

    # 2. Get routing labels
    labels = get_routing_labels(deployment)

    # 3. Create and run container
    try:
        deployment.status = Deployment.Status.STARTING
        deployment.save(update_fields=['status'])

        # Prepare volumes for Hot-Reload if enabled
        volumes = {}
        if deployment.hot_reload:
            try:
                local_source = project.local_source
                volumes[local_source.host_path] = {
                    'bind': local_source.container_path,
                    'mode': 'rw'
                }
                logger.info(f"Hot-Reload enabled for deployment {deployment.id}: mounting {local_source.host_path}")
            except LocalSource.DoesNotExist:
                logger.warning(f"Hot-Reload enabled for deployment {deployment.id} but no LocalSource found for project {project.id}")

        network_obj = client.networks.get(project_network_id)
        container = client.containers.run(
            image,
            detach=True,
            name=f"khamal-dep-{deployment.id}",
            labels=labels,
            network=network_obj.name,
            volumes=volumes,
            restart_policy={"Name": "always"}
        )

        # 4. Connect to global proxy network for routing
        proxy_net = client.networks.get(PROXY_NETWORK_NAME)
        proxy_net.connect(container)

        deployment.container_id = container.id
        deployment.status = Deployment.Status.RUNNING
        deployment.save(update_fields=['container_id', 'status'])

        return container
    except Exception as e:
        logger.error(f"Failed to create/start container for deployment {deployment.id}: {e}")
        deployment.status = Deployment.Status.FAILED
        deployment.save(update_fields=['status'])
        raise

def _wait_for_healthy(container, timeout: int = 60):
    """
    Waits for a container to become healthy or running.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        container.reload()
        # If the container has a health check, wait for it
        health = container.attrs.get("State", {}).get("Health", {}).get("Status")
        if health == "healthy":
            return True
        # If no health check, just wait for 'running' status
        if health is None and container.status == "running":
            return True

        if container.status == "exited":
            return False

        time.sleep(2)
    return False

def provision_database(project: Project, engine: str):
    """
    Provisions a database container (PostgreSQL or Redis) for the project.
    """
    client = get_docker_client()
    project_network_id = ensure_project_network(project)
    network_obj = client.networks.get(project_network_id)

    container_name = f"khamal-db-{engine}-{project.id}"
    image = DATABASE_IMAGES.get(engine, f"{engine}:latest")

    try:
        container = client.containers.get(container_name)
        if container.status != "running":
            container.start()
        logger.info(f"Database container {container_name} already exists and is running.")
        return container
    except docker.errors.NotFound:
        logger.info(f"Provisioning new {engine} container: {container_name}")

    environment = {}
    if engine == "postgres":
        environment = {
            "POSTGRES_DB": "khamal",
            "POSTGRES_USER": "khamal",
            "POSTGRES_PASSWORD": secrets.token_urlsafe(16)
        }

    volumes = {
        f"khamal-data-{engine}-{project.id}": {
            "bind": "/var/lib/postgresql/data" if engine == "postgres" else "/data",
            "mode": "rw"
        }
    }

    try:
        container = client.containers.run(
            image,
            name=container_name,
            detach=True,
            network=network_obj.name,
            environment=environment,
            volumes=volumes,
            restart_policy={"Name": "always"},
            labels={
                "khamal.managed": "true",
                "khamal.project.id": str(project.id),
                "khamal.db.engine": engine
            }
        )

        # Wait for database to be ready
        if not _wait_for_healthy(container):
            logger.warning(f"Database container {container_name} did not become healthy in time.")

        return container
    except docker.errors.APIError as e:
        if e.response is not None and e.response.status_code == 409:
            logger.info(f"Container {container_name} already exists (race condition).")
            return client.containers.get(container_name)
        raise
    except Exception as e:
        logger.error(f"Failed to provision {engine} for project {project.id}: {e}")
        raise

def auto_provision_from_plan(project: Project, plan):
    """
    Auto-provisions dependencies based on the Nixpacks plan.
    """
    if plan.has_postgres:
        provision_database(project, "postgres")

    if plan.has_redis:
        provision_database(project, "redis")

def get_deployment_logs(deployment: Deployment, tail: int = 1000) -> str:
    """
    Retrieves the logs for the deployment's container.
    """
    if not deployment.container_id:
        return ""

    client = get_docker_client()
    try:
        container = client.containers.get(deployment.container_id)
        # Returns logs as a string (UTF-8 decoded)
        return container.logs(tail=tail, stdout=True, stderr=True).decode('utf-8')
    except docker.errors.NotFound:
        logger.warning(f"Container {deployment.container_id} not found for logs.")
        return ""
    except Exception as e:
        logger.error(f"Failed to get logs for container {deployment.container_id}: {e}")
        return ""

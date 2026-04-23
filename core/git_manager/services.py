import os
import logging
import git
from concurrent.futures import ThreadPoolExecutor
from django.utils import timezone
from .models import Repository

logger = logging.getLogger(__name__)

# Executor for asynchronous Git operations
git_executor = ThreadPoolExecutor(max_workers=4)

def clone_repository(repo_id: int):
    """
    Clones a Git repository to the local path.
    """
    try:
        repo_obj = Repository.objects.get(id=repo_id)
        if os.path.exists(repo_obj.local_path) and os.listdir(repo_obj.local_path):
             logger.warning(f"Path {repo_obj.local_path} is not empty. Skipping clone.")
             return

        os.makedirs(os.path.dirname(repo_obj.local_path), exist_ok=True)
        git.Repo.clone_from(repo_obj.url, repo_obj.local_path, branch=repo_obj.current_branch)
        logger.info(f"Successfully cloned {repo_obj.url} to {repo_obj.local_path}")
    except Exception as e:
        logger.error(f"Failed to clone repository {repo_id}: {e}")
        raise

def pull_repository(repo_id: int):
    """
    Performs a git pull on the repository.
    """
    try:
        repo_obj = Repository.objects.get(id=repo_id)
        repo = git.Repo(repo_obj.local_path)
        origin = repo.remotes.origin
        origin.pull()

        repo_obj.last_pull_at = timezone.now()
        repo_obj.save(update_fields=['last_pull_at'])
        logger.info(f"Successfully pulled updates for {repo_obj.local_path}")
    except Exception as e:
        logger.error(f"Failed to pull repository {repo_id}: {e}")
        raise

def pull_repository_async(repo_id: int):
    """
    Performs a git pull asynchronously.
    """
    git_executor.submit(pull_repository, repo_id)

def switch_branch(repo_id: int, branch_name: str):
    """
    Switches the repository to a specific branch.
    """
    try:
        repo_obj = Repository.objects.get(id=repo_id)
        repo = git.Repo(repo_obj.local_path)

        # Fetch all branches
        repo.remotes.origin.fetch()

        # Checkout the branch
        repo.git.checkout(branch_name)

        repo_obj.current_branch = branch_name
        repo_obj.save(update_fields=['current_branch'])
        logger.info(f"Switched {repo_obj.local_path} to branch {branch_name}")
    except Exception as e:
        logger.error(f"Failed to switch branch for repository {repo_id}: {e}")
        raise

def list_branches(repo_id: int):
    """
    Lists all local and remote branches.
    """
    try:
        repo_obj = Repository.objects.get(id=repo_id)
        repo = git.Repo(repo_obj.local_path)
        return [ref.name for ref in repo.references]
    except Exception as e:
        logger.error(f"Failed to list branches for repository {repo_id}: {e}")
        raise

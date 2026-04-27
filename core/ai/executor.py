import os
from pathlib import Path
from typing import Dict, Any, List, Optional

def _handle_create(file_path: Path, content: str, relative_path: str) -> str:
    """Handles the 'create' action."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content)
    return f"Created {relative_path}"

def _handle_delete(file_path: Path, relative_path: str) -> str:
    """Handles the 'delete' action."""
    if file_path.exists():
        file_path.unlink()
        return f"Deleted {relative_path}"
    return f"Skip delete: {relative_path} does not exist"

def _handle_update(file_path: Path, content: str, relative_path: str, search_block: Optional[str]) -> str:
    """Handles the 'update' action."""
    if not file_path.exists():
        raise FileNotFoundError(f"Cannot update {relative_path}: File not found")

    original_content = file_path.read_text()
    if search_block:
        if search_block not in original_content:
            raise ValueError(f"Search block not found in {relative_path}")
        new_content = original_content.replace(search_block, content)
    else:
        new_content = content

    file_path.write_text(new_content)
    return f"Updated {relative_path}"

def apply_fix(fix_data: Dict[str, Any], root_dir: Path = None) -> List[str]:
    """
    Applies a structured fix to the filesystem.

    Args:
        fix_data: Dict with 'rationale' and 'changes'.
        root_dir: The base directory where changes should be applied.
                 Defaults to current working directory.

    Returns:
        A list of success messages for each change applied.

    Raises:
        FileNotFoundError: If an update is requested on a non-existent file.
        ValueError: If a search_block is provided but not found in the file.
        Exception: For other filesystem errors.
    """
    if root_dir is None:
        root_dir = Path.cwd()
    else:
        root_dir = Path(root_dir)

    results = []
    changes = fix_data.get("changes", [])

    for change in changes:
        file_path = (root_dir / change["file_path"]).resolve()

        # Security check: ensure the path is within root_dir
        if not str(file_path).startswith(str(root_dir.resolve())):
            raise PermissionError(f"Security error: Attempted to access path outside root directory: {change['file_path']}")

        action = change["action"]
        content = change["content"]
        search_block = change.get("search_block")
        rel_path = change["file_path"]

        if action == "create":
            results.append(_handle_create(file_path, content, rel_path))
        elif action == "delete":
            results.append(_handle_delete(file_path, rel_path))
        elif action == "update":
            results.append(_handle_update(file_path, content, rel_path, search_block))

    return results

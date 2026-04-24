import os
from pathlib import Path
from typing import Dict, Any, List

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

        if action == "create":
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
            results.append(f"Created {change['file_path']}")

        elif action == "delete":
            if file_path.exists():
                file_path.unlink()
                results.append(f"Deleted {change['file_path']}")
            else:
                results.append(f"Skip delete: {change['file_path']} does not exist")

        elif action == "update":
            if not file_path.exists():
                raise FileNotFoundError(f"Cannot update {change['file_path']}: File not found")

            original_content = file_path.read_text()
            if search_block:
                if search_block not in original_content:
                    raise ValueError(f"Search block not found in {change['file_path']}")
                # Replace only the first occurrence for safety, or all?
                # Standard practice in these tools is usually all, but exact block is expected.
                new_content = original_content.replace(search_block, content)
            else:
                # If no search_block, content is the new full file content
                new_content = content

            file_path.write_text(new_content)
            results.append(f"Updated {change['file_path']}")

    return results

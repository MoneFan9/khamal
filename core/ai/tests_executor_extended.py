import pytest
from pathlib import Path
from core.ai.executor import apply_fix

@pytest.fixture
def temp_root(tmp_path):
    return tmp_path

def test_apply_fix_create(temp_root):
    fix_data = {
        "changes": [
            {
                "file_path": "new_file.py",
                "action": "create",
                "content": "print('hello')"
            }
        ]
    }
    results = apply_fix(fix_data, root_dir=temp_root)

    assert "Created new_file.py" in results
    assert (temp_root / "new_file.py").read_text() == "print('hello')"

def test_apply_fix_delete(temp_root):
    test_file = temp_root / "to_delete.txt"
    test_file.write_text("goodbye")

    fix_data = {
        "changes": [
            {
                "file_path": "to_delete.txt",
                "action": "delete",
                "content": ""
            }
        ]
    }
    results = apply_fix(fix_data, root_dir=temp_root)

    assert "Deleted to_delete.txt" in results
    assert not test_file.exists()

def test_apply_fix_delete_non_existent(temp_root):
    fix_data = {
        "changes": [
            {
                "file_path": "missing.txt",
                "action": "delete",
                "content": ""
            }
        ]
    }
    results = apply_fix(fix_data, root_dir=temp_root)
    assert "Skip delete: missing.txt does not exist" in results

def test_apply_fix_update_full_content(temp_root):
    test_file = temp_root / "update_me.txt"
    test_file.write_text("old content")

    fix_data = {
        "changes": [
            {
                "file_path": "update_me.txt",
                "action": "update",
                "content": "new content",
                "search_block": None
            }
        ]
    }
    results = apply_fix(fix_data, root_dir=temp_root)

    assert "Updated update_me.txt" in results
    assert test_file.read_text() == "new content"

def test_apply_fix_update_search_replace(temp_root):
    test_file = temp_root / "replace.py"
    test_file.write_text("def old_func():\n    pass")

    fix_data = {
        "changes": [
            {
                "file_path": "replace.py",
                "action": "update",
                "content": "def new_func():",
                "search_block": "def old_func():"
            }
        ]
    }
    results = apply_fix(fix_data, root_dir=temp_root)

    assert "Updated replace.py" in results
    assert test_file.read_text() == "def new_func():\n    pass"

def test_apply_fix_update_not_found_raises(temp_root):
    fix_data = {
        "changes": [
            {
                "file_path": "not_there.txt",
                "action": "update",
                "content": "stuff"
            }
        ]
    }
    with pytest.raises(FileNotFoundError):
        apply_fix(fix_data, root_dir=temp_root)

def test_apply_fix_search_block_mismatch_raises(temp_root):
    test_file = temp_root / "mismatch.txt"
    test_file.write_text("actual content")

    fix_data = {
        "changes": [
            {
                "file_path": "mismatch.txt",
                "action": "update",
                "content": "new",
                "search_block": "wrong search"
            }
        ]
    }
    with pytest.raises(ValueError, match="Search block not found"):
        apply_fix(fix_data, root_dir=temp_root)

def test_apply_fix_security_check(temp_root):
    fix_data = {
        "changes": [
            {
                "file_path": "../outside.txt",
                "action": "create",
                "content": "danger"
            }
        ]
    }
    with pytest.raises(PermissionError):
        apply_fix(fix_data, root_dir=temp_root)

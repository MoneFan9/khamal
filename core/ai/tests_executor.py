import pytest
import os
from pathlib import Path
from core.ai.executor import apply_fix

@pytest.fixture
def temp_root(tmp_path):
    return tmp_path

def test_apply_fix_create(temp_root):
    fix_data = {
        "changes": [
            {
                "file_path": "new_file.txt",
                "action": "create",
                "content": "Hello World"
            }
        ]
    }
    results = apply_fix(fix_data, root_dir=temp_root)
    assert results == ["Created new_file.txt"]
    assert (temp_root / "new_file.txt").read_text() == "Hello World"

def test_apply_fix_delete(temp_root):
    file_to_delete = temp_root / "delete_me.txt"
    file_to_delete.write_text("Bye")

    fix_data = {
        "changes": [
            {
                "file_path": "delete_me.txt",
                "action": "delete",
                "content": ""
            }
        ]
    }
    results = apply_fix(fix_data, root_dir=temp_root)
    assert results == ["Deleted delete_me.txt"]
    assert not file_to_delete.exists()

def test_apply_fix_delete_non_existent(temp_root):
    fix_data = {
        "changes": [
            {
                "file_path": "non_existent.txt",
                "action": "delete",
                "content": ""
            }
        ]
    }
    results = apply_fix(fix_data, root_dir=temp_root)
    assert results == ["Skip delete: non_existent.txt does not exist"]

def test_apply_fix_update_full_content(temp_root):
    file_to_update = temp_root / "update.txt"
    file_to_update.write_text("Old content")

    fix_data = {
        "changes": [
            {
                "file_path": "update.txt",
                "action": "update",
                "content": "New content"
            }
        ]
    }
    results = apply_fix(fix_data, root_dir=temp_root)
    assert results == ["Updated update.txt"]
    assert file_to_update.read_text() == "New content"

def test_apply_fix_update_search_replace(temp_root):
    file_to_update = temp_root / "search.txt"
    file_to_update.write_text("Line 1\nLine 2\nLine 3")

    fix_data = {
        "changes": [
            {
                "file_path": "search.txt",
                "action": "update",
                "content": "REPLACED",
                "search_block": "Line 2"
            }
        ]
    }
    results = apply_fix(fix_data, root_dir=temp_root)
    assert results == ["Updated search.txt"]
    assert file_to_update.read_text() == "Line 1\nREPLACED\nLine 3"

def test_apply_fix_update_not_found_raises_error(temp_root):
    fix_data = {
        "changes": [
            {
                "file_path": "missing.txt",
                "action": "update",
                "content": "..."
            }
        ]
    }
    with pytest.raises(FileNotFoundError):
        apply_fix(fix_data, root_dir=temp_root)

def test_apply_fix_search_block_not_found_raises_error(temp_root):
    f = temp_root / "test.txt"
    f.write_text("content")
    fix_data = {
        "changes": [
            {
                "file_path": "test.txt",
                "action": "update",
                "content": "new",
                "search_block": "not there"
            }
        ]
    }
    with pytest.raises(ValueError, match="Search block not found"):
        apply_fix(fix_data, root_dir=temp_root)

def test_apply_fix_security_check_outside_root(temp_root):
    fix_data = {
        "changes": [
            {
                "file_path": "../outside.txt",
                "action": "create",
                "content": "Exploit"
            }
        ]
    }
    with pytest.raises(PermissionError, match="Security error"):
        apply_fix(fix_data, root_dir=temp_root)

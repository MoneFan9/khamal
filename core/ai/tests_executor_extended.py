import pytest
import os
from pathlib import Path
from ai.executor import apply_fix

@pytest.fixture
def temp_root(tmp_path):
    root = tmp_path / "app"
    root.mkdir()
    return root

def test_apply_fix_create(temp_root):
    fix_data = {
        "changes": [
            {
                "action": "create",
                "file_path": "new_file.py",
                "content": "print('hello')"
            }
        ]
    }
    results = apply_fix(fix_data, root_dir=temp_root)
    assert "Created new_file.py" in results
    assert (temp_root / "new_file.py").read_text() == "print('hello')"

def test_apply_fix_create_nested(temp_root):
    fix_data = {
        "changes": [
            {
                "action": "create",
                "file_path": "subdir/nested.py",
                "content": "nested"
            }
        ]
    }
    apply_fix(fix_data, root_dir=temp_root)
    assert (temp_root / "subdir" / "nested.py").read_text() == "nested"

def test_apply_fix_update_full(temp_root):
    # Create file first
    existing_file = temp_root / "test.py"
    existing_file.write_text("original content")

    fix_data = {
        "changes": [
            {
                "action": "update",
                "file_path": "test.py",
                "content": "new content",
                "search_block": None
            }
        ]
    }
    results = apply_fix(fix_data, root_dir=temp_root)
    assert "Updated test.py" in results
    assert existing_file.read_text() == "new content"

def test_apply_fix_update_partial(temp_root):
    existing_file = temp_root / "test.py"
    existing_file.write_text("line 1\nSEARCH ME\nline 3")

    fix_data = {
        "changes": [
            {
                "action": "update",
                "file_path": "test.py",
                "content": "REPLACED",
                "search_block": "SEARCH ME"
            }
        ]
    }
    apply_fix(fix_data, root_dir=temp_root)
    assert existing_file.read_text() == "line 1\nREPLACED\nline 3"

def test_apply_fix_update_not_found(temp_root):
    fix_data = {
        "changes": [
            {
                "action": "update",
                "file_path": "missing.py",
                "content": "content"
            }
        ]
    }
    with pytest.raises(FileNotFoundError):
        apply_fix(fix_data, root_dir=temp_root)

def test_apply_fix_update_search_not_found(temp_root):
    existing_file = temp_root / "test.py"
    existing_file.write_text("some content")

    fix_data = {
        "changes": [
            {
                "action": "update",
                "file_path": "test.py",
                "content": "new",
                "search_block": "NOT THERE"
            }
        ]
    }
    with pytest.raises(ValueError):
        apply_fix(fix_data, root_dir=temp_root)

def test_apply_fix_delete(temp_root):
    existing_file = temp_root / "test.py"
    existing_file.write_text("delete me")

    fix_data = {
        "changes": [
            {
                "action": "delete",
                "file_path": "test.py",
                "content": ""
            }
        ]
    }
    results = apply_fix(fix_data, root_dir=temp_root)
    assert "Deleted test.py" in results
    assert not existing_file.exists()

def test_apply_fix_delete_missing(temp_root):
    fix_data = {
        "changes": [
            {
                "action": "delete",
                "file_path": "ghost.py",
                "content": ""
            }
        ]
    }
    results = apply_fix(fix_data, root_dir=temp_root)
    assert "Skip delete: ghost.py does not exist" in results

def test_apply_fix_security_boundary(temp_root):
    fix_data = {
        "changes": [
            {
                "action": "create",
                "file_path": "../outside.txt",
                "content": "evil"
            }
        ]
    }
    with pytest.raises(PermissionError):
        apply_fix(fix_data, root_dir=temp_root)

def test_apply_fix_security_boundary_absolute(temp_root):
    fix_data = {
        "changes": [
            {
                "action": "create",
                "file_path": "/tmp/evil.txt",
                "content": "evil"
            }
        ]
    }
    with pytest.raises(PermissionError):
        apply_fix(fix_data, root_dir=temp_root)

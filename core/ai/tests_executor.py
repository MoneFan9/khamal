import pytest
import os
import shutil
from pathlib import Path
from core.ai.executor import apply_fix

@pytest.fixture
def executor_env():
    test_dir = Path("test_executor_env")
    test_dir.mkdir(exist_ok=True)
    (test_dir / "subdir").mkdir(exist_ok=True)
    yield test_dir
    if test_dir.exists():
        shutil.rmtree(test_dir)

def test_apply_fix_create(executor_env):
    fix_data = {
        "changes": [
            {"file_path": "new_file.txt", "action": "create", "content": "hello world"}
        ]
    }
    results = apply_fix(fix_data, root_dir=executor_env)
    assert results == ["Created new_file.txt"]
    assert (executor_env / "new_file.txt").exists()
    assert (executor_env / "new_file.txt").read_text() == "hello world"

def test_apply_fix_update(executor_env):
    file_path = executor_env / "update_me.txt"
    file_path.write_text("line1\nline2")

    fix_data = {
        "changes": [
            {
                "file_path": "update_me.txt",
                "action": "update",
                "search_block": "line1",
                "content": "new_line1"
            }
        ]
    }
    results = apply_fix(fix_data, root_dir=executor_env)
    assert results == ["Updated update_me.txt"]
    assert file_path.read_text() == "new_line1\nline2"

def test_apply_fix_delete(executor_env):
    file_path = executor_env / "delete_me.txt"
    file_path.write_text("content")

    fix_data = {
        "changes": [
            {"file_path": "delete_me.txt", "action": "delete", "content": ""}
        ]
    }
    results = apply_fix(fix_data, root_dir=executor_env)
    assert results == ["Deleted delete_me.txt"]
    assert not file_path.exists()

def test_security_path_traversal(executor_env):
    fix_data = {
        "changes": [
            {"file_path": "../outside.txt", "action": "create", "content": "evil"}
        ]
    }
    with pytest.raises(PermissionError):
        apply_fix(fix_data, root_dir=executor_env)

def test_update_not_found(executor_env):
    fix_data = {
        "changes": [
            {"file_path": "missing.txt", "action": "update", "content": "new"}
        ]
    }
    with pytest.raises(FileNotFoundError):
        apply_fix(fix_data, root_dir=executor_env)

def test_search_block_not_found(executor_env):
    file_path = executor_env / "file.txt"
    file_path.write_text("content")

    fix_data = {
        "changes": [
            {
                "file_path": "file.txt",
                "action": "update",
                "search_block": "wrong",
                "content": "new"
            }
        ]
    }
    with pytest.raises(ValueError):
        apply_fix(fix_data, root_dir=executor_env)

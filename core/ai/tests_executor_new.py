import pytest
from pathlib import Path
from core.ai.executor import apply_fix

def test_apply_fix_create(tmp_path):
    fix_data = {
        "changes": [
            {
                "file_path": "new_file.txt",
                "action": "create",
                "content": "Hello World"
            }
        ]
    }
    results = apply_fix(fix_data, root_dir=tmp_path)

    assert results == ["Created new_file.txt"]
    assert (tmp_path / "new_file.txt").read_text() == "Hello World"

def test_apply_fix_delete(tmp_path):
    test_file = tmp_path / "to_delete.txt"
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
    results = apply_fix(fix_data, root_dir=tmp_path)

    assert results == ["Deleted to_delete.txt"]
    assert not test_file.exists()

def test_apply_fix_delete_not_exists(tmp_path):
    fix_data = {
        "changes": [
            {
                "file_path": "non_existent.txt",
                "action": "delete",
                "content": ""
            }
        ]
    }
    results = apply_fix(fix_data, root_dir=tmp_path)
    assert results == ["Skip delete: non_existent.txt does not exist"]

def test_apply_fix_update_full(tmp_path):
    test_file = tmp_path / "update_me.txt"
    test_file.write_text("old content")

    fix_data = {
        "changes": [
            {
                "file_path": "update_me.txt",
                "action": "update",
                "content": "new content"
            }
        ]
    }
    results = apply_fix(fix_data, root_dir=tmp_path)

    assert results == ["Updated update_me.txt"]
    assert test_file.read_text() == "new content"

def test_apply_fix_update_search_block(tmp_path):
    test_file = tmp_path / "update_me.txt"
    test_file.write_text("line 1\nline 2\nline 3")

    fix_data = {
        "changes": [
            {
                "file_path": "update_me.txt",
                "action": "update",
                "search_block": "line 2",
                "content": "line TWO"
            }
        ]
    }
    results = apply_fix(fix_data, root_dir=tmp_path)

    assert results == ["Updated update_me.txt"]
    assert test_file.read_text() == "line 1\nline TWO\nline 3"

def test_apply_fix_update_not_found(tmp_path):
    fix_data = {
        "changes": [
            {
                "file_path": "missing.txt",
                "action": "update",
                "content": "content"
            }
        ]
    }
    with pytest.raises(FileNotFoundError):
        apply_fix(fix_data, root_dir=tmp_path)

def test_apply_fix_update_search_block_not_found(tmp_path):
    test_file = tmp_path / "file.txt"
    test_file.write_text("content")

    fix_data = {
        "changes": [
            {
                "file_path": "file.txt",
                "action": "update",
                "search_block": "missing",
                "content": "new"
            }
        ]
    }
    with pytest.raises(ValueError, match="Search block not found"):
        apply_fix(fix_data, root_dir=tmp_path)

def test_apply_fix_security_check(tmp_path):
    fix_data = {
        "changes": [
            {
                "file_path": "../outside.txt",
                "action": "create",
                "content": "evil"
            }
        ]
    }
    with pytest.raises(PermissionError, match="Security error"):
        apply_fix(fix_data, root_dir=tmp_path)

def test_apply_fix_default_root(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    fix_data = {
        "changes": [
            {
                "file_path": "local_file.txt",
                "action": "create",
                "content": "local"
            }
        ]
    }
    apply_fix(fix_data)
    assert (tmp_path / "local_file.txt").exists()

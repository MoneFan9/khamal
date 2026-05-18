import pytest
import shutil
import tempfile
from pathlib import Path
from .executor import apply_fix

@pytest.fixture
def test_dir():
    dir_path = Path(tempfile.mkdtemp())
    yield dir_path
    shutil.rmtree(dir_path)

def test_apply_fix_update_no_search_block(test_dir):
    file_path = test_dir / "full_update.txt"
    file_path.write_text("old content")

    fix_data = {
        "changes": [
            {
                "file_path": "full_update.txt",
                "action": "update",
                "content": "new full content"
            }
        ]
    }
    results = apply_fix(fix_data, root_dir=test_dir)
    assert results == ["Updated full_update.txt"]
    assert file_path.read_text() == "new full content"

def test_apply_fix_unknown_action_ignored(test_dir):
    fix_data = {
        "changes": [
            {
                "file_path": "test.txt",
                "action": "magic",
                "content": "some content"
            }
        ]
    }
    results = apply_fix(fix_data, root_dir=test_dir)
    assert results == []

def test_apply_fix_update_file_not_found(test_dir):
    fix_data = {
        "changes": [
            {
                "file_path": "ghost.txt",
                "action": "update",
                "content": "new"
            }
        ]
    }
    with pytest.raises(FileNotFoundError):
        apply_fix(fix_data, root_dir=test_dir)

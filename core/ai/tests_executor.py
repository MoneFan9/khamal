import unittest
from pathlib import Path
import tempfile
import shutil
from ai.executor import apply_fix

class TestExecutor(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_apply_fix_create(self):
        fix_data = {
            "changes": [
                {"action": "create", "file_path": "new_file.txt", "content": "hello world"}
            ]
        }
        results = apply_fix(fix_data, root_dir=self.test_dir)
        self.assertIn("Created new_file.txt", results[0])
        self.assertEqual((self.test_dir / "new_file.txt").read_text(), "hello world")

    def test_apply_fix_delete(self):
        test_file = self.test_dir / "to_delete.txt"
        test_file.write_text("trash")

        fix_data = {
            "changes": [
                {"action": "delete", "file_path": "to_delete.txt", "content": ""}
            ]
        }
        results = apply_fix(fix_data, root_dir=self.test_dir)
        self.assertIn("Deleted to_delete.txt", results[0])
        self.assertFalse(test_file.exists())

    def test_apply_fix_delete_nonexistent(self):
        fix_data = {
            "changes": [
                {"action": "delete", "file_path": "missing.txt", "content": ""}
            ]
        }
        results = apply_fix(fix_data, root_dir=self.test_dir)
        self.assertIn("Skip delete", results[0])

    def test_apply_fix_update_full(self):
        test_file = self.test_dir / "update_me.txt"
        test_file.write_text("old content")

        fix_data = {
            "changes": [
                {"action": "update", "file_path": "update_me.txt", "content": "new content"}
            ]
        }
        results = apply_fix(fix_data, root_dir=self.test_dir)
        self.assertIn("Updated update_me.txt", results[0])
        self.assertEqual(test_file.read_text(), "new content")

    def test_apply_fix_update_partial(self):
        test_file = self.test_dir / "partial.txt"
        test_file.write_text("line1\nline2\nline3")

        fix_data = {
            "changes": [
                {
                    "action": "update",
                    "file_path": "partial.txt",
                    "content": "REPLACED",
                    "search_block": "line2"
                }
            ]
        }
        results = apply_fix(fix_data, root_dir=self.test_dir)
        self.assertEqual(test_file.read_text(), "line1\nREPLACED\nline3")

    def test_apply_fix_update_not_found_raises(self):
        fix_data = {
            "changes": [
                {"action": "update", "file_path": "missing.txt", "content": "new"}
            ]
        }
        with self.assertRaises(FileNotFoundError):
            apply_fix(fix_data, root_dir=self.test_dir)

    def test_apply_fix_update_search_block_not_found_raises(self):
        test_file = self.test_dir / "exists.txt"
        test_file.write_text("content")

        fix_data = {
            "changes": [
                {
                    "action": "update",
                    "file_path": "exists.txt",
                    "content": "new",
                    "search_block": "WRONG"
                }
            ]
        }
        with self.assertRaises(ValueError):
            apply_fix(fix_data, root_dir=self.test_dir)

    def test_security_path_traversal(self):
        fix_data = {
            "changes": [
                {"action": "create", "file_path": "../outside.txt", "content": "evil"}
            ]
        }
        with self.assertRaises(PermissionError):
            apply_fix(fix_data, root_dir=self.test_dir)

import unittest
import os
from pathlib import Path
from core.ai.executor import apply_fix

class TestApplyFix(unittest.TestCase):
    def setUp(self):
        self.test_root = Path("/tmp/khamal_test_executor")
        self.test_root.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        import shutil
        if self.test_root.exists():
            shutil.rmtree(self.test_root)

    def test_handle_create(self):
        fix_data = {
            "changes": [
                {
                    "action": "create",
                    "file_path": "new_file.txt",
                    "content": "hello world"
                }
            ]
        }
        results = apply_fix(fix_data, root_dir=self.test_root)
        self.assertIn("Created new_file.txt", results[0])
        self.assertEqual((self.test_root / "new_file.txt").read_text(), "hello world")

    def test_handle_delete(self):
        target = self.test_root / "to_delete.txt"
        target.write_text("gone")

        fix_data = {
            "changes": [
                {
                    "action": "delete",
                    "file_path": "to_delete.txt",
                    "content": ""
                }
            ]
        }
        results = apply_fix(fix_data, root_dir=self.test_root)
        self.assertIn("Deleted to_delete.txt", results[0])
        self.assertFalse(target.exists())

    def test_handle_delete_non_existent(self):
        fix_data = {
            "changes": [
                {
                    "action": "delete",
                    "file_path": "non_existent.txt",
                    "content": ""
                }
            ]
        }
        results = apply_fix(fix_data, root_dir=self.test_root)
        self.assertIn("Skip delete", results[0])

    def test_handle_update_full(self):
        target = self.test_root / "update_full.txt"
        target.write_text("old")

        fix_data = {
            "changes": [
                {
                    "action": "update",
                    "file_path": "update_full.txt",
                    "content": "new",
                    "search_block": None
                }
            ]
        }
        results = apply_fix(fix_data, root_dir=self.test_root)
        self.assertIn("Updated update_full.txt", results[0])
        self.assertEqual(target.read_text(), "new")

    def test_handle_update_partial(self):
        target = self.test_root / "update_partial.txt"
        target.write_text("line 1\nline 2\nline 3")

        fix_data = {
            "changes": [
                {
                    "action": "update",
                    "file_path": "update_partial.txt",
                    "content": "line 2 modified",
                    "search_block": "line 2"
                }
            ]
        }
        results = apply_fix(fix_data, root_dir=self.test_root)
        self.assertIn("Updated update_partial.txt", results[0])
        self.assertEqual(target.read_text(), "line 1\nline 2 modified\nline 3")

    def test_handle_update_file_not_found(self):
        fix_data = {
            "changes": [
                {
                    "action": "update",
                    "file_path": "missing.txt",
                    "content": "data"
                }
            ]
        }
        with self.assertRaises(FileNotFoundError):
            apply_fix(fix_data, root_dir=self.test_root)

    def test_handle_update_search_block_not_found(self):
        target = self.test_root / "wrong_search.txt"
        target.write_text("content")

        fix_data = {
            "changes": [
                {
                    "action": "update",
                    "file_path": "wrong_search.txt",
                    "content": "new",
                    "search_block": "not there"
                }
            ]
        }
        with self.assertRaises(ValueError):
            apply_fix(fix_data, root_dir=self.test_root)

    def test_path_traversal_blocked(self):
        fix_data = {
            "changes": [
                {
                    "action": "create",
                    "file_path": "../outside.txt",
                    "content": "evil"
                }
            ]
        }
        with self.assertRaises(PermissionError):
            apply_fix(fix_data, root_dir=self.test_root)

    def test_apply_fix_default_root(self):
        # Coverage for root_dir is None
        from unittest.mock import patch
        with patch("core.ai.executor.Path.cwd") as mock_cwd:
            mock_cwd.return_value = self.test_root
            fix_data = {"changes": []}
            results = apply_fix(fix_data, root_dir=None)
            self.assertEqual(results, [])
            mock_cwd.assert_called_once()

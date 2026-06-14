import unittest
import os
import shutil
import tempfile
from pathlib import Path
from .executor import apply_fix

class TestExecutor(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_apply_fix_create(self):
        fix_data = {
            "changes": [
                {
                    "file_path": "new_file.txt",
                    "action": "create",
                    "content": "Hello World"
                }
            ]
        }
        results = apply_fix(fix_data, root_dir=self.test_dir)

        self.assertEqual(len(results), 1)
        self.assertIn("Created new_file.txt", results[0])
        self.assertTrue((self.test_dir / "new_file.txt").exists())
        self.assertEqual((self.test_dir / "new_file.txt").read_text(), "Hello World")

    def test_apply_fix_update_full_content(self):
        file_path = self.test_dir / "existing.txt"
        file_path.write_text("Original")

        fix_data = {
            "changes": [
                {
                    "file_path": "existing.txt",
                    "action": "update",
                    "content": "Updated",
                    "search_block": None
                }
            ]
        }
        apply_fix(fix_data, root_dir=self.test_dir)
        self.assertEqual(file_path.read_text(), "Updated")

    def test_apply_fix_update_search_block(self):
        file_path = self.test_dir / "existing.txt"
        file_path.write_text("Line 1\nLine 2\nLine 3")

        fix_data = {
            "changes": [
                {
                    "file_path": "existing.txt",
                    "action": "update",
                    "content": "Replaced Line 2",
                    "search_block": "Line 2"
                }
            ]
        }
        apply_fix(fix_data, root_dir=self.test_dir)
        self.assertEqual(file_path.read_text(), "Line 1\nReplaced Line 2\nLine 3")

    def test_apply_fix_delete(self):
        file_path = self.test_dir / "to_delete.txt"
        file_path.write_text("Delete me")

        fix_data = {
            "changes": [
                {
                    "file_path": "to_delete.txt",
                    "action": "delete",
                    "content": "" # Not used for delete but required by schema
                }
            ]
        }
        apply_fix(fix_data, root_dir=self.test_dir)
        self.assertFalse(file_path.exists())

    def test_apply_fix_delete_non_existent(self):
        fix_data = {
            "changes": [
                {
                    "file_path": "no_exist.txt",
                    "action": "delete",
                    "content": ""
                }
            ]
        }
        results = apply_fix(fix_data, root_dir=self.test_dir)
        self.assertIn("Skip delete", results[0])

    def test_security_check_outside_root(self):
        fix_data = {
            "changes": [
                {
                    "file_path": "../outside.txt",
                    "action": "create",
                    "content": "evil"
                }
            ]
        }
        with self.assertRaises(PermissionError):
            apply_fix(fix_data, root_dir=self.test_dir)

    def test_update_file_not_found(self):
        fix_data = {
            "changes": [
                {
                    "file_path": "no_exist.txt",
                    "action": "update",
                    "content": "new",
                    "search_block": None
                }
            ]
        }
        with self.assertRaises(FileNotFoundError):
            apply_fix(fix_data, root_dir=self.test_dir)

    def test_update_search_block_not_found(self):
        file_path = self.test_dir / "existing.txt"
        file_path.write_text("Original")

        fix_data = {
            "changes": [
                {
                    "file_path": "existing.txt",
                    "action": "update",
                    "content": "new",
                    "search_block": "NOT FOUND"
                }
            ]
        }
        with self.assertRaises(ValueError):
            apply_fix(fix_data, root_dir=self.test_dir)

    def test_apply_fix_default_root(self):
        # We need to be careful with CWD here.
        # But we can at least test that it uses Path.cwd() logic.
        fix_data = {"changes": []}
        results = apply_fix(fix_data)
        self.assertEqual(results, [])

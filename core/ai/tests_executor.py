import unittest
from pathlib import Path
import tempfile
import shutil
from .executor import apply_fix

class TestApplyFix(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.test_file = self.test_dir / "test.py"
        self.test_file.write_text("print('hello')\n")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_apply_fix_create(self):
        fix_data = {
            "changes": [
                {
                    "file_path": "new_file.py",
                    "action": "create",
                    "content": "new content"
                }
            ]
        }
        results = apply_fix(fix_data, root_dir=self.test_dir)
        self.assertEqual(results, ["Created new_file.py"])
        self.assertTrue((self.test_dir / "new_file.py").exists())
        self.assertEqual((self.test_dir / "new_file.py").read_text(), "new content")

    def test_apply_fix_update_with_search_block(self):
        fix_data = {
            "changes": [
                {
                    "file_path": "test.py",
                    "action": "update",
                    "search_block": "hello",
                    "content": "world"
                }
            ]
        }
        results = apply_fix(fix_data, root_dir=self.test_dir)
        self.assertEqual(results, ["Updated test.py"])
        self.assertEqual(self.test_file.read_text(), "print('world')\n")

    def test_apply_fix_update_no_search_block(self):
        fix_data = {
            "changes": [
                {
                    "file_path": "test.py",
                    "action": "update",
                    "content": "new whole content"
                }
            ]
        }
        results = apply_fix(fix_data, root_dir=self.test_dir)
        self.assertEqual(results, ["Updated test.py"])
        self.assertEqual(self.test_file.read_text(), "new whole content")

    def test_apply_fix_delete(self):
        fix_data = {
            "changes": [
                {
                    "file_path": "test.py",
                    "action": "delete",
                    "content": "" # content not used for delete
                }
            ]
        }
        results = apply_fix(fix_data, root_dir=self.test_dir)
        self.assertEqual(results, ["Deleted test.py"])
        self.assertFalse(self.test_file.exists())

    def test_apply_fix_security_boundary(self):
        fix_data = {
            "changes": [
                {
                    "file_path": "../outside.txt",
                    "action": "create",
                    "content": "dangerous"
                }
            ]
        }
        with self.assertRaises(PermissionError):
            apply_fix(fix_data, root_dir=self.test_dir)

    def test_apply_fix_file_not_found(self):
        fix_data = {
            "changes": [
                {
                    "file_path": "non_existent.py",
                    "action": "update",
                    "content": "content"
                }
            ]
        }
        with self.assertRaises(FileNotFoundError):
            apply_fix(fix_data, root_dir=self.test_dir)

    def test_apply_fix_search_block_not_found(self):
        fix_data = {
            "changes": [
                {
                    "file_path": "test.py",
                    "action": "update",
                    "search_block": "missing",
                    "content": "content"
                }
            ]
        }
        with self.assertRaises(ValueError):
            apply_fix(fix_data, root_dir=self.test_dir)

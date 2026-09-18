import os
import tempfile
import unittest
from zhirterminalassist.files import FileManager

class TestFileManager(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.cwd = self.tmp_dir.name
        self.files = FileManager(self.cwd)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_write_and_read_file(self):
        # Write file
        msg = self.files.write_file("test.txt", "line1\nline2\nline3\n", confirm_overwrite=False)
        self.assertIn("test.txt", msg)
        
        # Read file
        content = self.files.read_file("test.txt")
        self.assertIn("1 | line1", content)
        self.assertIn("2 | line2", content)
        self.assertIn("3 | line3", content)

    def test_edit_file_and_diff(self):
        self.files.write_file("code.py", "def hello():\n    print('hi')\n", confirm_overwrite=False)
        edit_msg = self.files.edit_file("code.py", "print('hi')", "print('world')", confirm_overwrite=False)
        self.assertIn("code.py", edit_msg)
        
        # Verify content updated
        content = self.files.read_file("code.py")
        self.assertIn("print('world')", content)
        
        # Verify session changes tracker
        summary = self.files.get_diff_summary()
        self.assertIn("code.py", summary)
        self.assertIn("+    print('world')", summary)

    def test_list_dir(self):
        self.files.write_file("sub/file1.txt", "content", confirm_overwrite=False)
        listing = self.files.list_dir("sub")
        self.assertIn("file1.txt", listing)

    def test_edit_file_not_unique_error(self):
        self.files.write_file("dup.txt", "dup\ndup\n", confirm_overwrite=False)
        err = self.files.edit_file("dup.txt", "dup", "single", confirm_overwrite=False)
        self.assertIn("appears 2 times", err)

if __name__ == "__main__":
    unittest.main()

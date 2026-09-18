import os
import subprocess
import tempfile
import unittest
from zhirterminalassist.git import GitManager

class TestGitManager(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.cwd = self.tmp_dir.name
        # Initialize real git repo
        subprocess.run(["git", "init"], cwd=self.cwd, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "TestUser"], cwd=self.cwd, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.cwd, check=True)
        self.git = GitManager(self.cwd)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_is_git_repo(self):
        self.assertTrue(self.git.is_git_repo())
        non_git = GitManager("/tmp")
        # /tmp is usually not a git repo or if it is, test a fresh tempdir without git init
        with tempfile.TemporaryDirectory() as empty_dir:
            self.assertFalse(GitManager(empty_dir).is_git_repo())

    def test_status_and_commit(self):
        # Create a file
        test_file = os.path.join(self.cwd, "sample.txt")
        with open(test_file, "w") as f:
            f.write("Hello git")

        status = self.git.get_status()
        self.assertIn("sample.txt", status)

        # Commit
        ok, msg = self.git.commit("Initial test commit")
        self.assertTrue(ok)
        self.assertIn("Initial test commit", msg)

        # Status after commit
        status_after = self.git.get_status()
        self.assertIn("clean", status_after)

if __name__ == "__main__":
    unittest.main()

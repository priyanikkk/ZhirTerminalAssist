import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class GitManager:
    def __init__(self, repo_dir: Optional[str] = None):
        self.repo_dir = repo_dir

    def _run_git(self, args: List[str]) -> Tuple[int, str, str]:
        if not shutil.which("git"):
            return -1, "", "git binary not found"
        try:
            res = subprocess.run(
                ["git"] + args,
                cwd=self.repo_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )
            return res.returncode, res.stdout.strip(), res.stderr.strip()
        except Exception as e:
            return -1, "", str(e)

    def is_git_repo(self) -> bool:
        code, _, _ = self._run_git(["rev-parse", "--is-inside-work-tree"])
        return code == 0

    def get_branch(self) -> str:
        code, out, _ = self._run_git(["branch", "--show-current"])
        return out if code == 0 else "unknown"

    def get_status(self) -> str:
        if not self.is_git_repo():
            return "Not a git repository."
        code, out, _ = self._run_git(["status", "--short"])
        if code != 0:
            return "Failed to get git status."
        if not out:
            return "Working tree clean, nothing to commit."
        return out

    def get_diff(self) -> str:
        if not self.is_git_repo():
            return "Not a git repository."
        code, out, _ = self._run_git(["diff"])
        code_staged, out_staged, _ = self._run_git(["diff", "--cached"])
        
        diffs = []
        if out:
            diffs.append("=== Unstaged Changes ===\n" + out)
        if out_staged:
            diffs.append("=== Staged Changes ===\n" + out_staged)
        return "\n\n".join(diffs) or "No changes detected in Git."

    def commit(self, message: str) -> Tuple[bool, str]:
        if not self.is_git_repo():
            return False, "Not a git repository."
        # Stage all changes
        code, _, err = self._run_git(["add", "."])
        if code != 0:
            return False, f"git add failed: {err}"
        
        code, out, err = self._run_git(["commit", "-m", message])
        if code != 0:
            return False, f"git commit failed: {err or out}"
        return True, out

    def push(self) -> Tuple[bool, str]:
        if not self.is_git_repo():
            return False, "Not a git repository."
        code, out, err = self._run_git(["push"])
        if code != 0:
            return False, f"git push failed: {err or out}"
        return True, out

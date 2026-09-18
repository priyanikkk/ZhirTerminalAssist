import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

class LogAnalyzer:
    @staticmethod
    def fetch_journalctl_errors(lines: int = 60) -> str:
        if not shutil.which("journalctl"):
            return "journalctl binary not found."
        try:
            res = subprocess.run(
                ["journalctl", "-p", "3", "-xb", "-n", str(lines), "--no-pager"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=8
            )
            return res.stdout.strip() or "No error-level entries found in recent systemd journal."
        except Exception as e:
            return f"Failed to retrieve journal: {e}"

    @staticmethod
    def read_file(path: str, max_lines: int = 250) -> str:
        p = Path(path).expanduser().resolve()
        if not p.exists() or not p.is_file():
            return f"Log file not found: {path}"
        try:
            try:
                content = p.read_text(encoding="utf-8", errors="replace")
            except Exception:
                content = p.read_text(encoding="latin-1", errors="replace")
            lines = content.splitlines()
            if len(lines) > max_lines:
                return f"# Showing last {max_lines} lines of {p.name}:\n" + "\n".join(lines[-max_lines:])
            return "\n".join(lines)
        except Exception as e:
            return f"Error reading log file: {e}"

    @staticmethod
    def read_stdin() -> Optional[str]:
        if not sys.stdin.isatty():
            try:
                return sys.stdin.read()
            except Exception:
                return None
        return None

    @staticmethod
    def extract_signatures(log_text: str) -> Dict[str, Any]:
        lines = log_text.splitlines()
        segfaults = [l for l in lines if "segfault" in l.lower() or "segmentation fault" in l.lower()]
        oom = [l for l in lines if "out of memory" in l.lower() or "oom-killer" in l.lower()]
        errors = [l for l in lines if any(k in l.lower() for k in ["error", "crit", "failed", "fatal"])]
        return {
            "total_lines": len(lines),
            "error_count": len(errors),
            "segfaults": segfaults[:5],
            "oom_kills": oom[:5],
            "sample_errors": errors[:8]
        }

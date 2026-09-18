import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

class LogAnalyzer:
    @staticmethod
    def fetch_system_errors(lines: int = 80) -> str:
        if not shutil.which("journalctl"):
            return "journalctl is not available on this system."
        try:
            cmd = ["journalctl", "-p", "3", "-xb", "-n", str(lines), "--no-pager"]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=8)
            if res.stdout.strip():
                return res.stdout.strip()
            return "No critical/error entries found in recent system journal."
        except Exception as e:
            return f"Failed to retrieve system journal: {e}"

    @staticmethod
    def fetch_user_errors(lines: int = 50) -> str:
        if not shutil.which("journalctl"):
            return "journalctl is not available on this system."
        try:
            cmd = ["journalctl", "--user", "-p", "3", "-xb", "-n", str(lines), "--no-pager"]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=8)
            if res.stdout.strip():
                return res.stdout.strip()
            return "No error entries in current user systemd session."
        except Exception as e:
            return f"Failed to retrieve user journal: {e}"

    @staticmethod
    def read_log_file(path: str, max_lines: int = 300) -> str:
        file_path = Path(path).expanduser().resolve()
        if not file_path.exists():
            return f"File does not exist: {path}"
        if not file_path.is_file():
            return f"Path is not a regular file: {path}"

        try:
            # Try reading with utf-8, fallback to latin-1
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                content = file_path.read_text(encoding="latin-1", errors="replace")

            lines = content.splitlines()
            if len(lines) > max_lines:
                return f"# Showing last {max_lines} lines of {file_path.name}:\n" + "\n".join(lines[-max_lines:])
            return "\n".join(lines)
        except Exception as e:
            return f"Error reading log file {path}: {e}"

    @staticmethod
    def extract_summary(log_text: str) -> Dict[str, Any]:
        lines = log_text.splitlines()
        total_lines = len(lines)
        
        # Identify common patterns
        error_lines = []
        warning_lines = []
        segfaults = []
        oom_kills = []
        device_errors = []

        for line in lines:
            lower = line.lower()
            if "segfault" in lower or "segmentation fault" in lower:
                segfaults.append(line)
            elif "out of memory" in lower or "oom-killer" in lower:
                oom_kills.append(line)
            elif any(k in lower for k in ["i/o error", "hardware error", "buffer I/O error"]):
                device_errors.append(line)
            elif any(k in lower for k in ["error", "crit", "alert", "emerg", "failed", "fatal"]):
                error_lines.append(line)
            elif "warn" in lower:
                warning_lines.append(line)

        return {
            "total_lines": total_lines,
            "error_count": len(error_lines),
            "warning_count": len(warning_lines),
            "segfaults": segfaults[:5],
            "oom_kills": oom_kills[:5],
            "device_errors": device_errors[:5],
            "sample_errors": error_lines[:10],
        }

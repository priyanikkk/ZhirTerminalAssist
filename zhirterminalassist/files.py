import difflib
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from rich.console import Console
from rich.syntax import Syntax

from zhirterminalassist.i18n import t

console = Console()

class FileManager:
    def __init__(self, root_dir: Optional[str] = None):
        self.root_dir = Path(root_dir or os.getcwd()).resolve()
        # Track session changes: path -> (original_content, current_content)
        self.session_changes: Dict[str, Tuple[str, str]] = {}

    def resolve_path(self, rel_path: str) -> Tuple[Path, bool]:
        """Resolves path and checks if it is inside the working directory."""
        target = Path(rel_path).expanduser()
        if not target.is_absolute():
            target = (self.root_dir / target).resolve()
        else:
            target = target.resolve()

        is_inside = False
        try:
            target.relative_to(self.root_dir)
            is_inside = True
        except ValueError:
            is_inside = False

        return target, is_inside

    def read_file(self, path_str: str, offset: int = 1, limit: int = 250) -> str:
        target, is_inside = self.resolve_path(path_str)
        if not is_inside:
            console.print(f"[yellow]{t('outside_cwd_warning')}[/yellow]")
            confirm = input().strip().lower()
            if confirm not in ("y", "yes"):
                return "Operation aborted: path outside working directory."

        if not target.exists():
            return f"Error: File not found: {path_str}"
        if not target.is_file():
            return f"Error: Path is a directory: {path_str}"

        try:
            try:
                content = target.read_text(encoding="utf-8", errors="replace")
            except Exception:
                content = target.read_text(encoding="latin-1", errors="replace")
            
            lines = content.splitlines()
            total_lines = len(lines)
            start = max(1, offset)
            end = min(total_lines, start + limit - 1)
            
            result_lines = []
            for i in range(start - 1, end):
                result_lines.append(f"{i + 1:4d} | {lines[i]}")
            
            header = f"# File: {target.name} (lines {start}-{end} of {total_lines})\n"
            return header + "\n".join(result_lines)
        except Exception as e:
            return f"Error reading file {path_str}: {e}"

    def render_diff(self, file_path_str: str, old_content: str, new_content: str) -> str:
        old_lines = old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)
        diff = list(difflib.unified_diff(
            old_lines, new_lines,
            fromfile=f"a/{file_path_str}",
            tofile=f"b/{file_path_str}",
            n=3
        ))
        if not diff:
            return "(No changes)"
        return "".join(diff)

    def write_file(self, path_str: str, content: str, confirm_overwrite: bool = True) -> str:
        target, is_inside = self.resolve_path(path_str)
        if not is_inside:
            console.print(f"[yellow]{t('outside_cwd_warning')}[/yellow]")
            confirm = input().strip().lower()
            if confirm not in ("y", "yes"):
                return "Operation aborted: path outside working directory."

        old_content = ""
        is_update = target.exists()
        if is_update:
            try:
                old_content = target.read_text(encoding="utf-8", errors="replace")
            except Exception:
                pass

        diff_str = self.render_diff(path_str, old_content, content)
        if is_update and diff_str != "(No changes)":
            console.print(f"\n[bold cyan]● Editing {path_str}[/bold cyan]\n")
            for line in diff_str.splitlines():
                if line.startswith("+") and not line.startswith("+++"):
                    console.print(f"[green]{line}[/green]")
                elif line.startswith("-") and not line.startswith("---"):
                    console.print(f"[red]{line}[/red]")
                else:
                    console.print(f"[dim]{line}[/dim]")
            
            if confirm_overwrite:
                confirm = input(f"\n{t('apply_changes')}").strip().lower()
                if confirm in ("n", "no"):
                    return f"Cancelled modifying {path_str}"

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

        # Track session changes
        orig = self.session_changes.get(str(target), (old_content, ""))[0]
        self.session_changes[str(target)] = (orig, content)

        if is_update:
            return t("file_updated", path=path_str)
        return t("file_created", path=path_str)

    def edit_file(self, path_str: str, old_str: str, new_str: str, confirm_overwrite: bool = True) -> str:
        target, is_inside = self.resolve_path(path_str)
        if not target.exists():
            return f"Error: File not found: {path_str}"

        try:
            content = target.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return f"Error reading file {path_str}: {e}"

        if old_str not in content:
            return f"Error: String to replace not found in {path_str}"

        count = content.count(old_str)
        if count > 1:
            return f"Error: String to replace is ambiguous; appears {count} times in {path_str}"

        new_content = content.replace(old_str, new_str, 1)
        return self.write_file(path_str, new_content, confirm_overwrite=confirm_overwrite)

    def list_dir(self, path_str: str = ".", max_depth: int = 2) -> str:
        target, is_inside = self.resolve_path(path_str)
        if not target.exists():
            return f"Error: Directory not found: {path_str}"
        if not target.is_dir():
            return f"Error: Not a directory: {path_str}"

        entries = []
        try:
            for root, dirs, files in os.walk(target):
                rel_root = os.path.relpath(root, target)
                depth = 0 if rel_root == "." else rel_root.count(os.sep) + 1
                if depth > max_depth:
                    continue
                # Skip hidden/venv
                dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("__pycache__", "venv", "node_modules")]
                indent = "  " * depth
                folder_name = os.path.basename(root) if depth > 0 else "."
                entries.append(f"{indent}📁 {folder_name}/")
                for f in sorted(files):
                    if not f.startswith("."):
                        entries.append(f"{indent}  📄 {f}")
            return "\n".join(entries[:100])
        except Exception as e:
            return f"Error listing directory: {e}"

    def get_diff_summary(self) -> str:
        if not self.session_changes:
            return t("no_diff")

        out = []
        for path_str, (old_c, new_c) in self.session_changes.items():
            rel = os.path.relpath(path_str, self.root_dir)
            out.append(f"\n[bold cyan]--- {rel} ---[/bold cyan]")
            diff = self.render_diff(rel, old_c, new_c)
            for line in diff.splitlines():
                if line.startswith("+") and not line.startswith("+++"):
                    out.append(f"[green]{line}[/green]")
                elif line.startswith("-") and not line.startswith("---"):
                    out.append(f"[red]{line}[/red]")
                else:
                    out.append(f"[dim]{line}[/dim]")
        return "\n".join(out)

import json
import os
from typing import Any, Dict, List, Optional
from rich.console import Console
from rich.panel import Panel

from zhirterminalassist.ai import ToolCall, get_ai_provider
from zhirterminalassist.executor import CommandExecutor
from zhirterminalassist.files import FileManager
from zhirterminalassist.git import GitManager
from zhirterminalassist.history import get_history_manager
from zhirterminalassist.i18n import t

console = Console()

class AgentSession:
    def __init__(self, working_dir: Optional[str] = None):
        self.working_dir = os.path.abspath(working_dir or os.getcwd())
        self.files = FileManager(self.working_dir)
        self.git = GitManager(self.working_dir)
        self.executor = CommandExecutor()
        self.history_mgr = get_history_manager()
        self.messages: List[Dict[str, Any]] = []

    def reset_context(self):
        self.messages.clear()
        self.files.session_changes.clear()

    def run_turn(self, user_prompt: str, max_steps: int = 15):
        self.messages.append({"role": "user", "content": user_prompt})
        provider = get_ai_provider()

        for step in range(max_steps):
            content, tool_calls, error = provider.send_messages(self.messages, cwd=self.working_dir)

            if error:
                console.print(f"\n[bold red]✗ {t('error')}:[/bold red] {error}\n")
                break

            # If there's text content, output it
            if content and content.strip():
                # Avoid printing tool pseudo-tags directly if they were parsed
                clean_text = content.strip()
                if not tool_calls or not clean_text.startswith("<tool"):
                    console.print(f"\n[bold white]{clean_text}[/bold white]\n")

            if not tool_calls:
                if content:
                    self.messages.append({"role": "assistant", "content": content})
                    self.history_mgr.add_interaction(user_prompt, content, [])
                break

            # Process tool calls
            # Record assistant turn with tool calls
            serialized_tool_calls = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.name,
                        "arguments": json.dumps(tc.arguments, ensure_ascii=False)
                    }
                }
                for tc in tool_calls
            ]
            self.messages.append({
                "role": "assistant",
                "content": content or "",
                "tool_calls": serialized_tool_calls
            })

            # Execute each tool
            for tc in tool_calls:
                tool_output = self._execute_tool(tc)
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": tc.name,
                    "content": str(tool_output)
                })

    def _execute_tool(self, tc: ToolCall) -> str:
        name = tc.name
        args = tc.arguments or {}

        if name == "bash":
            cmd = args.get("command", "")
            console.print(f"[bold cyan]● Running command...[/bold cyan]")
            console.print(f"[bold white]$ {cmd}[/bold white]")
            
            # Execute with security checks and prompt
            code, output = self.executor.run_agent_command(cmd, cwd=self.working_dir)
            if code == 0:
                console.print(f"[bold green]✓ {t('done')}[/bold green]\n")
            else:
                console.print(f"[bold red]✗ {t('error')} (code {code})[/bold red]\n")
            return f"Exit code: {code}\nOutput:\n{output}"

        elif name == "read_file":
            path = args.get("path", "")
            offset = args.get("offset", 1)
            limit = args.get("limit", 250)
            console.print(f"[bold cyan]● Inspecting {path}...[/bold cyan]")
            res = self.files.read_file(path, offset=offset, limit=limit)
            console.print(f"[green]✓ Read {path}[/green]\n")
            return res

        elif name == "write_file":
            path = args.get("path", "")
            content = args.get("content", "")
            console.print(f"[bold cyan]● Writing file {path}...[/bold cyan]")
            res = self.files.write_file(path, content, confirm_overwrite=True)
            console.print(f"[green]✓ {res}[/green]\n")
            return res

        elif name == "edit_file":
            path = args.get("path", "")
            old_str = args.get("old_str", "")
            new_str = args.get("new_str", "")
            console.print(f"[bold cyan]● Editing {path}...[/bold cyan]")
            res = self.files.edit_file(path, old_str, new_str)
            console.print(f"[green]✓ {res}[/green]\n")
            return res

        elif name == "list_dir":
            path = args.get("path", ".")
            console.print(f"[bold cyan]● Inspecting directory '{path}'...[/bold cyan]")
            res = self.files.list_dir(path)
            console.print(f"[green]✓ Listed {path}[/green]\n")
            return res

        elif name == "git_status":
            console.print(f"[bold cyan]● Checking Git status...[/bold cyan]")
            res = self.git.get_status()
            console.print(f"[dim]{res}[/dim]\n")
            return res

        elif name == "git_diff":
            console.print(f"[bold cyan]● Inspecting Git diff...[/bold cyan]")
            res = self.git.get_diff()
            console.print(f"[dim]{res[:500]}[/dim]\n")
            return res

        elif name == "git_commit":
            msg = args.get("message", "")
            console.print(f"\n[bold yellow]● Git Commit Proposal[/bold yellow]")
            console.print(f"Message: [bold white]\"{msg}\"[/bold white]")
            confirm = input(t("git_commit_confirm")).strip().lower()
            if confirm in ("n", "no"):
                console.print(f"[yellow]{t('cancelled')}[/yellow]\n")
                return "User cancelled the git commit."
            ok, out = self.git.commit(msg)
            if ok:
                console.print(f"[bold green]✓ {t('git_commit_success', commit=msg)}[/bold green]\n")
                return f"Commit succeeded: {out}"
            else:
                console.print(f"[bold red]✗ {out}[/bold red]\n")
                return f"Commit failed: {out}"

        return f"Unknown tool: {name}"

import os
import sys
from pathlib import Path
from typing import List, Optional
try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
    from prompt_toolkit.formatted_text import HTML
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.styles import Style
    HAS_PROMPT_TOOLKIT = True
except ImportError:
    HAS_PROMPT_TOOLKIT = False

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from zhirterminalassist.agent import AgentSession
from zhirterminalassist.config import DATA_DIR, get_config, mask_api_key
from zhirterminalassist.i18n import get_language, set_language, t
from zhirterminalassist.system import get_system_info

console = Console()

def print_agent_banner(working_dir: str):
    cfg = get_config()
    model = cfg.get("model", "unknown")
    lang = get_language()
    lang_display = "ru (Русский)" if lang == "ru" else "en (English)"

    banner = Panel(
        "[bold cyan]ZhirTerminalAssist[/bold cyan]\n"
        "[dim]AI Terminal Agent[/dim]",
        border_style="cyan",
        width=52
    )
    console.print(banner)
    console.print(f"  [bold cyan]{t('model_label')}:[/bold cyan]     {model}")
    console.print(f"  [bold cyan]{t('directory_label')}:[/bold cyan] {working_dir}")
    console.print(f"  [bold cyan]{t('language_label')}:[/bold cyan]  {lang_display}\n")
    console.print(f"  [dim]Type /help for available commands[/dim]\n")

class TerminalUI:
    def __init__(self, agent_session: AgentSession):
        self.agent = agent_session
        self.config = get_config()
        self.prompt_session = None
        
        if HAS_PROMPT_TOOLKIT:
            history_file = DATA_DIR / "agent_prompt_history.txt"
            self.prompt_session = PromptSession(
                history=FileHistory(str(history_file)),
                auto_suggest=AutoSuggestFromHistory(),
                enable_history_search=True
            )
        else:
            try:
                import readline
                history_file = DATA_DIR / "agent_readline_history.txt"
                if history_file.exists():
                    readline.read_history_file(str(history_file))
            except Exception:
                pass

    def run(self):
        print_agent_banner(self.agent.working_dir)

        while True:
            try:
                if self.prompt_session is not None:
                    prompt_text = HTML('<style color="#00d7ff" bold="true">zhir </style><style color="#00afff" bold="true">❯ </style>')
                    user_input = self.prompt_session.prompt(prompt_text).strip()
                else:
                    user_input = input(f"{t('prompt_symbol')}").strip()
            except KeyboardInterrupt:
                console.print(f"\n[yellow]{t('cancelled')}[/yellow]")
                continue
            except EOFError:
                console.print(f"\n[dim]{t('goodbye')}[/dim]")
                break

            if not user_input:
                continue

            # Check for slash commands
            if user_input.startswith("/"):
                should_continue = self.handle_slash_command(user_input)
                if not should_continue:
                    break
                continue

            # Run agent turn
            self.agent.run_turn(user_input)

    def handle_slash_command(self, cmd_line: str) -> bool:
        parts = cmd_line.strip().split()
        cmd = parts[0].lower()
        args = parts[1:]

        if cmd in ("/exit", "/quit", "/q"):
            console.print(f"[dim]{t('goodbye')}[/dim]")
            return False

        elif cmd == "/clear":
            os.system("clear")
            print_agent_banner(self.agent.working_dir)

        elif cmd in ("/help", "/?"):
            self._cmd_help()

        elif cmd == "/status":
            self._cmd_status()

        elif cmd == "/model":
            self._cmd_model(args)

        elif cmd == "/config":
            self._cmd_config(args)

        elif cmd == "/history":
            self._cmd_history(args)

        elif cmd == "/commands":
            self._cmd_commands()

        elif cmd == "/files":
            path = args[0] if args else "."
            self._cmd_files(path)

        elif cmd == "/diff":
            self._cmd_diff()

        elif cmd == "/reset":
            self.agent.reset_context()
            console.print(f"[bold green]✓ {t('cmd_reset')}[/bold green]\n")

        elif cmd == "/language":
            self._cmd_language(args)

        else:
            console.print(f"[yellow]Unknown command: {cmd}. Type /help for available commands.[/yellow]\n")

        return True

    def _cmd_help(self):
        table = Table(title=t("help_header"), show_header=True, header_style="bold cyan", border_style="dim")
        table.add_column("Command", style="bold yellow", width=22)
        table.add_column("Description", style="white")

        commands = [
            ("/help", t("cmd_help")),
            ("/clear", t("cmd_clear")),
            ("/status", t("cmd_status")),
            ("/model [name]", t("cmd_model")),
            ("/config [show|set <k> <v>]", t("cmd_config")),
            ("/history [search]", t("cmd_history")),
            ("/commands", t("cmd_commands")),
            ("/files [path]", t("cmd_files")),
            ("/diff", t("cmd_diff")),
            ("/reset", t("cmd_reset")),
            ("/language [ru|en]", t("cmd_language")),
            ("/exit, /quit", t("cmd_exit")),
        ]
        for c, desc in commands:
            table.add_row(c, desc)
        console.print(table)
        console.print("")

    def _cmd_status(self):
        info = get_system_info(refresh_cpu=True)
        git_branch = self.agent.git.get_branch() or "not a git repo"
        table = Table(title="System & Session Status", show_header=True, header_style="bold cyan")
        table.add_column("Property", width=20)
        table.add_column("Value")

        table.add_row("OS", info.os_pretty_name)
        table.add_row("Kernel", info.kernel)
        table.add_row("CPU", f"{info.cpu_model} ({info.cpu_usage_percent}%)")
        table.add_row("RAM", f"{info.ram_used_gb} / {info.ram_total_gb} GB ({info.ram_percent}%)")
        table.add_row("Working Dir", self.agent.working_dir)
        table.add_row("Git Branch", git_branch)
        table.add_row("AI Model", self.config.get("model", "unknown"))
        table.add_row("Provider", self.config.get("provider", "openrouter"))
        table.add_row("Session Messages", str(len(self.agent.messages)))
        table.add_row("Language", get_language())
        console.print(table)
        console.print("")

    def _cmd_model(self, args: List[str]):
        if args:
            new_model = args[0]
            self.config.set("model", new_model)
            console.print(f"[bold green]✓ Model set to: {new_model}[/bold green]\n")
        else:
            current = self.config.get("model", "unknown")
            console.print(f"\n[bold cyan]Current model:[/bold cyan] [bold white]{current}[/bold white]\n")
            console.print("[dim]Popular models you can set with '/model <name>':[/dim]")
            console.print("  • anthropic/claude-3.7-sonnet")
            console.print("  • anthropic/claude-3.5-haiku")
            console.print("  • google/gemini-2.5-flash")
            console.print("  • google/gemini-2.5-pro")
            console.print("  • openai/gpt-4o")
            console.print("  • openai/gpt-4o-mini")
            console.print("  • deepseek/deepseek-chat")
            console.print("  • qwen2.5:latest (Ollama local)\n")

    def _cmd_config(self, args: List[str]):
        if not args or args[0] in ("show", "list"):
            table = Table(title="Configuration", show_header=True, header_style="bold cyan")
            table.add_column("Setting", width=20)
            table.add_column("Value")
            table.add_row("provider", str(self.config.get("provider")))
            table.add_row("model", str(self.config.get("model")))
            table.add_row("base_url", str(self.config.get("base_url")))
            table.add_row("api_key", mask_api_key(str(self.config.get("api_key", ""))))
            table.add_row("temperature", str(self.config.get("temperature")))
            table.add_row("max_tokens", str(self.config.get("max_tokens")))
            table.add_row("auto_execute_safe", str(self.config.get("auto_execute_safe")))
            table.add_row("language", str(self.config.get("language")))
            console.print(table)
            console.print("[dim]To change: /config set <key> <value>[/dim]\n")
        elif args[0] == "set" and len(args) >= 3:
            k, v = args[1], " ".join(args[2:])
            try:
                self.config.set(k, v)
                console.print(f"[bold green]✓ Set {k} = {v if 'key' not in k else mask_api_key(v)}[/bold green]\n")
            except Exception as e:
                console.print(f"[bold red]✗ Error: {e}[/bold red]\n")
        else:
            console.print("[yellow]Usage: /config [show | set <key> <value>][/yellow]\n")

    def _cmd_history(self, args: List[str]):
        from zhirterminalassist.history import get_history_manager
        hist = get_history_manager()
        search = args[0] if args else ""
        entries = hist.get_history(limit=15, search=search)
        if not entries:
            console.print("[yellow]No command history found.[/yellow]\n")
            return

        table = Table(title="Recent Execution History", show_header=True, header_style="bold cyan")
        table.add_column("Time", width=19)
        table.add_column("Risk", width=8)
        table.add_column("Status", width=8)
        table.add_column("Command")

        for e in entries:
            stat_color = "green" if e["status"] == "SUCCESS" else "red"
            risk_color = "green" if e["risk_level"] == "SAFE" else ("yellow" if e["risk_level"] == "CONFIRM" else "red")
            ts = e["created_at"][:19].replace("T", " ")
            table.add_row(
                ts,
                f"[{risk_color}]{e['risk_level']}[/{risk_color}]",
                f"[{stat_color}]{e['status']}[/{stat_color}]",
                e["command"]
            )
        console.print(table)
        console.print("")

    def _cmd_commands(self):
        table = Table(title=t("cmd_commands"), show_header=True, header_style="bold cyan")
        table.add_column("Tool", style="bold cyan", width=18)
        table.add_column("Arguments", style="dim yellow", width=30)
        table.add_column("Description")

        tools = [
            ("bash", "command: str", "Execute a bash shell command with security validation"),
            ("read_file", "path: str, offset: int, limit: int", "Read content of a file with line numbers"),
            ("write_file", "path: str, content: str", "Write or overwrite a file with user confirmation"),
            ("edit_file", "path: str, old_str: str, new_str: str", "Replace exact text in file with interactive diff preview"),
            ("list_dir", "path: str", "List contents of directory recursively"),
            ("git_status", "(none)", "Show current git status and changed files"),
            ("git_diff", "(none)", "Show uncommitted git diff"),
            ("git_commit", "message: str", "Create a git commit with review and confirmation"),
        ]
        for t_name, args, desc in tools:
            table.add_row(t_name, args, desc)
        console.print(table)
        console.print("")

    def _cmd_files(self, path: str):
        console.print(f"[bold cyan]● Listing {path}:[/bold cyan]")
        res = self.agent.files.list_dir(path)
        console.print(f"[dim]{res}[/dim]\n")

    def _cmd_diff(self):
        # 1. Git diff
        git_diff = self.agent.git.get_diff() if self.agent.git.is_git_repo() else ""
        session_diff = self.agent.files.get_diff_summary()

        if not git_diff and not session_diff:
            console.print(f"[yellow]{t('git_clean')}[/yellow]\n")
            return

        if session_diff:
            console.print(Panel(session_diff, title="Session File Changes", border_style="cyan"))

        if git_diff:
            console.print(Panel(git_diff[:4000], title="Git Diff", border_style="magenta"))
        console.print("")

    def _cmd_language(self, args: List[str]):
        if args:
            lang = args[0].lower()
            set_language(lang)
            self.config.set("language", lang)
            console.print(f"[bold green]✓ {t('language_changed')}[/bold green]\n")
        else:
            console.print(f"[bold cyan]{t('language_select_title')}[/bold cyan]")
            console.print("  1) Русский (ru)")
            console.print("  2) English (en)")
            try:
                choice = input("Select [1/2]: ").strip()
                selected = "ru" if choice in ("1", "ru", "русский") else "en"
                set_language(selected)
                self.config.set("language", selected)
                console.print(f"[bold green]✓ {t('language_changed')}[/bold green]\n")
            except (KeyboardInterrupt, EOFError):
                console.print(f"\n[yellow]{t('cancelled')}[/yellow]\n")

import os
import readline
import sys
from typing import List, Optional
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from zhirterminalassist import __version__
from zhirterminalassist.ai import get_ai_client
from zhirterminalassist.completion import get_completion_script
from zhirterminalassist.config import get_config, mask_api_key, setup_logging
from zhirterminalassist.diagnostics import DiagnosticsRunner
from zhirterminalassist.executor import CommandExecutor
from zhirterminalassist.history import get_history_manager
from zhirterminalassist.logs import LogAnalyzer
from zhirterminalassist.security import SecurityChecker
from zhirterminalassist.system import get_system_info

console = Console()

def print_banner(info):
    banner_text = (
        "[bold cyan]⚡ ZhirTerminalAssist[/bold cyan]\n"
        "[dim]AI Linux Terminal Assistant[/dim]"
    )
    console.print(Panel(banner_text, border_style="cyan", width=62))

    gpu_short = info.gpus[0] if info.gpus else "Generic"
    if len(gpu_short) > 34:
        gpu_short = gpu_short[:31] + "..."

    cpu_short = info.cpu_model
    if len(cpu_short) > 34:
        cpu_short = cpu_short[:31] + "..."

    tree_text = (
        f"  [bold]System[/bold]\n"
        f"  ├─ [cyan]OS[/cyan]      {info.os_pretty_name}\n"
        f"  ├─ [cyan]Kernel[/cyan]  {info.kernel}\n"
        f"  ├─ [cyan]CPU[/cyan]     {cpu_short}\n"
        f"  ├─ [cyan]GPU[/cyan]     {gpu_short}\n"
        f"  ├─ [cyan]RAM[/cyan]     {info.ram_total_gb} GB\n"
        f"  └─ [cyan]Shell[/cyan]   {info.shell}"
    )
    console.print(tree_text)
    console.print("\n[dim]Type your question, or 'exit' / Ctrl+C to quit.[/dim]\n")

def cmd_system():
    info = get_system_info(refresh_cpu=True)
    root_disk = next((d for d in info.disks if d['mountpoint'] == '/'), info.disks[0] if info.disks else None)
    disk_str = f"{root_disk['used_gb']} / {root_disk['total_gb']} GB" if root_disk else "Unknown"

    console.print("\n[bold cyan]SYSTEM[/bold cyan]\n")
    console.print(f"OS        [bold]{info.os_pretty_name}[/bold]")
    console.print(f"Kernel    {info.kernel} ({info.arch})")
    console.print(f"CPU       {info.cpu_model}")
    console.print(f"GPU       {'; '.join(info.gpus)}")
    console.print(f"RAM       {info.ram_used_gb} / {info.ram_total_gb} GB")
    console.print(f"Disk      {disk_str}")
    console.print(f"Shell     {info.shell}")
    console.print(f"DE        {info.desktop_environment}")
    console.print(f"Session   {info.display_server}\n")

    console.print(f"CPU usage     [bold green]{info.cpu_usage_percent}%[/bold green]")
    console.print(f"Memory        {info.ram_used_gb} / {info.ram_total_gb} GB ({info.ram_percent}%)")
    if root_disk:
        console.print(f"Disk          {root_disk['used_gb']} / {root_disk['total_gb']} GB ({root_disk['percent']}%)")
    console.print(f"Uptime        {info.uptime_human}\n")

def cmd_diagnose(category: str = "all", ask_ai: bool = False):
    results = DiagnosticsRunner.run_category(category)
    for cat_name, checks in results.items():
        table = Table(title=f"Diagnostics: {cat_name}", show_header=True, header_style="bold cyan")
        table.add_column("Check", width=26)
        table.add_column("Status", width=10)
        table.add_column("Details")
        table.add_column("Action / Command")

        for item in checks:
            if item.status == "OK":
                stat = "[bold green]✓ OK[/bold green]"
            elif item.status == "WARN":
                stat = "[bold yellow]⚠ WARN[/bold yellow]"
            else:
                stat = "[bold red]✗ FAIL[/bold red]"

            action_text = ""
            if item.suggested_action:
                action_text += f"[italic]{item.suggested_action}[/italic]\n"
            if item.command:
                action_text += f"[cyan]`{item.command}`[/cyan]"

            table.add_row(item.name, stat, item.details, action_text.strip())

        console.print(table)
        console.print("")

    if ask_ai:
        report = DiagnosticsRunner.format_report_markdown(results)
        console.print("[cyan]🤖 Analyzing diagnostics with AI...[/cyan]\n")
        client = get_ai_client()
        resp = client.query(f"Analyze these diagnostic results and propose actions:\n\n{report}")
        if resp.is_success:
            console.print(Panel(Markdown(resp.content), title="AI Diagnostic Analysis", border_style="cyan"))
            if resp.commands:
                CommandExecutor.execute_list(resp.commands)
        else:
            console.print(f"[red]{resp.error_message}[/red]\n{resp.error_details}")

def cmd_explain(command_str: str):
    info = SecurityChecker.explain_command_local(command_str)
    console.print("\n[bold cyan]COMMAND[/bold cyan]\n")
    console.print(f"  {info['command']}\n")

    console.print("[bold cyan]BREAKDOWN[/bold cyan]\n")
    for token, desc in info["breakdown"]:
        console.print(f"[bold yellow]{token}[/bold yellow]")
        console.print(f"  {desc}\n")

    risk_style = "green" if "Low" in info["risk"] else ("yellow" if "Medium" in info["risk"] else "red")
    console.print("[bold cyan]RISK[/bold cyan]")
    console.print(f"  [{risk_style}]{info['risk']}[/{risk_style}]\n")

    # Ask AI for extended context if key exists
    config = get_config()
    if config.get("api_key") or config.get("provider") == "local":
        client = get_ai_client()
        resp = client.query(f"Explain this Linux command in detail: `{command_str}`")
        if resp.is_success:
            console.print(Panel(Markdown(resp.content), title="Detailed AI Explanation", border_style="blue"))

def cmd_logs(path: Optional[str] = None):
    if path:
        content = LogAnalyzer.read_file(path)
        title = f"Log File: {path}"
    else:
        content = LogAnalyzer.fetch_journalctl_errors(lines=70)
        title = "Recent Systemd Journal Errors"

    console.print(Panel(content[:4000], title=title, border_style="magenta"))
    summary = LogAnalyzer.extract_signatures(content)
    console.print(f"\n[dim]Total Lines: {summary['total_lines']} | Error Lines: {summary['error_count']} | Segfaults: {len(summary['segfaults'])} | OOMs: {len(summary['oom_kills'])}[/dim]")

def cmd_analyze(input_text: Optional[str] = None):
    if not input_text:
        input_text = LogAnalyzer.read_stdin()

    if not input_text:
        console.print("[yellow]Enter or paste text/log to analyze (press Ctrl+D when finished):[/yellow]")
        try:
            input_text = sys.stdin.read()
        except (KeyboardInterrupt, EOFError):
            return

    if not input_text.strip():
        console.print("[red]No input provided to analyze.[/red]")
        return

    console.print("\n[cyan]🔍 Analyzing log stream with AI...[/cyan]\n")
    client = get_ai_client()
    prompt = (
        "Analyze this Linux log snippet. Identify root causes, group any errors, "
        f"explain what happened in plain language, and suggest fixing commands:\n\n```text\n{input_text[:6000]}\n```"
    )
    resp = client.query(prompt)
    if resp.is_success:
        console.print(Panel(Markdown(resp.content), title="AI Log Root Cause Analysis", border_style="green"))
        if resp.commands:
            CommandExecutor.execute_list(resp.commands)
    else:
        console.print(f"[red]{resp.error_message}[/red]\n{resp.error_details}")

def cmd_history(search: str = ""):
    hist = get_history_manager()
    entries = hist.get_history(limit=25, search=search)
    if not entries:
        console.print("[yellow]No command history found.[/yellow]")
        return

    table = Table(title="Execution History", show_header=True, header_style="bold cyan")
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

def cmd_config(args: List[str]):
    config = get_config()
    if not args or args[0] in ("show", "list"):
        table = Table(title="ZhirTerminalAssist Configuration", show_header=True, header_style="bold cyan")
        table.add_column("Setting", width=20)
        table.add_column("Value")

        table.add_row("provider", config.get("provider"))
        table.add_row("model", config.get("model"))
        table.add_row("base_url", config.get("base_url"))
        table.add_row("api_key", mask_api_key(config.get("api_key", "")))
        table.add_row("temperature", str(config.get("temperature")))
        table.add_row("max_tokens", str(config.get("max_tokens")))
        console.print(table)
        console.print("\n[dim]To change a setting: zhirta config set <key> <value>[/dim]\n")
        return

    action = args[0]
    if action == "set" and len(args) >= 3:
        key, val = args[1], " ".join(args[2:])
        try:
            config.set(key, val)
            console.print(f"[green]✓ Successfully set {key} = {val if 'key' not in key else mask_api_key(val)}[/green]")
        except Exception as e:
            console.print(f"[red]Error setting {key}: {e}[/red]")
    elif action == "get" and len(args) >= 2:
        val = config.get(args[1], "<unset>")
        console.print(f"{args[1]}: {val if 'key' not in args[1] else mask_api_key(val)}")
    else:
        console.print("[yellow]Usage: zhirta config [set <key> <value> | get <key>][/yellow]")

def cmd_interactive():
    info = get_system_info(refresh_cpu=False)
    print_banner(info)
    client = get_ai_client()
    hist_mgr = get_history_manager()
    conversation_history = []

    while True:
        try:
            query = input("\n[zhir] > ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Goodbye![/yellow]")
            break

        if not query:
            continue
        if query.lower() in ("exit", "quit", "q"):
            console.print("[dim]Exiting...[/dim]")
            break
        if query.lower() == "clear":
            os.system("clear")
            print_banner(info)
            continue
        if query.lower() == "system":
            cmd_system()
            continue
        if query.lower() == "diagnose":
            cmd_diagnose()
            continue

        console.print("  [dim cyan]🔍 Анализирую запрос и состояние системы...[/dim cyan]\n")
        resp = client.query(query, history=conversation_history)
        if resp.is_success:
            conversation_history.append({"role": "user", "content": query})
            conversation_history.append({"role": "assistant", "content": resp.content})
            hist_mgr.add_interaction(query, resp.content, resp.commands)

            console.print(Panel(Markdown(resp.content), title="AI Assistant", border_style="cyan"))
            if resp.commands:
                CommandExecutor.execute_list(resp.commands)
        else:
            console.print(Panel(
                f"[bold red]{resp.error_message}[/bold red]\n\n{resp.error_details}",
                title="AI Error",
                border_style="red"
            ))

def print_help():
    help_text = f"""
[bold cyan]ZhirTerminalAssist[/bold cyan] v{__version__}
[dim]Intelligent AI Linux Terminal Assistant and Diagnostics[/dim]

[bold]USAGE:[/bold]
  zhirta                            Start interactive REPL terminal session
  zhirta "<question or query>"      Ask a one-shot question to the AI assistant
  zhirta system                     Show system telemetry, hardware & resource usage
  zhirta diagnose [category]        Run system diagnostics (audio, network, gpu, etc.)
  zhirta explain "<command>"        Break down a Linux command, its flags, and risks
  zhirta logs [file.log]            View systemd journal error logs or custom file
  zhirta analyze                    Analyze stdin pipe with AI (e.g. dmesg | zhirta analyze)
  zhirta history                    Show execution history table
  zhirta config [set key val]       View or update settings (model, api-key, base-url)
  zhirta completion [shell]         Generate shell completion script (bash, zsh, fish)
  zhirta version                    Show version information
"""
    console.print(help_text)

def main():
    setup_logging()
    args = sys.argv[1:]

    # Check for stdin pipe: e.g. cat error.log | zhirta analyze
    if not sys.stdin.isatty():
        if not args or args[0] == "analyze":
            cmd_analyze()
            return

    if not args:
        cmd_interactive()
        return

    cmd = args[0].lower()

    if cmd in ("--version", "-v", "version"):
        console.print(f"ZhirTerminalAssist version [bold cyan]{__version__}[/bold cyan]")
        return

    if cmd in ("--help", "-h", "help"):
        print_help()
        return

    if cmd in ("system", "--system", "-s"):
        cmd_system()
        return

    if cmd in ("diagnose", "--diagnose", "-d"):
        category = args[1] if len(args) > 1 and not args[1].startswith("-") else "all"
        ask_ai = "--ai" in args
        cmd_diagnose(category=category, ask_ai=ask_ai)
        return

    if cmd in ("explain", "--explain", "-e"):
        if len(args) < 2:
            console.print("[red]Please specify the command to explain. Example: zhirta explain 'sudo pacman -Syu'[/red]")
            return
        cmd_explain(" ".join(args[1:]))
        return

    if cmd in ("logs", "--logs", "-l"):
        path = args[1] if len(args) > 1 else None
        cmd_logs(path)
        return

    if cmd == "analyze":
        path = args[1] if len(args) > 1 else None
        if path:
            text = LogAnalyzer.read_file(path)
            cmd_analyze(text)
        else:
            cmd_analyze()
        return

    if cmd == "history":
        search = args[1] if len(args) > 1 else ""
        cmd_history(search)
        return

    if cmd == "config":
        cmd_config(args[1:])
        return

    if cmd == "completion":
        shell = args[1] if len(args) > 1 else "bash"
        print(get_completion_script(shell))
        return

    # Fallback: treat all arguments as a direct natural language question
    query = " ".join(args)
    client = get_ai_client()
    hist_mgr = get_history_manager()
    console.print(f"\n[bold cyan]Query:[/bold cyan] {query}")
    console.print("  [dim]Analyzing system state and contacting AI...[/dim]\n")

    resp = client.query(query)
    if resp.is_success:
        hist_mgr.add_interaction(query, resp.content, resp.commands)
        console.print(Panel(Markdown(resp.content), title="AI Assistant", border_style="cyan"))
        if resp.commands:
            CommandExecutor.execute_list(resp.commands)
    else:
        console.print(Panel(
            f"[bold red]{resp.error_message}[/bold red]\n\n{resp.error_details}",
            title="AI Error",
            border_style="red"
        ))

if __name__ == "__main__":
    main()

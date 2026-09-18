import argparse
import sys
from rich.console import Console
from rich.markdown import Markdown
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table

from zhirterminalassist.ai.client import get_ai_client
from zhirterminalassist.ai.prompt import get_system_prompt
from zhirterminalassist.config import get_config, setup_logging
from zhirterminalassist.storage.history_db import get_history_db
from zhirterminalassist.system.diagnostics import DiagnosticsRunner
from zhirterminalassist.system.info import format_system_summary_for_ai, get_system_info
from zhirterminalassist.system.security import RiskLevel, SecurityChecker

console = Console()

def cmd_system():
    info = get_system_info(refresh_cpu=True)
    table = Table(title="💻 System Hardware & OS Summary", show_header=True, header_style="bold cyan")
    table.add_column("Property", style="dim", width=24)
    table.add_column("Value", style="bold")

    table.add_row("Operating System", f"{info.os_pretty_name} (ID: {info.os_id})")
    table.add_row("Kernel & Arch", f"{info.kernel} ({info.arch})")
    table.add_row("Desktop & Display", f"{info.desktop_environment} ({info.display_server})")
    table.add_row("Hostname & Shell", f"{info.hostname} ({info.shell})")
    table.add_row("CPU Model", f"{info.cpu_model} ({info.cpu_cores_logical} cores, {info.cpu_usage_percent}% load)")
    table.add_row("RAM Usage", f"{info.ram_used_gb} / {info.ram_total_gb} GB ({info.ram_percent}%)")
    table.add_row("Swap Usage", f"{info.swap_used_gb} / {info.swap_total_gb} GB ({info.swap_percent}%)")
    
    for d in info.disks[:3]:
        table.add_row(f"Disk ({escape(d['mountpoint'])})", f"{d['used_gb']}/{d['total_gb']} GB ({d['percent']}%) on {escape(d['device'])}")
    
    table.add_row("GPU(s)", "\n".join(info.gpus))
    table.add_row("Package Managers", ", ".join(info.available_package_managers) or "None detected")
    table.add_row("Uptime", info.uptime_human)

    console.print(table)

def cmd_diagnose(analyze_with_ai: bool = False):
    console.print("[bold cyan]🔍 Running Linux System Diagnostics...[/bold cyan]\n")
    results = DiagnosticsRunner.run_all()
    
    for category, items in results.items():
        table = Table(title=f"Category: {category}", show_header=True, header_style="bold magenta")
        table.add_column("Check", width=28)
        table.add_column("Status", width=10)
        table.add_column("Details")
        table.add_column("Suggested Action / Command")

        for item in items:
            if item.status == "OK":
                status_str = "[bold green]✓ OK[/bold green]"
            elif item.status == "WARN":
                status_str = "[bold yellow]⚠ WARN[/bold yellow]"
            else:
                status_str = "[bold red]✗ FAIL[/bold red]"

            action_text = ""
            if item.suggested_action:
                action_text += f"[italic]{item.suggested_action}[/italic]\n"
            if item.command:
                action_text += f"[bold cyan]`{item.command}`[/bold cyan]"

            table.add_row(item.name, status_str, item.details, action_text.strip())

        console.print(table)
        console.print("")

    if analyze_with_ai:
        report_md = DiagnosticsRunner.format_report_markdown(results)
        console.print("\n[bold cyan]🤖 Sending Diagnostics to AI for Analysis...[/bold cyan]")
        client = get_ai_client()
        query = f"Please analyze these system diagnostics and suggest step-by-step remediation:\n\n{report_md}"
        response = client.query(query)
        if response.is_success:
            console.print(Panel(Markdown(response.content), title="AI Diagnostic Analysis", border_style="green"))
        else:
            console.print(Panel(f"[bold red]{response.error_message}[/bold red]\n\n{response.error_details}", title="AI Error", border_style="red"))

def cmd_explain(command_str: str):
    console.print(f"[bold cyan]🔍 Explaining command:[/bold cyan] [yellow]{command_str}[/yellow]\n")
    analysis = SecurityChecker.analyze(command_str)
    if analysis.risk_level == RiskLevel.BLOCKED:
        console.print(Panel(f"[bold red]{analysis.warning_message}[/bold red]", border_style="red"))
    elif analysis.risk_level == RiskLevel.CONFIRM:
        console.print(Panel(f"[bold yellow]{analysis.warning_message}[/bold yellow]", border_style="yellow"))

    client = get_ai_client()
    prompt = f"Explain this Linux command in detail, including its purpose, arguments, safety implications, and common usage: `{command_str}`"
    with console.status("[bold green]Contacting AI Assistant...[/bold green]"):
        response = client.query(prompt)

    if response.is_success:
        console.print(Panel(Markdown(response.content), title=f"Explanation: {command_str}", border_style="blue"))
    else:
        console.print(Panel(f"[bold red]{response.error_message}[/bold red]\n\n{response.error_details}", title="AI Error", border_style="red"))

def cmd_ask(query: str):
    console.print(f"[bold cyan]User Query:[/bold cyan] {query}\n")
    client = get_ai_client()
    db = get_history_db()
    conv_id = db.create_conversation(title=query[:40])
    db.add_message(conv_id, "user", query)

    with console.status("[bold green]Thinking & Analyzing System State...[/bold green]"):
        response = client.query(query)

    if response.is_success:
        db.add_message(conv_id, "assistant", response.content, response.commands)
        console.print(Panel(Markdown(response.content), title="AI Linux Assistant", border_style="cyan"))
        
        if response.commands:
            console.print("\n[bold yellow]Suggested Commands:[/bold yellow]")
            for idx, c in enumerate(response.commands, 1):
                sec = SecurityChecker.analyze(c)
                if sec.risk_level == RiskLevel.SAFE:
                    tag_colored = "[green][SAFE][/green]"
                elif sec.risk_level == RiskLevel.CONFIRM:
                    tag_colored = "[yellow][CONFIRM][/yellow]"
                else:
                    tag_colored = "[red][BLOCKED][/red]"
                console.print(f"  {idx}. {tag_colored} [bold]{c}[/bold]")
    else:
        console.print(Panel(f"[bold red]{response.error_message}[/bold red]\n\n{response.error_details}", title="AI Error", border_style="red"))

def main():
    setup_logging()
    args = sys.argv[1:]

    if not args:
        import os
        if os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"):
            from zhirterminalassist.__main__ import main as gui_main
            sys.exit(gui_main())
        else:
            print("ZhirTerminalAssist CLI.\nUsage: zhirta <query> | system | diagnose | explain <cmd> | --gui")
            sys.exit(0)

    # Flags
    if "--gui" in args or "-g" in args or args[0] == "gui":
        from zhirterminalassist.__main__ import main as gui_main
        sys.exit(gui_main())

    if args[0] in ("system", "--system", "-s"):
        cmd_system()
        return

    if args[0] in ("diagnose", "--diagnose", "-d"):
        with_ai = "--ai" in args
        cmd_diagnose(analyze_with_ai=with_ai)
        return

    if args[0] in ("explain", "--explain", "-e"):
        if len(args) < 2:
            console.print("[red]Error: Please specify the command to explain. Example: zhirta explain 'chmod 755 file'[/red]")
            sys.exit(1)
        target_cmd = " ".join(args[1:])
        cmd_explain(target_cmd)
        return

    # Natural language query
    query = " ".join(args)
    cmd_ask(query)

if __name__ == "__main__":
    main()

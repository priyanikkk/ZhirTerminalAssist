import os
import subprocess
import sys
from typing import List, Optional, Tuple
from rich.console import Console
from rich.panel import Panel

from zhirterminalassist.history import get_history_manager
from zhirterminalassist.security import CommandAnalysis, RiskLevel, SecurityChecker

console = Console()

class CommandExecutor:
    @staticmethod
    def prompt_and_execute(command: str) -> Optional[int]:
        analysis = SecurityChecker.analyze(command)

        # 1. BLOCKED
        if analysis.risk_level == RiskLevel.BLOCKED:
            console.print(Panel(
                f"[bold red]⛔ BLOCKED COMMAND[/bold red]\n\n"
                f"[bold white]$ {command}[/bold white]\n\n"
                f"[yellow]{analysis.reason}[/yellow]\n\n"
                "[italic red]This command was blocked because it causes catastrophic, unrecoverable damage.[/italic red]",
                border_style="red"
            ))
            return None

        # 2. DANGEROUS
        elif analysis.risk_level == RiskLevel.DANGEROUS:
            console.print(Panel(
                f"[bold red]⚠ DANGEROUS COMMAND[/bold red]\n\n"
                f"[bold yellow]$ {command}[/bold yellow]\n\n"
                f"Impact: [bold white]{analysis.reason}[/bold white]",
                border_style="red"
            ))
        else:
            console.print(f"\n[bold cyan]$[/bold cyan] [bold white]{command}[/bold white]")

        # Prompt user
        try:
            confirm = input("Execute? [y/N]: ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Cancelled.[/yellow]")
            return None

        if confirm not in ("y", "yes"):
            console.print("[dim]Skipped.[/dim]")
            return None

        # Execute
        console.print(f"[dim]Running...[/dim]\n")
        history = get_history_manager()
        shell = os.environ.get("SHELL", "/bin/bash")

        try:
            process = subprocess.Popen(
                command,
                shell=True,
                executable=shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            output_lines = []
            for line in iter(process.stdout.readline, ''):
                sys.stdout.write(line)
                sys.stdout.flush()
                output_lines.append(line)
            
            process.stdout.close()
            ret_code = process.wait()
            output_str = "".join(output_lines)

            status = "SUCCESS" if ret_code == 0 else "FAILED"
            history.add_execution(
                command=command,
                status=status,
                exit_code=ret_code,
                output=output_str[:2000],
                risk_level=analysis.risk_level.value
            )

            if ret_code != 0:
                console.print(f"\n[red]Process exited with code {ret_code}[/red]")
            else:
                console.print(f"\n[green]✓ Command completed successfully[/green]")
            return ret_code

        except KeyboardInterrupt:
            console.print("\n[yellow]Command execution interrupted by user (SIGINT)[/yellow]")
            return -1
        except Exception as e:
            console.print(f"\n[red]Execution failed: {e}[/red]")
            return -1

    @classmethod
    def execute_list(cls, commands: List[str]):
        for cmd in commands:
            code = cls.prompt_and_execute(cmd)
            if code is not None and code != 0:
                try:
                    cont = input("Command failed. Continue to next command? [y/N]: ").strip().lower()
                    if cont not in ("y", "yes"):
                        break
                except (KeyboardInterrupt, EOFError):
                    break

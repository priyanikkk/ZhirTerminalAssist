import os
import subprocess
import sys
from typing import List, Optional, Tuple
from rich.console import Console
from rich.panel import Panel

from zhirterminalassist.config import get_config
from zhirterminalassist.history import get_history_manager
from zhirterminalassist.i18n import t
from zhirterminalassist.security import CommandAnalysis, RiskLevel, SecurityChecker

console = Console()

class CommandExecutor:
    def run_agent_command(self, command: str, cwd: Optional[str] = None) -> Tuple[int, str]:
        analysis = SecurityChecker.analyze(command)
        cfg = get_config()
        auto_safe = cfg.get("auto_execute_safe", False)

        # 1. BLOCKED
        if analysis.risk_level == RiskLevel.BLOCKED:
            console.print(Panel(
                f"[bold red]⛔ {t('blocked_warning')}[/bold red]\n\n"
                f"[bold white]$ {command}[/bold white]\n\n"
                f"[yellow]{analysis.reason}[/yellow]\n\n"
                "[italic red]This command was blocked because it causes catastrophic, unrecoverable damage.[/italic red]",
                border_style="red"
            ))
            return -1, f"Command blocked by security policy: {analysis.reason}"

        # 2. DANGEROUS
        elif analysis.risk_level == RiskLevel.DANGEROUS:
            console.print(Panel(
                f"[bold red]{t('dangerous_warning')}[/bold red]\n\n"
                f"[bold yellow]$ {command}[/bold yellow]\n\n"
                f"Impact: [bold white]{analysis.reason}[/bold white]",
                border_style="red"
            ))
            try:
                confirm = input(f"{t('execute_confirm')} [y/N]: ").strip().lower()
            except (KeyboardInterrupt, EOFError):
                console.print(f"\n[yellow]{t('cancelled')}[/yellow]")
                return -1, "Execution cancelled by user."

            if confirm not in ("y", "yes"):
                console.print(f"[dim]{t('skipped')}[/dim]")
                return -1, "Execution cancelled by user."

        # 3. CONFIRM
        elif analysis.risk_level == RiskLevel.CONFIRM:
            console.print(f"\n[bold yellow]⚠ {analysis.reason}[/bold yellow]")
            try:
                confirm = input(f"{t('execute_confirm')} [y/N]: ").strip().lower()
            except (KeyboardInterrupt, EOFError):
                console.print(f"\n[yellow]{t('cancelled')}[/yellow]")
                return -1, "Execution cancelled by user."

            if confirm not in ("y", "yes"):
                console.print(f"[dim]{t('skipped')}[/dim]")
                return -1, "Execution cancelled by user."

        # 4. SAFE
        else:
            if not auto_safe:
                try:
                    confirm = input(f"{t('execute_confirm')} [Y/n]: ").strip().lower()
                except (KeyboardInterrupt, EOFError):
                    console.print(f"\n[yellow]{t('cancelled')}[/yellow]")
                    return -1, "Execution cancelled by user."

                if confirm in ("n", "no"):
                    console.print(f"[dim]{t('skipped')}[/dim]")
                    return -1, "Execution skipped by user."

        # Execution
        console.print(f"[dim]Running...[/dim]\n")
        history = get_history_manager()
        shell = os.environ.get("SHELL", "/bin/bash")
        exec_cwd = cwd or os.getcwd()

        try:
            process = subprocess.Popen(
                command,
                shell=True,
                executable=shell,
                cwd=exec_cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            output_lines = []
            if process.stdout:
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

            return ret_code, output_str

        except KeyboardInterrupt:
            console.print("\n[yellow]Command execution interrupted by user (SIGINT)[/yellow]")
            return -1, "Command execution interrupted by user (SIGINT)"
        except Exception as e:
            console.print(f"\n[red]Execution failed: {e}[/red]")
            return -1, f"Execution failed: {e}"

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

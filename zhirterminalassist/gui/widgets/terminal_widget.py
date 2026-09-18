import os
import re
from PySide6.QtCore import QProcess, Qt, Signal
from PySide6.QtGui import QFont, QGuiApplication, QTextCursor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QPlainTextEdit, QFrame
)
from zhirterminalassist.gui.dialogs.confirm_dialog import ConfirmCommandDialog
from zhirterminalassist.storage.history_db import get_history_db
from zhirterminalassist.system.security import RiskLevel, SecurityChecker

class TerminalInput(QLineEdit):
    up_pressed = Signal()
    down_pressed = Signal()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Up:
            self.up_pressed.emit()
        elif event.key() == Qt.Key.Key_Down:
            self.down_pressed.emit()
        else:
            super().keyPressEvent(event)

class TerminalWidget(QWidget):
    explain_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cmd_history = []
        self.history_idx = -1
        self.db = get_history_db()

        # Shell process
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.on_stdout)
        self.process.readyReadStandardError.connect(self.on_stderr)
        self.process.finished.connect(self.on_process_finished)

        self.current_cmd = ""

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(12)

        # Header
        h_box = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Embedded Terminal")
        title.setProperty("class", "page-title")
        subtitle = QLabel("Direct Linux command execution with security monitoring and AI assistance")
        subtitle.setProperty("class", "page-subtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        h_box.addLayout(title_box)
        h_box.addStretch()

        # Action Buttons in Header
        self.explain_btn = QPushButton("💡 Explain Last Command")
        self.explain_btn.clicked.connect(self.explain_last_command)
        h_box.addWidget(self.explain_btn)

        copy_btn = QPushButton("Copy Output")
        copy_btn.clicked.connect(self.copy_output)
        h_box.addWidget(copy_btn)

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_console)
        h_box.addWidget(clear_btn)

        self.kill_btn = QPushButton("Stop Process")
        self.kill_btn.setEnabled(False)
        self.kill_btn.setStyleSheet("background-color: #991b1b; color: white;")
        self.kill_btn.clicked.connect(self.kill_process)
        h_box.addWidget(self.kill_btn)

        main_layout.addLayout(h_box)

        # Console Text Box
        self.console = QPlainTextEdit()
        self.console.setObjectName("terminalConsole")
        self.console.setReadOnly(True)
        self.console.setMaximumBlockCount(5000)
        font = QFont("JetBrains Mono, Fira Code, DejaVu Sans Mono, monospace", 10)
        self.console.setFont(font)
        main_layout.addWidget(self.console, 1)

        # Input Row
        input_card = QFrame()
        input_card.setProperty("class", "card")
        input_layout = QHBoxLayout(input_card)
        input_layout.setContentsMargins(8, 6, 8, 6)
        input_layout.setSpacing(8)

        prompt_lbl = QLabel("$")
        prompt_lbl.setStyleSheet("color: #38bdf8; font-weight: bold; font-family: monospace; font-size: 14px;")
        input_layout.addWidget(prompt_lbl)

        self.input_edit = TerminalInput()
        self.input_edit.setPlaceholderText("Enter command (e.g. systemctl --failed, journalctl -p 3 -xb, df -h)...")
        self.input_edit.returnPressed.connect(self.run_input_command)
        self.input_edit.up_pressed.connect(self.nav_history_up)
        self.input_edit.down_pressed.connect(self.nav_history_down)
        input_layout.addWidget(self.input_edit, 1)

        self.exec_btn = QPushButton("Execute")
        self.exec_btn.setProperty("class", "btn-primary")
        self.exec_btn.setFixedWidth(85)
        self.exec_btn.clicked.connect(self.run_input_command)
        input_layout.addWidget(self.exec_btn)

        main_layout.addWidget(input_card)

        # Initial Welcome Banner
        user = os.environ.get("USER", "user")
        import platform
        self.append_text(f"ZhirTerminalAssist Terminal Engine [User: {user} | Host: {platform.node()}]\nType a command or press 'Explain Last Command' to consult the AI assistant.\n\n")

    def run_input_command(self):
        cmd = self.input_edit.text().strip()
        if not cmd:
            return

        # Add to history
        self.cmd_history.append(cmd)
        self.history_idx = len(self.cmd_history)
        self.input_edit.clear()

        self.execute_command(cmd)

    def execute_command(self, cmd: str):
        if self.process.state() == QProcess.ProcessState.Running:
            self.append_text("Error: Another process is currently executing. Click 'Stop Process' first.\n")
            return

        # Security check
        analysis = SecurityChecker.analyze(cmd)
        if analysis.risk_level == RiskLevel.BLOCKED:
            dlg = ConfirmCommandDialog(analysis, parent=self)
            dlg.exec()
            self.append_text(f"\n[SECURITY] ⛔ Execution blocked: {analysis.reason}\n$ ")
            return

        if analysis.risk_level == RiskLevel.CONFIRM:
            dlg = ConfirmCommandDialog(analysis, parent=self)
            dlg.exec()
            if not dlg.confirmed:
                self.append_text(f"\n[SECURITY] ⚠ Cancelled execution of: {cmd}\n$ ")
                return

        self.current_cmd = cmd
        self.current_output = []
        self.append_text(f"\n$ {cmd}\n")

        self.kill_btn.setEnabled(True)
        self.exec_btn.setEnabled(False)

        # Run via bash -c
        shell = os.environ.get("SHELL", "/bin/bash")
        self.process.start(shell, ["-c", cmd])

    def on_stdout(self):
        data = self.process.readAllStandardOutput().data().decode("utf-8", errors="replace")
        self.append_text(data)

    def on_stderr(self):
        data = self.process.readAllStandardError().data().decode("utf-8", errors="replace")
        self.append_text(data)

    def on_process_finished(self, exit_code, exit_status):
        self.kill_btn.setEnabled(False)
        self.exec_btn.setEnabled(True)
        self.append_text(f"\n[Process completed with exit code {exit_code}]\n$ ")

        # Record in DB
        analysis = SecurityChecker.analyze(self.current_cmd)
        self.db.record_execution(
            command=self.current_cmd,
            status="SUCCESS" if exit_code == 0 else "FAILED",
            exit_code=exit_code,
            output="",
            error="",
            risk_level=analysis.risk_level.value
        )

    def kill_process(self):
        if self.process.state() == QProcess.ProcessState.Running:
            self.process.terminate()
            self.append_text("\n[Sent termination signal to process...]\n")

    def append_text(self, text: str):
        # Strip simple ANSI color escape sequences
        clean_text = re.sub(r'\x1b\[[0-9;]*[mK]', '', text)
        self.console.moveCursor(QTextCursor.MoveOperation.End)
        self.console.insertPlainText(clean_text)
        self.console.moveCursor(QTextCursor.MoveOperation.End)

    def copy_output(self):
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(self.console.toPlainText())

    def clear_console(self):
        self.console.clear()
        self.append_text("$ ")

    def nav_history_up(self):
        if not self.cmd_history:
            return
        if self.history_idx > 0:
            self.history_idx -= 1
            self.input_edit.setText(self.cmd_history[self.history_idx])

    def nav_history_down(self):
        if not self.cmd_history:
            return
        if self.history_idx < len(self.cmd_history) - 1:
            self.history_idx += 1
            self.input_edit.setText(self.cmd_history[self.history_idx])
        else:
            self.history_idx = len(self.cmd_history)
            self.input_edit.clear()

    def explain_last_command(self):
        cmd = self.current_cmd or (self.cmd_history[-1] if self.cmd_history else "")
        if cmd:
            self.explain_requested.emit(cmd)
        else:
            self.append_text("\nNo recent command to explain.\n$ ")

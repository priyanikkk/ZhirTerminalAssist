import subprocess
from datetime import datetime
from typing import List, Optional

from PySide6.QtCore import QObject, QThread, Qt, Signal, QTimer
from PySide6.QtGui import QClipboard, QFont, QGuiApplication
from PySide6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QScrollArea, QSizePolicy, QTextBrowser, QVBoxLayout, QWidget
)

from zhirterminalassist.ai.client import AIResponse, get_ai_client
from zhirterminalassist.config import get_config
from zhirterminalassist.gui.dialogs.confirm_dialog import ConfirmCommandDialog
from zhirterminalassist.gui.dialogs.error_dialog import FriendlyErrorDialog
from zhirterminalassist.storage.history_db import get_history_db
from zhirterminalassist.system.security import RiskLevel, SecurityChecker

class AIWorker(QObject):
    finished = Signal(object)

    def __init__(self, query: str, history: List[dict]):
        super().__init__()
        self.query = query
        self.history = history

    def run(self):
        client = get_ai_client()
        resp = client.query(self.query, history=self.history)
        self.finished.emit(resp)

class CommandCard(QFrame):
    def __init__(self, command: str, execute_callback, explain_callback, parent=None):
        super().__init__(parent)
        self.command = command
        self.execute_callback = execute_callback
        self.explain_callback = explain_callback

        self.setStyleSheet("""
            QFrame {
                background-color: #030712;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 4px 8px;
                margin: 4px 0px;
            }
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        # Risk badge
        analysis = SecurityChecker.analyze(command)
        risk_lbl = QLabel(analysis.risk_level.value)
        if analysis.risk_level == RiskLevel.SAFE:
            risk_lbl.setStyleSheet("background-color: #065f46; color: #34d399; font-size: 10px; font-weight: bold; border-radius: 4px; padding: 2px 6px;")
        elif analysis.risk_level == RiskLevel.CONFIRM:
            risk_lbl.setStyleSheet("background-color: #78350f; color: #fbbf24; font-size: 10px; font-weight: bold; border-radius: 4px; padding: 2px 6px;")
        else:
            risk_lbl.setStyleSheet("background-color: #7f1d1d; color: #f87171; font-size: 10px; font-weight: bold; border-radius: 4px; padding: 2px 6px;")
        layout.addWidget(risk_lbl)

        # Command text
        cmd_lbl = QLabel(command)
        cmd_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        cmd_lbl.setStyleSheet("color: #38bdf8; font-family: monospace; font-size: 12px;")
        layout.addWidget(cmd_lbl, 1)

        # Copy button
        self.copy_btn = QPushButton("Copy")
        self.copy_btn.setFixedSize(56, 26)
        self.copy_btn.setStyleSheet("font-size: 11px; padding: 2px;")
        self.copy_btn.clicked.connect(self._copy_command)
        layout.addWidget(self.copy_btn)

        # Explain button
        explain_btn = QPushButton("Explain")
        explain_btn.setFixedSize(62, 26)
        explain_btn.setStyleSheet("font-size: 11px; padding: 2px;")
        explain_btn.clicked.connect(lambda: self.explain_callback(command))
        layout.addWidget(explain_btn)

        # Execute button
        exec_btn = QPushButton("Execute")
        exec_btn.setFixedSize(66, 26)
        exec_btn.setStyleSheet("""
            background-color: #4f46e5;
            color: white;
            font-size: 11px;
            font-weight: bold;
            padding: 2px;
        """)
        exec_btn.clicked.connect(lambda: self.execute_callback(command))
        layout.addWidget(exec_btn)

    def _copy_command(self):
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(self.command)
        self.copy_btn.setText("Copied!")
        self.copy_btn.setStyleSheet("background-color: #065f46; color: white; font-size: 11px;")

class MessageWidget(QFrame):
    def __init__(self, role: str, text: str, commands: List[str] = None, execute_callback=None, explain_callback=None, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        is_user = role == "user"
        if is_user:
            self.setStyleSheet("""
                QFrame {
                    background-color: #1e1b4b;
                    border: 1px solid #3730a3;
                    border-radius: 12px;
                    margin-left: 60px;
                }
            """)
            sender_title = "👤 You"
            title_color = "#a5b4fc"
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: #1e293b;
                    border: 1px solid #334155;
                    border-radius: 12px;
                    margin-right: 60px;
                }
            """)
            sender_title = "⚡ ZhirTerminalAssist AI"
            title_color = "#38bdf8"

        # Sender header
        header = QLabel(sender_title)
        header.setStyleSheet(f"font-weight: bold; color: {title_color}; font-size: 12px;")
        layout.addWidget(header)

        # Message Body
        body = QTextBrowser()
        body.setOpenExternalLinks(True)
        # Convert plain markdown to simple HTML or use setMarkdown
        body.setMarkdown(text)
        body.setStyleSheet("""
            QTextBrowser {
                background: transparent;
                border: none;
                color: #f1f5f9;
                font-size: 13px;
            }
        """)
        # Calculate dynamic height
        body.document().adjustSize()
        body.setFixedHeight(int(body.document().size().height()) + 20)
        layout.addWidget(body)

        # Render suggested commands if any
        if commands and execute_callback and explain_callback:
            cmd_header = QLabel("Suggested Commands:")
            cmd_header.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: bold; margin-top: 4px;")
            layout.addWidget(cmd_header)

            for cmd in commands:
                card = CommandCard(cmd, execute_callback, explain_callback)
                layout.addWidget(card)

class ChatWidget(QWidget):
    open_settings_requested = Signal()
    run_in_terminal_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.conv_history: List[dict] = []
        self.db = get_history_db()
        self.conv_id = self.db.create_conversation("Interactive Session")
        self.thread: Optional[QThread] = None
        self.worker: Optional[AIWorker] = None

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(12)

        # Header
        h_box = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("AI Terminal Assistant")
        title.setProperty("class", "page-title")
        subtitle = QLabel("Natural language Linux problem solving & diagnostic command suggestions")
        subtitle.setProperty("class", "page-subtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        h_box.addLayout(title_box)

        h_box.addStretch()
        clear_btn = QPushButton("Clear Chat")
        clear_btn.clicked.connect(self.clear_chat)
        h_box.addWidget(clear_btn)
        main_layout.addLayout(h_box)

        # Quick Prompt Chips
        chips_layout = QHBoxLayout()
        chips_layout.setSpacing(8)
        chips = [
            "Почему нет звука?",
            "Покажи, что занимает место на диске",
            "Проверь состояние GPU",
            "Установи Discord",
            "Почему Steam не запускается?",
        ]
        for chip in chips:
            btn = QPushButton(chip)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #1e293b;
                    color: #cbd5e1;
                    border: 1px solid #334155;
                    border-radius: 14px;
                    padding: 4px 10px;
                    font-size: 11.5px;
                }
                QPushButton:hover {
                    background-color: #334155;
                    color: #ffffff;
                    border-color: #6366f1;
                }
            """)
            btn.clicked.connect(lambda ch, text=chip: self.send_query(text))
            chips_layout.addWidget(btn)
        chips_layout.addStretch()
        main_layout.addLayout(chips_layout)

        # Scroll area for chat messages
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setStyleSheet("background: transparent;")

        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setContentsMargins(0, 0, 0, 0)
        self.messages_layout.setSpacing(12)
        self.messages_layout.addStretch()

        self.scroll.setWidget(self.messages_container)
        main_layout.addWidget(self.scroll, 1)

        # Execution Feedback Box
        self.exec_feedback = QLabel("")
        self.exec_feedback.setVisible(False)
        self.exec_feedback.setWordWrap(True)
        self.exec_feedback.setStyleSheet("padding: 8px; border-radius: 6px; font-family: monospace; font-size: 11.5px;")
        main_layout.addWidget(self.exec_feedback)

        # Input row
        input_row = QHBoxLayout()
        input_row.setSpacing(8)

        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText("Ask a question, paste an error, or describe what you want to do...")
        self.query_input.returnPressed.connect(self.handle_send)
        input_row.addWidget(self.query_input, 1)

        self.send_btn = QPushButton("Ask AI")
        self.send_btn.setProperty("class", "btn-primary")
        self.send_btn.setFixedWidth(90)
        self.send_btn.clicked.connect(self.handle_send)
        input_row.addWidget(self.send_btn)

        main_layout.addLayout(input_row)

        # Add initial greeting message
        self.add_message("assistant", (
            "Привет! Я **ZhirTerminalAssist** — твой персональный AI-ассистент для Linux.\n\n"
            "Задай мне любой вопрос на естественном языке, например:\n"
            "• *«почему у меня нет звука?»*\n"
            "• *«почему Steam не запускается?»*\n"
            "• *«покажи, что занимает место на диске»*\n"
            "• *«найди ошибку в этом логе»*\n\n"
            "Я исследую систему и предложу команды. Каждая команда снабжена кнопками **Copy** и **Execute** с проверкой безопасности."
        ))

    def handle_send(self):
        text = self.query_input.text().strip()
        if not text:
            return
        self.query_input.clear()
        self.send_query(text)

    def send_query(self, query: str):
        self.add_message("user", query)
        self.db.add_message(self.conv_id, "user", query)
        self.conv_history.append({"role": "user", "content": query})

        # Disable input while waiting
        self.send_btn.setEnabled(False)
        self.send_btn.setText("Thinking...")

        # Run AI client in background thread
        self.thread = QThread()
        self.worker = AIWorker(query, self.conv_history)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_ai_finished)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def on_ai_finished(self, resp: AIResponse):
        self.send_btn.setEnabled(True)
        self.send_btn.setText("Ask AI")

        if resp.is_success:
            self.add_message("assistant", resp.content, resp.commands)
            self.db.add_message(self.conv_id, "assistant", resp.content, resp.commands)
            self.conv_history.append({"role": "assistant", "content": resp.content})
        else:
            # Show friendly error dialog
            dlg = FriendlyErrorDialog(
                title=resp.error_message or "AI Request Failed",
                message=resp.error_details or "Please check your network and provider settings.",
                on_open_settings=self.open_settings_requested.emit,
                parent=self
            )
            dlg.exec()
            self.add_message("assistant", f"⚠️ **Ошибка подключения**: {resp.error_message}\n\n{resp.error_details}")

    def add_message(self, role: str, text: str, commands: List[str] = None):
        msg = MessageWidget(
            role=role,
            text=text,
            commands=commands,
            execute_callback=self.execute_command,
            explain_callback=self.explain_command
        )
        # Insert before the stretch item
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, msg)
        # Scroll to bottom
        QTimer.singleShot(100, lambda: self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum()))

    def execute_command(self, command: str):
        analysis = SecurityChecker.analyze(command)
        config = get_config()
        auto_exec_safe = config.get("auto_execute_safe", False)

        # 1. Blocked commands cannot be executed
        if analysis.risk_level == RiskLevel.BLOCKED:
            dlg = ConfirmCommandDialog(analysis, parent=self)
            dlg.exec()
            return

        # 2. If requires confirmation, or if safe but auto_exec is disabled
        if analysis.risk_level == RiskLevel.CONFIRM or not auto_exec_safe:
            dlg = ConfirmCommandDialog(analysis, parent=self)
            dlg.exec()
            if not dlg.confirmed:
                self.show_feedback(f"Cancelled execution of: {command}", is_error=True)
                return

        # 3. Execute command safely via subprocess
        self.show_feedback(f"Executing: {command}...", is_error=False)
        try:
            res = subprocess.run(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=30
            )
            output = res.stdout
            err = res.stderr
            status = "SUCCESS" if res.returncode == 0 else "FAILED"
            
            # Record in SQLite history DB
            self.db.record_execution(
                command=command,
                status=status,
                exit_code=res.returncode,
                output=output,
                error=err,
                risk_level=analysis.risk_level.value
            )

            # Display execution result
            if res.returncode == 0:
                summary = output.strip() or "(Command completed with exit code 0)"
                self.show_feedback(f"✓ {command}\n{summary[:400]}", is_error=False)
            else:
                summary = err.strip() or output.strip() or f"(Exit code {res.returncode})"
                self.show_feedback(f"✗ Failed (exit {res.returncode}): {command}\n{summary[:400]}", is_error=True)

        except Exception as e:
            self.show_feedback(f"Execution failed: {e}", is_error=True)

    def explain_command(self, command: str):
        self.send_query(f"Explain this Linux command in detail: `{command}`")

    def show_feedback(self, text: str, is_error: bool = False):
        self.exec_feedback.setVisible(True)
        self.exec_feedback.setText(text)
        if is_error:
            self.exec_feedback.setStyleSheet("background-color: #450a0a; color: #f87171; border: 1px solid #991b1b; padding: 8px; border-radius: 6px; font-family: monospace;")
        else:
            self.exec_feedback.setStyleSheet("background-color: #022c22; color: #34d399; border: 1px solid #065f46; padding: 8px; border-radius: 6px; font-family: monospace;")

    def clear_chat(self):
        # Remove all message widgets except stretch
        while self.messages_layout.count() > 1:
            item = self.messages_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self.conv_history.clear()
        self.conv_id = self.db.create_conversation("New Session")
        self.exec_feedback.setVisible(False)

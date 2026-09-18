from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QFrame
)
from zhirterminalassist.system.security import CommandAnalysis, RiskLevel

class ConfirmCommandDialog(QDialog):
    def __init__(self, analysis: CommandAnalysis, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Security Confirmation")
        self.setFixedWidth(540)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.confirmed = False

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header card
        header_card = QFrame()
        header_card.setObjectName("confirmHeader")
        header_layout = QVBoxLayout(header_card)
        header_layout.setContentsMargins(12, 12, 12, 12)

        if analysis.risk_level == RiskLevel.BLOCKED:
            title = QLabel("⛔ COMMAND BLOCKED BY SECURITY POLICY")
            title.setStyleSheet("color: #ef4444; font-size: 14px; font-weight: bold;")
        else:
            title = QLabel("⚠ COMMAND REQUIRES CONFIRMATION")
            title.setStyleSheet("color: #f59e0b; font-size: 14px; font-weight: bold;")
        
        header_layout.addWidget(title)

        reason_lbl = QLabel(analysis.reason)
        reason_lbl.setWordWrap(True)
        reason_lbl.setStyleSheet("color: #cbd5e1; font-size: 12px;")
        header_layout.addWidget(reason_lbl)

        layout.addWidget(header_card)

        # Command display
        cmd_lbl = QLabel("Command to execute:")
        cmd_lbl.setStyleSheet("font-weight: 600; color: #94a3b8;")
        layout.addWidget(cmd_lbl)

        cmd_box = QTextEdit()
        cmd_box.setReadOnly(True)
        cmd_box.setPlainText(analysis.command)
        cmd_box.setFixedHeight(80)
        cmd_box.setStyleSheet("""
            background-color: #030712;
            color: #38bdf8;
            border: 1px solid #334155;
            font-family: monospace;
            font-size: 13px;
            padding: 8px;
        """)
        layout.addWidget(cmd_box)

        # Warning explanation
        if analysis.risk_level == RiskLevel.BLOCKED:
            warn = QLabel(analysis.warning_message)
            warn.setStyleSheet("color: #f87171; font-size: 12px; font-style: italic;")
            warn.setWordWrap(True)
            layout.addWidget(warn)
        else:
            note = QLabel("Executing system modifications, package operations, or elevated commands can alter your system configuration. Proceed only if you understand the effect.")
            note.setWordWrap(True)
            note.setStyleSheet("color: #94a3b8; font-size: 11px;")
            layout.addWidget(note)

        # Buttons
        btn_box = QHBoxLayout()
        btn_box.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedWidth(100)
        cancel_btn.clicked.connect(self.reject)
        btn_box.addWidget(cancel_btn)

        if analysis.risk_level != RiskLevel.BLOCKED:
            exec_btn = QPushButton("Execute")
            exec_btn.setProperty("class", "btn-primary")
            exec_btn.setFixedWidth(110)
            exec_btn.setStyleSheet("""
                background-color: #e11d48;
                color: white;
                font-weight: bold;
                border: 1px solid #f43f5e;
                padding: 6px 14px;
                border-radius: 6px;
            """)
            exec_btn.clicked.connect(self.on_execute)
            btn_box.addWidget(exec_btn)

        layout.addLayout(btn_box)

    def on_execute(self):
        self.confirmed = True
        self.accept()

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit,
    QFileDialog, QFrame
)
from zhirterminalassist.system.logs import LogAnalyzer

class LogsWidget(QWidget):
    analyze_log_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(14)

        # Header
        h_box = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("System Log Analyzer")
        title.setProperty("class", "page-title")
        subtitle = QLabel("Inspect journalctl logs, open custom crash logs, or analyze stack traces with AI")
        subtitle.setProperty("class", "page-subtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        h_box.addLayout(title_box)
        h_box.addStretch()

        self.ai_btn = QPushButton("🤖 Analyze with AI")
        self.ai_btn.setProperty("class", "btn-primary")
        self.ai_btn.clicked.connect(self.on_analyze_ai)
        h_box.addWidget(self.ai_btn)

        main_layout.addLayout(h_box)

        # Quick log source buttons
        btn_bar = QHBoxLayout()
        btn_bar.setSpacing(8)

        sys_log_btn = QPushButton("📋 Fetch System Journal (Errors)")
        sys_log_btn.clicked.connect(self.fetch_system_journal)
        btn_bar.addWidget(sys_log_btn)

        user_log_btn = QPushButton("👤 Fetch User Session Journal")
        user_log_btn.clicked.connect(self.fetch_user_journal)
        btn_bar.addWidget(user_log_btn)

        open_file_btn = QPushButton("📂 Open .log File...")
        open_file_btn.clicked.connect(self.open_file_dialog)
        btn_bar.addWidget(open_file_btn)

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_logs)
        btn_bar.addWidget(clear_btn)

        btn_bar.addStretch()
        main_layout.addLayout(btn_bar)

        # Summary strip
        self.summary_card = QFrame()
        self.summary_card.setProperty("class", "card")
        summary_layout = QHBoxLayout(self.summary_card)
        summary_layout.setContentsMargins(12, 8, 12, 8)
        self.summary_lbl = QLabel("No log loaded. Select a source above or paste raw log text.")
        self.summary_lbl.setStyleSheet("color: #94a3b8; font-size: 12px;")
        summary_layout.addWidget(self.summary_lbl)
        main_layout.addWidget(self.summary_card)

        # Log Text Box
        self.log_text = QTextEdit()
        self.log_text.setPlaceholderText("Paste log output here or load from journalctl / file...")
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #030712;
                color: #e2e8f0;
                font-family: monospace;
                font-size: 12px;
            }
        """)
        self.log_text.textChanged.connect(self.update_summary)
        main_layout.addWidget(self.log_text, 1)

    def fetch_system_journal(self):
        logs = LogAnalyzer.fetch_system_errors(lines=100)
        self.log_text.setPlainText(logs)

    def fetch_user_journal(self):
        logs = LogAnalyzer.fetch_user_errors(lines=80)
        self.log_text.setPlainText(logs)

    def open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Log File", "", "Log Files (*.log *.txt);;All Files (*)"
        )
        if file_path:
            content = LogAnalyzer.read_log_file(file_path, max_lines=400)
            self.log_text.setPlainText(content)

    def update_summary(self):
        text = self.log_text.toPlainText().strip()
        if not text:
            self.summary_lbl.setText("No log loaded. Select a source above or paste raw log text.")
            return

        summary = LogAnalyzer.extract_summary(text)
        total = summary["total_lines"]
        errs = summary["error_count"]
        warns = summary["warning_count"]
        seg = len(summary["segfaults"])
        oom = len(summary["oom_kills"])

        parts = [f"Lines: {total}", f"Errors: {errs}", f"Warnings: {warns}"]
        if seg > 0:
            parts.append(f"<span style='color:#ef4444; font-weight:bold;'>Segfaults: {seg}</span>")
        if oom > 0:
            parts.append(f"<span style='color:#f87171; font-weight:bold;'>OOM Kills: {oom}</span>")

        self.summary_lbl.setText(" • ".join(parts))

    def clear_logs(self):
        self.log_text.clear()

    def on_analyze_ai(self):
        text = self.log_text.toPlainText().strip()
        if not text:
            return

        prompt = (
            "Analyze this Linux log output. Specifically:\n"
            "1. Identify the root cause and group any related errors.\n"
            "2. Explain in plain language what failed and why.\n"
            "3. Propose safe diagnostic and remediation commands.\n\n"
            f"```text\n{text[:6000]}\n```"
        )
        self.analyze_log_requested.emit(prompt)

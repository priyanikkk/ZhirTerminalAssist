from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QFrame, QTreeWidget, QTreeWidgetItem, QHeaderView
)
from zhirterminalassist.system.diagnostics import DiagnosticsRunner, CheckResult

class DiagnosticsWidget(QWidget):
    ask_ai_requested = Signal(str)
    run_cmd_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.last_results = {}

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(16)

        # Header
        h_box = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("System Diagnostics")
        title.setProperty("class", "page-title")
        subtitle = QLabel("Automated health auditing across Audio, GPU, Network, Services, and Storage")
        subtitle.setProperty("class", "page-subtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        h_box.addLayout(title_box)
        h_box.addStretch()

        self.ask_ai_btn = QPushButton("🤖 Ask AI to Analyze")
        self.ask_ai_btn.setProperty("class", "btn-primary")
        self.ask_ai_btn.setEnabled(False)
        self.ask_ai_btn.clicked.connect(self.on_ask_ai)
        h_box.addWidget(self.ask_ai_btn)

        self.run_btn = QPushButton("🔄 Run All Checks")
        self.run_btn.clicked.connect(self.run_diagnostics)
        h_box.addWidget(self.run_btn)

        main_layout.addLayout(h_box)

        # Tree widget for diagnostic categories and check items
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Component / Check", "Status", "Diagnostic Details", "Action / Command"])
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.tree.header().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.tree.header().setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        self.tree.setColumnWidth(0, 260)
        self.tree.setColumnWidth(3, 260)
        self.tree.setAlternatingRowColors(True)
        self.tree.setStyleSheet("""
            QTreeWidget::item {
                padding: 6px 4px;
            }
        """)
        main_layout.addWidget(self.tree, 1)

        # Bottom summary strip
        self.summary_lbl = QLabel("Click 'Run All Checks' to perform comprehensive system diagnostic.")
        self.summary_lbl.setStyleSheet("color: #94a3b8; font-size: 12px;")
        main_layout.addWidget(self.summary_lbl)

        # Auto-run diagnostics on widget creation
        self.run_diagnostics()

    def run_diagnostics(self):
        self.run_btn.setEnabled(False)
        self.run_btn.setText("Scanning...")
        self.tree.clear()

        self.last_results = DiagnosticsRunner.run_all()
        
        total_ok = 0
        total_warn = 0
        total_fail = 0

        for category, items in self.last_results.items():
            cat_item = QTreeWidgetItem(self.tree)
            cat_item.setText(0, f"📂 {category}")
            cat_item.setExpanded(True)
            f = cat_item.font(0); f.setBold(True); cat_item.setFont(0, f); cat_item.setForeground(0, QColor("#38bdf8"))

            cat_ok = True
            for item in items:
                child = QTreeWidgetItem(cat_item)
                child.setText(0, f"  {item.name}")
                
                if item.status == "OK":
                    total_ok += 1
                    child.setText(1, "✓ OK")
                    child.setForeground(1, Qt.GlobalColor.green)
                elif item.status == "WARN":
                    total_warn += 1
                    child.setText(1, "⚠ WARN")
                    child.setForeground(1, Qt.GlobalColor.yellow)
                    cat_ok = False
                else:
                    total_fail += 1
                    child.setText(1, "✗ FAIL")
                    child.setForeground(1, Qt.GlobalColor.red)
                    cat_ok = False

                child.setText(2, item.details)
                action_text = ""
                if item.suggested_action:
                    action_text += item.suggested_action
                if item.command:
                    action_text += f" [`{item.command}`]" if action_text else f"`{item.command}`"
                child.setText(3, action_text)

        self.summary_lbl.setText(
            f"Diagnostics completed: {total_ok} passed, {total_warn} warnings, {total_fail} failures."
        )
        self.ask_ai_btn.setEnabled(True)
        self.run_btn.setEnabled(True)
        self.run_btn.setText("🔄 Run All Checks")

    def on_ask_ai(self):
        if not self.last_results:
            return
        report = DiagnosticsRunner.format_report_markdown(self.last_results)
        prompt = (
            "Please analyze these system diagnostics, explain the root causes of any warnings or failures, "
            f"and propose specific corrective commands:\n\n{report}"
        )
        self.ask_ai_requested.emit(prompt)

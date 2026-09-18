from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QTextEdit, QMessageBox
)
from zhirterminalassist.storage.history_db import get_history_db

class HistoryWidget(QWidget):
    run_in_terminal_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = get_history_db()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(14)

        # Header
        h_box = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Execution & Interaction History")
        title.setProperty("class", "page-title")
        subtitle = QLabel("Auditable local record of AI interactions and executed terminal commands")
        subtitle.setProperty("class", "page-subtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        h_box.addLayout(title_box)
        h_box.addStretch()

        clear_btn = QPushButton("Clear History")
        clear_btn.clicked.connect(self.clear_history)
        h_box.addWidget(clear_btn)

        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.load_history)
        h_box.addWidget(refresh_btn)

        main_layout.addLayout(h_box)

        # Search box
        search_box = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search command history...")
        self.search_input.textChanged.connect(self.load_history)
        search_box.addWidget(self.search_input)
        main_layout.addLayout(search_box)

        # History Table
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Timestamp", "Risk Level", "Status", "Exit Code", "Command"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 160)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        main_layout.addWidget(self.table, 1)

        # Action bar
        action_bar = QHBoxLayout()
        self.copy_btn = QPushButton("Copy Command")
        self.copy_btn.setEnabled(False)
        self.copy_btn.clicked.connect(self.copy_selected)
        action_bar.addWidget(self.copy_btn)

        self.rerun_btn = QPushButton("Re-run in Terminal")
        self.rerun_btn.setProperty("class", "btn-primary")
        self.rerun_btn.setEnabled(False)
        self.rerun_btn.clicked.connect(self.rerun_selected)
        action_bar.addWidget(self.rerun_btn)

        action_bar.addStretch()
        main_layout.addLayout(action_bar)

        # Output Details view
        self.output_view = QTextEdit()
        self.output_view.setReadOnly(True)
        self.output_view.setFixedHeight(120)
        self.output_view.setPlaceholderText("Select a history entry to view stdout/stderr execution log.")
        self.output_view.setStyleSheet("font-family: monospace; font-size: 11.5px;")
        main_layout.addWidget(self.output_view)

        self.load_history()

    def load_history(self):
        query = self.search_input.text().strip()
        entries = self.db.get_executions(limit=150, search=query)
        self.table.setRowCount(len(entries))

        for row, entry in enumerate(entries):
            # Timestamp
            ts_str = entry.get("created_at", "")[:19].replace("T", " ")
            self.table.setItem(row, 0, QTableWidgetItem(ts_str))

            # Risk
            risk = entry.get("risk_level", "SAFE")
            risk_item = QTableWidgetItem(risk)
            if risk == "SAFE":
                risk_item.setForeground(Qt.GlobalColor.green)
            elif risk == "CONFIRM":
                risk_item.setForeground(Qt.GlobalColor.yellow)
            else:
                risk_item.setForeground(Qt.GlobalColor.red)
            self.table.setItem(row, 1, risk_item)

            # Status
            status = entry.get("status", "")
            stat_item = QTableWidgetItem(status)
            if status == "SUCCESS":
                stat_item.setForeground(Qt.GlobalColor.green)
            else:
                stat_item.setForeground(Qt.GlobalColor.red)
            self.table.setItem(row, 2, stat_item)

            # Exit code
            exit_code = entry.get("exit_code")
            self.table.setItem(row, 3, QTableWidgetItem(str(exit_code) if exit_code is not None else "-"))

            # Command
            cmd_item = QTableWidgetItem(entry.get("command", ""))
            cmd_item.setData(Qt.ItemDataRole.UserRole, entry)
            self.table.setItem(row, 4, cmd_item)

    def on_selection_changed(self):
        row = self.table.currentRow()
        if row < 0:
            self.copy_btn.setEnabled(False)
            self.rerun_btn.setEnabled(False)
            self.output_view.clear()
            return

        cmd_item = self.table.item(row, 4)
        if cmd_item:
            entry = cmd_item.data(Qt.ItemDataRole.UserRole)
            self.copy_btn.setEnabled(True)
            self.rerun_btn.setEnabled(True)
            out = entry.get("output", "")
            err = entry.get("error", "")
            details = []
            if out:
                details.append(f"--- STDOUT ---\n{out}")
            if err:
                details.append(f"--- STDERR ---\n{err}")
            self.output_view.setPlainText("\n".join(details) or "(No output captured)")

    def copy_selected(self):
        row = self.table.currentRow()
        if row >= 0:
            cmd = self.table.item(row, 4).text()
            QGuiApplication.clipboard().setText(cmd)
            self.copy_btn.setText("Copied!")
            self.copy_btn.setStyleSheet("background-color: #065f46; color: white;")

    def rerun_selected(self):
        row = self.table.currentRow()
        if row >= 0:
            cmd = self.table.item(row, 4).text()
            self.run_in_terminal_requested.emit(cmd)

    def clear_history(self):
        reply = QMessageBox.question(
            self, "Clear History",
            "Are you sure you want to clear all command and message history?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.db.clear_all()
            self.load_history()
            self.output_view.clear()

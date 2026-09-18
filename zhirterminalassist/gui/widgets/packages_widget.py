from typing import List, Optional
from PySide6.QtCore import QObject, QThread, Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QTextEdit, QFrame, QMessageBox
)
from zhirterminalassist.gui.dialogs.confirm_dialog import ConfirmCommandDialog
from zhirterminalassist.system.packages import PackageManager, PackageItem
from zhirterminalassist.system.security import SecurityChecker

class SearchWorker(QObject):
    finished = Signal(list)

    def __init__(self, pm: PackageManager, query: str):
        super().__init__()
        self.pm = pm
        self.query = query

    def run(self):
        results = self.pm.search(self.query)
        self.finished.emit(results)

class PackagesWidget(QWidget):
    run_in_terminal_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pm = PackageManager()
        self.thread: Optional[QThread] = None
        self.worker: Optional[SearchWorker] = None
        self.current_packages: List[PackageItem] = []

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(14)

        # Header
        h_box = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Package Management")
        title.setProperty("class", "page-title")
        subtitle = QLabel(f"Manage software packages via native package manager: {self.pm.primary_pm.upper()}")
        subtitle.setProperty("class", "page-subtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        h_box.addLayout(title_box)
        h_box.addStretch()

        upgrade_btn = QPushButton(f"🚀 System Upgrade ({self.pm.primary_pm})")
        upgrade_btn.setProperty("class", "btn-primary")
        upgrade_btn.clicked.connect(self.system_upgrade)
        h_box.addWidget(upgrade_btn)
        main_layout.addLayout(h_box)

        # Search Bar
        search_card = QFrame()
        search_card.setProperty("class", "card")
        search_layout = QHBoxLayout(search_card)
        search_layout.setContentsMargins(8, 6, 8, 6)
        search_layout.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(f"Search software repository ({self.pm.primary_pm} / flatpak)...")
        self.search_input.returnPressed.connect(self.start_search)
        search_layout.addWidget(self.search_input, 1)

        self.search_btn = QPushButton("Search")
        self.search_btn.setProperty("class", "btn-primary")
        self.search_btn.setFixedWidth(80)
        self.search_btn.clicked.connect(self.start_search)
        search_layout.addWidget(self.search_btn)

        main_layout.addWidget(search_card)

        # Results Table
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Package Name", "Version", "Repository", "Description"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 180)
        self.table.setColumnWidth(1, 120)
        self.table.setColumnWidth(2, 100)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.itemSelectionChanged.connect(self.on_row_selected)
        main_layout.addWidget(self.table, 1)

        # Action bar & Details
        actions_box = QHBoxLayout()
        actions_box.setSpacing(10)

        self.install_btn = QPushButton("Install Selected")
        self.install_btn.setProperty("class", "btn-success")
        self.install_btn.setEnabled(False)
        self.install_btn.clicked.connect(self.install_selected)
        actions_box.addWidget(self.install_btn)

        self.remove_btn = QPushButton("Remove Selected")
        self.remove_btn.setProperty("class", "btn-danger")
        self.remove_btn.setEnabled(False)
        self.remove_btn.clicked.connect(self.remove_selected)
        actions_box.addWidget(self.remove_btn)

        self.info_btn = QPushButton("Package Info")
        self.info_btn.setEnabled(False)
        self.info_btn.clicked.connect(self.show_package_info)
        actions_box.addWidget(self.info_btn)

        actions_box.addStretch()
        main_layout.addLayout(actions_box)

        # Package Details View
        self.details_view = QTextEdit()
        self.details_view.setReadOnly(True)
        self.details_view.setFixedHeight(120)
        self.details_view.setPlaceholderText("Select a package to view repository metadata and details.")
        main_layout.addWidget(self.details_view)

    def start_search(self):
        query = self.search_input.text().strip()
        if not query:
            return

        self.search_btn.setEnabled(False)
        self.search_btn.setText("Searching...")
        self.table.setRowCount(0)
        self.details_view.clear()

        self.thread = QThread()
        self.worker = SearchWorker(self.pm, query)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_search_finished)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def on_search_finished(self, results: List[PackageItem]):
        self.search_btn.setEnabled(True)
        self.search_btn.setText("Search")
        self.current_packages = results
        self.table.setRowCount(len(results))

        for row, pkg in enumerate(results):
            name_item = QTableWidgetItem(pkg.name)
            name_item.setData(Qt.ItemDataRole.UserRole, pkg)
            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, QTableWidgetItem(pkg.version))
            self.table.setItem(row, 2, QTableWidgetItem(pkg.source))
            self.table.setItem(row, 3, QTableWidgetItem(pkg.description))

        if not results:
            self.details_view.setPlainText(f"No packages found matching '{self.search_input.text()}'.")

    def on_row_selected(self):
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            self.install_btn.setEnabled(False)
            self.remove_btn.setEnabled(False)
            self.info_btn.setEnabled(False)
            return

        row = self.table.currentRow()
        item = self.table.item(row, 0)
        if item:
            pkg: PackageItem = item.data(Qt.ItemDataRole.UserRole)
            self.install_btn.setEnabled(True)
            self.remove_btn.setEnabled(True)
            self.info_btn.setEnabled(True)
            self.details_view.setPlainText(
                f"Package: {pkg.name}\nVersion: {pkg.version}\nRepository: {pkg.source}\nDescription: {pkg.description}"
            )

    def install_selected(self):
        row = self.table.currentRow()
        if row < 0:
            return
        pkg: PackageItem = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        cmd = self.pm.get_install_command(pkg.name)
        
        analysis = SecurityChecker.analyze(cmd)
        dlg = ConfirmCommandDialog(analysis, parent=self)
        dlg.exec()
        if dlg.confirmed:
            self.run_in_terminal_requested.emit(cmd)

    def remove_selected(self):
        row = self.table.currentRow()
        if row < 0:
            return
        pkg: PackageItem = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        cmd = self.pm.get_remove_command(pkg.name)
        
        analysis = SecurityChecker.analyze(cmd)
        dlg = ConfirmCommandDialog(analysis, parent=self)
        dlg.exec()
        if dlg.confirmed:
            self.run_in_terminal_requested.emit(cmd)

    def show_package_info(self):
        row = self.table.currentRow()
        if row < 0:
            return
        pkg: PackageItem = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        info_text = self.pm.get_info(pkg.name)
        self.details_view.setPlainText(info_text)

    def system_upgrade(self):
        cmd = self.pm.get_update_command()
        analysis = SecurityChecker.analyze(cmd)
        dlg = ConfirmCommandDialog(analysis, parent=self)
        dlg.exec()
        if dlg.confirmed:
            self.run_in_terminal_requested.emit(cmd)

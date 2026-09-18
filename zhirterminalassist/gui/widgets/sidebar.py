from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QButtonGroup
)

class SidebarWidget(QFrame):
    page_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(6)

        # Header
        header = QFrame()
        header.setObjectName("sidebarHeader")
        h_layout = QVBoxLayout(header)
        h_layout.setContentsMargins(0, 0, 0, 10)
        h_layout.setSpacing(2)

        title = QLabel("⚡ ZhirTerminalAssist")
        title.setObjectName("sidebarTitle")
        subtitle = QLabel("Linux AI Assistant & Ops")
        subtitle.setObjectName("sidebarSubtitle")

        h_layout.addWidget(title)
        h_layout.addWidget(subtitle)
        layout.addWidget(header)

        # Button group for mutual exclusivity
        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)

        self.nav_items = [
            ("📊  Dashboard", 0),
            ("🤖  AI Assistant", 1),
            ("💻  Terminal", 2),
            ("🔍  Diagnostics", 3),
            ("📦  Packages", 4),
            ("📜  Log Analyzer", 5),
            ("🕒  History", 6),
            ("⚙️  Settings", 7),
        ]

        self.buttons = []
        for text, index in self.nav_items:
            btn = QPushButton(text)
            btn.setProperty("class", "nav-btn")
            btn.setCheckable(True)
            if index == 0:
                btn.setChecked(True)
            btn.clicked.connect(lambda checked, idx=index: self.page_changed.emit(idx))
            self.btn_group.addButton(btn, index)
            layout.addWidget(btn)
            self.buttons.append(btn)

        layout.addStretch()

        # Footer info
        footer_lbl = QLabel("v1.0.0 • Linux Native")
        footer_lbl.setStyleSheet("color: #475569; font-size: 11px; padding-left: 8px;")
        layout.addWidget(footer_lbl)

    def set_current_index(self, index: int):
        btn = self.btn_group.button(index)
        if btn:
            btn.setChecked(True)

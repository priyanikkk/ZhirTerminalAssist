from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
)

class FriendlyErrorDialog(QDialog):
    def __init__(self, title: str, message: str, details: str = "", on_open_settings=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ZhirTerminalAssist - Notice")
        self.setFixedWidth(500)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.on_open_settings = on_open_settings

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        card = QFrame()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 14, 14, 14)
        card_layout.setSpacing(8)

        t_lbl = QLabel(f"⚠ {title}")
        t_lbl.setStyleSheet("color: #f87171; font-size: 15px; font-weight: bold;")
        card_layout.addWidget(t_lbl)

        m_lbl = QLabel(message)
        m_lbl.setWordWrap(True)
        m_lbl.setStyleSheet("color: #f1f5f9; font-size: 13px;")
        card_layout.addWidget(m_lbl)

        if details:
            d_lbl = QLabel(details)
            d_lbl.setWordWrap(True)
            d_lbl.setStyleSheet("color: #94a3b8; font-size: 12px; margin-top: 6px;")
            card_layout.addWidget(d_lbl)

        layout.addWidget(card)

        # Button row
        btn_box = QHBoxLayout()
        btn_box.addStretch()

        if self.on_open_settings:
            settings_btn = QPushButton("Open Settings")
            settings_btn.setProperty("class", "btn-primary")
            settings_btn.clicked.connect(self._handle_settings)
            btn_box.addWidget(settings_btn)

        close_btn = QPushButton("Dismiss")
        close_btn.clicked.connect(self.accept)
        btn_box.addWidget(close_btn)

        layout.addLayout(btn_box)

    def _handle_settings(self):
        self.accept()
        if self.on_open_settings:
            self.on_open_settings()

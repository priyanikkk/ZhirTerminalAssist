"""Modern sleek dark theme styling for PySide6."""

MAIN_STYLE = """
/* Global Application Style */
QWidget {
    background-color: #0f172a;
    color: #f1f5f9;
    font-family: 'Inter', 'Segoe UI', 'Ubuntu', 'Cantarell', sans-serif;
    font-size: 13px;
    selection-background-color: #6366f1;
    selection-color: #ffffff;
}

/* Main Window & Central Widget */
QMainWindow {
    background-color: #090d16;
}

/* Sidebar Navigation */
#sidebar {
    background-color: #0b1120;
    border-right: 1px solid #1e293b;
    min-width: 220px;
    max-width: 240px;
}

#sidebarHeader {
    padding: 16px 12px;
    border-bottom: 1px solid #1e293b;
}

#sidebarTitle {
    font-size: 16px;
    font-weight: bold;
    color: #38bdf8;
    letter-spacing: 0.5px;
}

#sidebarSubtitle {
    font-size: 11px;
    color: #64748b;
}

/* Navigation Buttons */
QPushButton.nav-btn {
    text-align: left;
    padding: 10px 16px;
    border: none;
    border-radius: 8px;
    background-color: transparent;
    color: #94a3b8;
    font-size: 13px;
    font-weight: 500;
    margin: 2px 8px;
}

QPushButton.nav-btn:hover {
    background-color: #1e293b;
    color: #f8fafc;
}

QPushButton.nav-btn:checked {
    background-color: #4f46e5;
    color: #ffffff;
    font-weight: 600;
}

/* Content Area */
#contentArea {
    background-color: #0f172a;
}

/* Cards & Panels */
QFrame.card {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 16px;
}

QFrame.card-highlight {
    background-color: #172033;
    border: 1px solid #6366f1;
    border-radius: 12px;
    padding: 16px;
}

/* Headings */
QLabel.page-title {
    font-size: 20px;
    font-weight: bold;
    color: #f8fafc;
    margin-bottom: 4px;
}

QLabel.page-subtitle {
    font-size: 12px;
    color: #94a3b8;
    margin-bottom: 16px;
}

QLabel.card-title {
    font-size: 14px;
    font-weight: 600;
    color: #e2e8f0;
}

QLabel.stat-value {
    font-size: 24px;
    font-weight: bold;
    color: #38bdf8;
}

/* Standard Buttons */
QPushButton {
    background-color: #334155;
    color: #f8fafc;
    border: 1px solid #475569;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #475569;
    border-color: #64748b;
}

QPushButton:pressed {
    background-color: #1e293b;
}

QPushButton:disabled {
    background-color: #1e293b;
    color: #475569;
    border-color: #334155;
}

/* Primary Action Buttons */
QPushButton.btn-primary {
    background-color: #4f46e5;
    border: 1px solid #6366f1;
    color: #ffffff;
    font-weight: 600;
}

QPushButton.btn-primary:hover {
    background-color: #6366f1;
    border-color: #818cf8;
}

QPushButton.btn-primary:pressed {
    background-color: #4338ca;
}

/* Danger Buttons */
QPushButton.btn-danger {
    background-color: #991b1b;
    border: 1px solid #ef4444;
    color: #ffffff;
}

QPushButton.btn-danger:hover {
    background-color: #dc2626;
}

/* Success Buttons */
QPushButton.btn-success {
    background-color: #065f46;
    border: 1px solid #10b981;
    color: #ffffff;
}

QPushButton.btn-success:hover {
    background-color: #059669;
}

/* Inputs & Text Edits */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #0b1120;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 8px 12px;
    color: #f8fafc;
    font-size: 13px;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #6366f1;
}

/* Terminal Console */
#terminalConsole {
    background-color: #030712;
    color: #e2e8f0;
    font-family: 'JetBrains Mono', 'Fira Code', 'DejaVu Sans Mono', 'Consolas', monospace;
    font-size: 12.5px;
    border: 1px solid #1e293b;
    border-radius: 8px;
    padding: 10px;
}

/* Progress Bars */
QProgressBar {
    background-color: #0b1120;
    border: 1px solid #334155;
    border-radius: 5px;
    text-align: center;
    color: #ffffff;
    font-size: 11px;
    font-weight: bold;
    height: 14px;
}

QProgressBar::chunk {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #38bdf8, stop:1 #6366f1);
    border-radius: 4px;
}

/* Tables & Lists */
QTableWidget, QListWidget, QTreeWidget {
    background-color: #0b1120;
    border: 1px solid #334155;
    border-radius: 8px;
    gridline-color: #1e293b;
    color: #f8fafc;
}

QTableWidget::item:selected, QListWidget::item:selected {
    background-color: #312e81;
    color: #ffffff;
}

QHeaderView::section {
    background-color: #1e293b;
    color: #94a3b8;
    padding: 6px;
    border: 1px solid #334155;
    font-weight: 600;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background-color: #0f172a;
    width: 10px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background-color: #334155;
    min-height: 24px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background-color: #475569;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    border: none;
    background-color: #0f172a;
    height: 10px;
    margin: 0px;
}

QScrollBar::handle:horizontal {
    background-color: #334155;
    min-width: 24px;
    border-radius: 5px;
}

/* Combobox */
QComboBox {
    background-color: #0b1120;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px 12px;
    color: #f8fafc;
}

QComboBox:hover {
    border-color: #6366f1;
}

QComboBox QAbstractItemView {
    background-color: #1e293b;
    border: 1px solid #334155;
    selection-background-color: #4f46e5;
    color: #f8fafc;
}
"""

import sys
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QStackedWidget
)

from zhirterminalassist.config import setup_logging
from zhirterminalassist.gui.theme import MAIN_STYLE
from zhirterminalassist.gui.widgets.chat_widget import ChatWidget
from zhirterminalassist.gui.widgets.dashboard_widget import DashboardWidget
from zhirterminalassist.gui.widgets.diagnostics_widget import DiagnosticsWidget
from zhirterminalassist.gui.widgets.history_widget import HistoryWidget
from zhirterminalassist.gui.widgets.logs_widget import LogsWidget
from zhirterminalassist.gui.widgets.packages_widget import PackagesWidget
from zhirterminalassist.gui.widgets.settings_widget import SettingsWidget
from zhirterminalassist.gui.widgets.sidebar import SidebarWidget
from zhirterminalassist.gui.widgets.terminal_widget import TerminalWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ZhirTerminalAssist")
        self.resize(1200, 780)
        self.setMinimumSize(980, 640)

        # Set Window Icon
        icon_path = Path(__file__).parent.parent.parent / "assets" / "icon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Sidebar Navigation
        self.sidebar = SidebarWidget()
        main_layout.addWidget(self.sidebar)

        # 2. Stacked Content Area
        self.stack = QStackedWidget()
        self.stack.setObjectName("contentArea")

        # Instantiate all page widgets
        self.dashboard_page = DashboardWidget()
        self.chat_page = ChatWidget()
        self.terminal_page = TerminalWidget()
        self.diagnostics_page = DiagnosticsWidget()
        self.packages_page = PackagesWidget()
        self.logs_page = LogsWidget()
        self.history_page = HistoryWidget()
        self.settings_page = SettingsWidget()

        # Add pages in exact order matching sidebar indices (0..7)
        self.stack.addWidget(self.dashboard_page)     # 0
        self.stack.addWidget(self.chat_page)          # 1
        self.stack.addWidget(self.terminal_page)      # 2
        self.stack.addWidget(self.diagnostics_page)   # 3
        self.stack.addWidget(self.packages_page)      # 4
        self.stack.addWidget(self.logs_page)          # 5
        self.stack.addWidget(self.history_page)       # 6
        self.stack.addWidget(self.settings_page)      # 7

        main_layout.addWidget(self.stack, 1)

        # Wire navigation signals
        self.sidebar.page_changed.connect(self.navigate_to_page)
        
        # Inter-page communication
        # 1. Chat -> Settings
        self.chat_page.open_settings_requested.connect(lambda: self.navigate_to_page(7))
        
        # 2. Terminal -> Chat explain
        self.terminal_page.explain_requested.connect(self.handle_explain_in_chat)

        # 3. Diagnostics -> Chat analyze
        self.diagnostics_page.ask_ai_requested.connect(self.handle_diagnostics_in_chat)

        # 4. Packages -> Terminal execute
        self.packages_page.run_in_terminal_requested.connect(self.handle_run_in_terminal)

        # 5. Logs -> Chat analyze
        self.logs_page.analyze_log_requested.connect(self.handle_diagnostics_in_chat)

        # 6. History -> Terminal execute
        self.history_page.run_in_terminal_requested.connect(self.handle_run_in_terminal)

    def navigate_to_page(self, index: int):
        self.stack.setCurrentIndex(index)
        self.sidebar.set_current_index(index)

    def handle_explain_in_chat(self, command: str):
        self.navigate_to_page(1)
        self.chat_page.send_query(f"Explain this Linux command in detail: `{command}`")

    def handle_diagnostics_in_chat(self, prompt: str):
        self.navigate_to_page(1)
        self.chat_page.send_query(prompt)

    def handle_run_in_terminal(self, command: str):
        self.navigate_to_page(2)
        self.terminal_page.execute_command(command)

def create_application():
    setup_logging()
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    
    app.setApplicationName("ZhirTerminalAssist")
    app.setOrganizationName("ZhirTerminalAssist")
    app.setStyleSheet(MAIN_STYLE)
    
    icon_path = Path(__file__).parent.parent.parent / "assets" / "icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    window = MainWindow()
    return app, window

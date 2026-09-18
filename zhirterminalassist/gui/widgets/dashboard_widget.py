from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QFrame,
    QProgressBar, QScrollArea
)
import psutil
from zhirterminalassist.system.info import get_system_info, get_uptime_human

class MetricCard(QFrame):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setProperty("class", "card")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(16, 14, 16, 14)
        self.layout.setSpacing(8)

        self.title_lbl = QLabel(title)
        self.title_lbl.setProperty("class", "card-title")
        self.layout.addWidget(self.title_lbl)

        self.value_lbl = QLabel("...")
        self.value_lbl.setProperty("class", "stat-value")
        self.layout.addWidget(self.value_lbl)

        self.sub_lbl = QLabel("")
        self.sub_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")
        self.layout.addWidget(self.sub_lbl)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.layout.addWidget(self.progress)

    def set_data(self, value: str, subtitle: str = "", percent: float = None):
        self.value_lbl.setText(value)
        if subtitle:
            self.sub_lbl.setText(subtitle)
        if percent is not None:
            self.progress.setVisible(True)
            self.progress.setValue(int(percent))
            if percent > 85:
                self.progress.setStyleSheet("QProgressBar::chunk { background-color: #ef4444; }")
            elif percent > 65:
                self.progress.setStyleSheet("QProgressBar::chunk { background-color: #f59e0b; }")
            else:
                self.progress.setStyleSheet("QProgressBar::chunk { background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #38bdf8, stop:1 #6366f1); }")

class DashboardWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(16)

        # Header
        header_box = QVBoxLayout()
        header_box.setSpacing(4)
        title = QLabel("System Dashboard")
        title.setProperty("class", "page-title")
        subtitle = QLabel("Real-time telemetry, resources, and hardware diagnostics")
        subtitle.setProperty("class", "page-subtitle")
        header_box.addWidget(title)
        header_box.addWidget(subtitle)
        main_layout.addLayout(header_box)

        # Scroll area for cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(16)

        # 1. Grid of Primary Metrics
        grid = QGridLayout()
        grid.setSpacing(16)

        self.cpu_card = MetricCard("CPU Utilization")
        self.ram_card = MetricCard("Memory (RAM)")
        self.swap_card = MetricCard("Swap Memory")
        self.uptime_card = MetricCard("System Uptime")

        grid.addWidget(self.cpu_card, 0, 0)
        grid.addWidget(self.ram_card, 0, 1)
        grid.addWidget(self.swap_card, 1, 0)
        grid.addWidget(self.uptime_card, 1, 1)
        content_layout.addLayout(grid)

        # 2. Host and Hardware Card
        self.hw_card = QFrame()
        self.hw_card.setProperty("class", "card")
        hw_layout = QVBoxLayout(self.hw_card)
        hw_layout.setSpacing(8)
        hw_title = QLabel("💻 Host & Environment")
        hw_title.setProperty("class", "card-title")
        hw_layout.addWidget(hw_title)
        self.hw_details = QLabel("Loading hardware profile...")
        self.hw_details.setStyleSheet("color: #cbd5e1; font-size: 12.5px; line-height: 1.4;")
        hw_layout.addWidget(self.hw_details)
        content_layout.addWidget(self.hw_card)

        # 3. Storage and Disks Card
        self.storage_card = QFrame()
        self.storage_card.setProperty("class", "card")
        self.storage_layout = QVBoxLayout(self.storage_card)
        self.storage_layout.setSpacing(10)
        storage_title = QLabel("💾 Storage Partitions")
        storage_title.setProperty("class", "card-title")
        self.storage_layout.addWidget(storage_title)
        self.disk_entries_layout = QVBoxLayout()
        self.storage_layout.addLayout(self.disk_entries_layout)
        content_layout.addWidget(self.storage_card)

        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

        # Timer for live refresh (every 2 seconds)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_metrics)
        self.timer.start(2000)

        # Initial refresh
        self.refresh_metrics()

    def refresh_metrics(self):
        try:
            info = get_system_info(refresh_cpu=False)
            
            # CPU
            cpu_p = psutil.cpu_percent()
            self.cpu_card.set_data(
                f"{cpu_p:.1f}%",
                f"{info.cpu_model} ({info.cpu_cores_logical} vCPUs)",
                percent=cpu_p
            )

            # RAM
            self.ram_card.set_data(
                f"{info.ram_used_gb} / {info.ram_total_gb} GB",
                f"{info.ram_available_gb} GB available ({info.ram_percent}%)",
                percent=info.ram_percent
            )

            # Swap
            self.swap_card.set_data(
                f"{info.swap_used_gb} / {info.swap_total_gb} GB",
                f"{info.swap_percent}% allocated",
                percent=info.swap_percent
            )

            # Uptime
            self.uptime_card.set_data(
                info.uptime_human,
                f"Host: {info.hostname} | Shell: {info.shell}"
            )

            # Host Details
            gpu_str = ", ".join(info.gpus) or "Generic"
            pms = ", ".join(info.available_package_managers) or "None"
            hw_text = (
                f"<b>OS:</b> {info.os_pretty_name} ({info.os_id}) &nbsp;&bull;&nbsp; "
                f"<b>Kernel:</b> {info.kernel} ({info.arch})<br>"
                f"<b>Desktop:</b> {info.desktop_environment} &nbsp;&bull;&nbsp; "
                f"<b>Display Server:</b> {info.display_server}<br>"
                f"<b>GPU:</b> {gpu_str}<br>"
                f"<b>Package Tools:</b> {pms}"
            )
            self.hw_details.setText(hw_text)

            # Disks
            # Clear old disk entries
            while self.disk_entries_layout.count():
                item = self.disk_entries_layout.takeAt(0)
                w = item.widget()
                if w:
                    w.deleteLater()

            for d in info.disks:
                row = QFrame()
                r_layout = QHBoxLayout(row)
                r_layout.setContentsMargins(0, 4, 0, 4)
                
                info_lbl = QLabel(f"<b>{d['mountpoint']}</b> <span style='color:#94a3b8;'>({d['device']})</span>")
                info_lbl.setFixedWidth(240)
                r_layout.addWidget(info_lbl)

                bar = QProgressBar()
                bar.setValue(int(d['percent']))
                bar.setFixedHeight(12)
                if d['percent'] > 90:
                    bar.setStyleSheet("QProgressBar::chunk { background-color: #ef4444; }")
                elif d['percent'] > 75:
                    bar.setStyleSheet("QProgressBar::chunk { background-color: #f59e0b; }")
                r_layout.addWidget(bar)

                usage_lbl = QLabel(f"{d['used_gb']} / {d['total_gb']} GB ({d['percent']}%)")
                usage_lbl.setFixedWidth(140)
                usage_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                usage_lbl.setStyleSheet("color: #cbd5e1; font-size: 11px;")
                r_layout.addWidget(usage_lbl)

                self.disk_entries_layout.addWidget(row)

        except Exception as e:
            pass

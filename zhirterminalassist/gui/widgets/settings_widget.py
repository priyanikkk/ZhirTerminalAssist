from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QDoubleSpinBox, QSpinBox, QCheckBox, QFrame,
    QMessageBox, QScrollArea
)
from zhirterminalassist.ai.providers import PROVIDERS
from zhirterminalassist.config import get_config
import httpx

class SettingsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = get_config()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(16)

        # Header
        h_box = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Application Settings")
        title.setProperty("class", "page-title")
        subtitle = QLabel("Configure AI backend providers, API credentials, model parameters, and safety policies")
        subtitle.setProperty("class", "page-subtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        h_box.addLayout(title_box)
        main_layout.addLayout(h_box)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        container = QWidget()
        form_layout = QVBoxLayout(container)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(18)

        # 1. AI Provider Card
        ai_card = QFrame()
        ai_card.setProperty("class", "card")
        ai_layout = QGridLayout(ai_card)
        ai_layout.setSpacing(12)
        ai_layout.setContentsMargins(18, 16, 18, 16)

        card_title = QLabel("🤖 AI Provider Configuration")
        card_title.setProperty("class", "card-title")
        ai_layout.addWidget(card_title, 0, 0, 1, 2)

        # Provider selection
        ai_layout.addWidget(QLabel("Provider:"), 1, 0)
        self.provider_combo = QComboBox()
        for key, p in PROVIDERS.items():
            self.provider_combo.addItem(p.display_name, key)
        self.provider_combo.currentIndexChanged.connect(self.on_provider_changed)
        ai_layout.addWidget(self.provider_combo, 1, 1)

        # Base URL
        ai_layout.addWidget(QLabel("API Base URL:"), 2, 0)
        self.base_url_input = QLineEdit()
        ai_layout.addWidget(self.base_url_input, 2, 1)

        # API Key
        ai_layout.addWidget(QLabel("API Key:"), 3, 0)
        key_box = QHBoxLayout()
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("Enter your API key (stored only in ~/.config/zhirterminalassist/)")
        key_box.addWidget(self.api_key_input, 1)

        self.show_key_btn = QPushButton("Show")
        self.show_key_btn.setFixedWidth(60)
        self.show_key_btn.setCheckable(True)
        self.show_key_btn.clicked.connect(self.toggle_show_key)
        key_box.addWidget(self.show_key_btn)
        ai_layout.addLayout(key_box, 3, 1)

        # Model identifier
        ai_layout.addWidget(QLabel("Model:"), 4, 0)
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        ai_layout.addWidget(self.model_combo, 4, 1)

        form_layout.addWidget(ai_card)

        # 2. Hyperparameters Card
        params_card = QFrame()
        params_card.setProperty("class", "card")
        p_layout = QGridLayout(params_card)
        p_layout.setSpacing(12)
        p_layout.setContentsMargins(18, 16, 18, 16)

        p_title = QLabel("⚙️ Generation Parameters")
        p_title.setProperty("class", "card-title")
        p_layout.addWidget(p_title, 0, 0, 1, 2)

        # Temperature
        p_layout.addWidget(QLabel("Temperature:"), 1, 0)
        self.temp_spin = QDoubleSpinBox()
        self.temp_spin.setRange(0.0, 1.5)
        self.temp_spin.setSingleStep(0.1)
        self.temp_spin.setValue(0.7)
        p_layout.addWidget(self.temp_spin, 1, 1)

        # Max tokens
        p_layout.addWidget(QLabel("Max Tokens:"), 2, 0)
        self.tokens_spin = QSpinBox()
        self.tokens_spin.setRange(256, 16384)
        self.tokens_spin.setSingleStep(256)
        self.tokens_spin.setValue(2048)
        p_layout.addWidget(self.tokens_spin, 2, 1)

        form_layout.addWidget(params_card)

        # 3. Security Policy Card
        sec_card = QFrame()
        sec_card.setProperty("class", "card")
        s_layout = QVBoxLayout(sec_card)
        s_layout.setSpacing(10)
        s_layout.setContentsMargins(18, 16, 18, 16)

        s_title = QLabel("🛡️ Execution & Security Policies")
        s_title.setProperty("class", "card-title")
        s_layout.addWidget(s_title)

        self.auto_safe_check = QCheckBox("Automatically execute verified safe, read-only commands without confirmation dialog")
        self.auto_safe_check.setStyleSheet("color: #cbd5e1;")
        s_layout.addWidget(self.auto_safe_check)

        sec_note = QLabel("Dangerous commands (rm, mkfs, dd, package removals, service terminations) will ALWAYS require explicit confirmation regardless of this setting.")
        sec_note.setStyleSheet("color: #94a3b8; font-size: 11.5px; font-style: italic;")
        sec_note.setWordWrap(True)
        s_layout.addWidget(sec_note)

        form_layout.addWidget(sec_card)

        scroll.setWidget(container)
        main_layout.addWidget(scroll, 1)

        # Bottom Button Bar
        btn_bar = QHBoxLayout()
        self.test_btn = QPushButton("🔌 Test Connection")
        self.test_btn.clicked.connect(self.test_connection)
        btn_bar.addWidget(self.test_btn)

        btn_bar.addStretch()

        self.save_btn = QPushButton("Save Settings")
        self.save_btn.setProperty("class", "btn-primary")
        self.save_btn.setFixedWidth(130)
        self.save_btn.clicked.connect(self.save_settings)
        btn_bar.addWidget(self.save_btn)

        main_layout.addLayout(btn_bar)

        self.load_settings()

    def toggle_show_key(self):
        if self.show_key_btn.isChecked():
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.show_key_btn.setText("Hide")
        else:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_key_btn.setText("Show")

    def on_provider_changed(self):
        key = self.provider_combo.currentData()
        p = PROVIDERS.get(key)
        if p:
            self.base_url_input.setText(p.default_base_url)
            self.model_combo.clear()
            if p.recommended_models:
                for m in p.recommended_models:
                    self.model_combo.addItem(m)
            self.model_combo.setEditText(p.default_model)

    def load_settings(self):
        prov = self.config.get("ai_provider", "openrouter")
        idx = self.provider_combo.findData(prov)
        if idx >= 0:
            self.provider_combo.setCurrentIndex(idx)

        self.base_url_input.setText(self.config.get("ai_base_url", "https://openrouter.ai/api/v1"))
        self.api_key_input.setText(self.config.get("ai_api_key", ""))
        self.model_combo.setEditText(self.config.get("ai_model", "google/gemini-2.5-flash"))
        self.temp_spin.setValue(float(self.config.get("ai_temperature", 0.7)))
        self.tokens_spin.setValue(int(self.config.get("ai_max_tokens", 2048)))
        self.auto_safe_check.setChecked(bool(self.config.get("auto_execute_safe", False)))

    def save_settings(self):
        self.config.set("ai_provider", self.provider_combo.currentData())
        self.config.set("ai_base_url", self.base_url_input.text().strip())
        self.config.set("ai_api_key", self.api_key_input.text().strip())
        self.config.set("ai_model", self.model_combo.currentText().strip())
        self.config.set("ai_temperature", self.temp_spin.value())
        self.config.set("ai_max_tokens", self.tokens_spin.value())
        self.config.set("auto_execute_safe", self.auto_safe_check.isChecked())

        QMessageBox.information(self, "Settings Saved", "Application settings have been updated and saved locally.")

    def test_connection(self):
        base_url = self.base_url_input.text().strip().rstrip("/")
        if not base_url.endswith("/v1") and "/v1" not in base_url:
            base_url = f"{base_url}/v1"
        endpoint = f"{base_url}/models"
        api_key = self.api_key_input.text().strip()

        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        self.test_btn.setEnabled(False)
        self.test_btn.setText("Testing...")

        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(endpoint, headers=headers)
                if resp.status_code in (200, 201):
                    QMessageBox.information(
                        self, "Connection Successful",
                        f"Successfully connected to {base_url} (HTTP {resp.status_code})!"
                    )
                elif resp.status_code == 401:
                    QMessageBox.warning(
                        self, "Authentication Failed",
                        "Provider returned HTTP 401 Unauthorized. Please verify your API Key."
                    )
                else:
                    QMessageBox.warning(
                        self, "Provider Response",
                        f"Provider reachable but returned HTTP {resp.status_code}:\n{resp.text[:300]}"
                    )
        except Exception as e:
            QMessageBox.critical(
                self, "Connection Error",
                f"Could not connect to {endpoint}:\n{str(e)}"
            )
        finally:
            self.test_btn.setEnabled(True)
            self.test_btn.setText("🔌 Test Connection")

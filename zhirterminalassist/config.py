import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import load_dotenv

CONFIG_DIR = Path.home() / ".config" / "zhirterminalassist"
DATA_DIR = Path.home() / ".local" / "share" / "zhirterminalassist"
LOG_DIR = DATA_DIR / "logs"

CONFIG_FILE = CONFIG_DIR / "config.json"
HISTORY_FILE = DATA_DIR / "history.db"
LOG_FILE = LOG_DIR / "app.log"

DEFAULT_CONFIG: Dict[str, Any] = {
    "provider": "openrouter",
    "api_key": "",
    "base_url": "https://openrouter.ai/api/v1",
    "model": "google/gemini-2.5-flash",
    "temperature": 0.7,
    "max_tokens": 2048,
    "auto_execute_safe": False,
    "language": "ru",
}

PROVIDER_DEFAULTS = {
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "model": "google/gemini-2.5-flash",
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o-mini",
    },
    "local": {
        "base_url": "http://localhost:11434/v1",
        "model": "qwen2.5:latest",
    },
}

def ensure_directories():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

def setup_logging():
    ensure_directories()
    logger = logging.getLogger("zhirterminalassist")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        file_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    return logger

class AppConfig:
    def __init__(self):
        ensure_directories()
        self._load_env()
        self.data: Dict[str, Any] = dict(DEFAULT_CONFIG)
        self.load()

    def _load_env(self):
        local_env = Path(".env")
        config_env = CONFIG_DIR / ".env"
        if local_env.exists():
            load_dotenv(dotenv_path=local_env)
        elif config_env.exists():
            load_dotenv(dotenv_path=config_env)
        else:
            load_dotenv()

    def load(self):
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    saved_data = json.load(f)
                    self.data.update(saved_data)
            except Exception as e:
                logging.getLogger("zhirterminalassist").error(f"Failed to read config: {e}")

        # Map environment variables if present
        env_provider = os.getenv("AI_PROVIDER")
        env_key = os.getenv("AI_API_KEY")
        env_url = os.getenv("AI_BASE_URL")
        env_model = os.getenv("AI_MODEL")
        env_temp = os.getenv("AI_TEMPERATURE")
        env_max_tok = os.getenv("AI_MAX_TOKENS")

        if env_provider:
            self.data["provider"] = env_provider.lower()
        if env_key:
            self.data["api_key"] = env_key
        if env_url:
            self.data["base_url"] = env_url
        if env_model:
            self.data["model"] = env_model
        if env_temp:
            try:
                self.data["temperature"] = float(env_temp)
            except ValueError:
                pass
        if env_max_tok:
            try:
                self.data["max_tokens"] = int(env_max_tok)
            except ValueError:
                pass

    def save(self):
        ensure_directories()
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def set(self, key: str, value: Any):
        # Normalize key aliases
        norm_key = key.replace("-", "_").lower()
        if norm_key in ("api_url", "url"):
            norm_key = "base_url"
        
        if norm_key in ("temperature",):
            value = float(value)
        elif norm_key in ("max_tokens",):
            value = int(value)
        elif norm_key in ("auto_execute_safe",):
            value = str(value).lower() in ("1", "true", "yes")

        self.data[norm_key] = value
        if norm_key == "language":
            from zhirterminalassist.i18n import set_language
            set_language(str(value))
        self.save()

def mask_api_key(key: str) -> str:
    if not key:
        return "<not set>"
    if len(key) <= 8:
        return "****"
    return f"{key[:4]}...{key[-4:]}"

_config_instance: Optional[AppConfig] = None

def get_config() -> AppConfig:
    global _config_instance
    if _config_instance is None:
        _config_instance = AppConfig()
    return _config_instance

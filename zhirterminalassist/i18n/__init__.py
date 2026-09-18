import json
from pathlib import Path
from typing import Dict, Any

_LOCALES: Dict[str, Dict[str, str]] = {}
_CURRENT_LANG = "ru"

def _load_locales():
    global _LOCALES
    dir_path = Path(__file__).parent
    for lang in ["ru", "en"]:
        file_path = dir_path / f"{lang}.json"
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    _LOCALES[lang] = json.load(f)
            except Exception:
                _LOCALES[lang] = {}

_load_locales()

def set_language(lang: str):
    global _CURRENT_LANG
    lang = lang.lower().strip()
    if lang in ("ru", "russian", "русский", "1"):
        _CURRENT_LANG = "ru"
    elif lang in ("en", "english", "английский", "2"):
        _CURRENT_LANG = "en"
    return _CURRENT_LANG

def get_language() -> str:
    return _CURRENT_LANG

def t(key: str, **kwargs) -> str:
    strings = _LOCALES.get(_CURRENT_LANG, _LOCALES.get("en", {}))
    template = strings.get(key, _LOCALES.get("en", {}).get(key, key))
    if kwargs:
        try:
            return template.format(**kwargs)
        except Exception:
            return template
    return template

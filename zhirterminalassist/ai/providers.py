import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

@dataclass
class ProviderConfig:
    name: str
    display_name: str
    default_base_url: str
    default_model: str
    requires_key: bool = True
    recommended_models: List[str] = None

PROVIDERS: Dict[str, ProviderConfig] = {
    "openrouter": ProviderConfig(
        name="openrouter",
        display_name="OpenRouter (Multi-model)",
        default_base_url="https://openrouter.ai/api/v1",
        default_model="google/gemini-2.5-flash",
        requires_key=True,
        recommended_models=[
            "google/gemini-2.5-flash",
            "anthropic/claude-3.5-sonnet",
            "meta-llama/llama-3.3-70b-instruct",
            "deepseek/deepseek-chat",
            "mistralai/mistral-large",
        ]
    ),
    "openai": ProviderConfig(
        name="openai",
        display_name="OpenAI / Compatible API",
        default_base_url="https://api.openai.com/v1",
        default_model="gpt-4o-mini",
        requires_key=True,
        recommended_models=[
            "gpt-4o-mini",
            "gpt-4o",
            "deepseek-chat",
        ]
    ),
    "local": ProviderConfig(
        name="local",
        display_name="Local Endpoint (Ollama / LM Studio)",
        default_base_url="http://localhost:11434/v1",
        default_model="qwen2.5:latest",
        requires_key=False,
        recommended_models=[
            "qwen2.5:latest",
            "llama3.2:latest",
            "mistral:latest",
            "deepseek-r1:latest",
        ]
    ),
}

def extract_bash_commands(text: str) -> List[str]:
    """Extract bash command lines from markdown code blocks."""
    commands = []
    # Match ```bash ... ``` or ```sh ... ``` or ```shell ... ```
    pattern = r"```(?:bash|sh|shell|zsh)?\s*\n([\s\S]*?)```"
    matches = re.findall(pattern, text, re.IGNORECASE)
    for block in matches:
        for line in block.strip().splitlines():
            line = line.strip()
            # Strip comments or empty lines
            if not line or line.startswith("#"):
                continue
            # Strip leading $ prompt if present
            if line.startswith("$ "):
                line = line[2:].strip()
            if line and line not in commands:
                commands.append(line)
    return commands

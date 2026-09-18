import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import httpx

from zhirterminalassist.config import AppConfig, get_config
from zhirterminalassist.system import format_system_summary_for_ai

logger = logging.getLogger("zhirterminalassist.ai")

SYSTEM_PROMPT_TEMPLATE = """You are ZhirTerminalAssist, an expert Linux Systems Administrator and terminal assistant.
You assist the user inside their native Linux terminal.

CURRENT SYSTEM CONTEXT:
{system_info}

CORE RULES:
1. Grounding: Never make up command outputs or system state.
2. Distribution Specific: Always target the user's specific distribution (e.g. pacman on Arch/CachyOS, apt on Debian/Ubuntu, dnf on Fedora). Respect Wayland vs X11.
3. Diagnose First: If diagnosing an issue, start with safe read-only inspection commands (e.g. pactl info, wpctl status, systemctl --failed, journalctl, ip a).
4. Command Extraction: Enclose all recommended commands in fenced bash code blocks:
   ```bash
   command to run
   ```
5. Safety: Explain any command that alters files or system state. Never suggest destructive commands like rm -rf without explicit warning.
6. Language: Reply in the same language as the user's query (Russian or English).
"""

@dataclass
class AIResponse:
    content: str
    commands: List[str] = field(default_factory=list)
    model: str = ""
    is_success: bool = True
    error_message: Optional[str] = None
    error_details: Optional[str] = None

def extract_bash_commands(text: str) -> List[str]:
    commands = []
    matches = re.findall(r"```(?:bash|sh|shell|zsh)?\s*\n([\s\S]*?)```", text, re.IGNORECASE)
    for block in matches:
        for line in block.strip().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("$ "):
                line = line[2:].strip()
            if line and line not in commands:
                commands.append(line)
    return commands

class AIClient:
    def __init__(self, config: Optional[AppConfig] = None):
        self.config = config or get_config()

    def query(
        self,
        user_message: str,
        history: Optional[List[Dict[str, str]]] = None,
        custom_system_context: Optional[str] = None,
        timeout: float = 45.0
    ) -> AIResponse:
        provider = self.config.get("provider", "openrouter")
        base_url = self.config.get("base_url", "https://openrouter.ai/api/v1")
        api_key = self.config.get("api_key", "").strip()
        model = self.config.get("model", "google/gemini-2.5-flash").strip()
        temperature = float(self.config.get("temperature", 0.7))
        max_tokens = int(self.config.get("max_tokens", 2048))

        # Check API key requirement (local ollama does not require key)
        if provider != "local" and not api_key:
            return AIResponse(
                content="",
                is_success=False,
                error_message="API Key is not configured.",
                error_details=(
                    f"Selected provider '{provider}' requires an API key.\n\n"
                    "Configure it via CLI:\n"
                    "  zhirta config set api-key your_api_key\n"
                    "Or in ~/.config/zhirterminalassist/config.json / .env"
                )
            )

        clean_base_url = base_url.rstrip("/")
        if not clean_base_url.endswith("/v1") and "/v1" not in clean_base_url:
            clean_base_url = f"{clean_base_url}/v1"
        endpoint = f"{clean_base_url}/chat/completions"

        # Formulate system prompt
        sys_info = format_system_summary_for_ai()
        if custom_system_context:
            sys_info += f"\n\nAdditional Diagnostic Input:\n{custom_system_context}"
        sys_prompt = SYSTEM_PROMPT_TEMPLATE.format(system_info=sys_info)

        messages = [{"role": "system", "content": sys_prompt}]
        if history:
            for item in history[-8:]:
                messages.append({"role": item.get("role", "user"), "content": item.get("content", "")})
        messages.append({"role": "user", "content": user_message})

        headers = {"Content-Type": "application/json", "User-Agent": "ZhirTerminalAssist-CLI/1.0"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        if provider == "openrouter":
            headers["HTTP-Referer"] = "https://github.com/priyanikkk/ZhirTerminalAssist"
            headers["X-Title"] = "ZhirTerminalAssist"

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.post(endpoint, json=payload, headers=headers)
                if resp.status_code == 401:
                    return AIResponse(
                        content="",
                        is_success=False,
                        error_message="HTTP 401 Unauthorized",
                        error_details="The provided API key was rejected by the provider. Update with `zhirta config set api-key <key>`."
                    )
                elif resp.status_code >= 400:
                    try:
                        err_text = resp.json().get("error", {}).get("message", resp.text)
                    except Exception:
                        err_text = resp.text
                    return AIResponse(
                        content="",
                        is_success=False,
                        error_message=f"Provider Error (HTTP {resp.status_code})",
                        error_details=err_text
                    )

                data = resp.json()
                choices = data.get("choices", [])
                if not choices:
                    return AIResponse(
                        content="",
                        is_success=False,
                        error_message="Empty response from AI",
                        error_details="No choices were returned in the API payload."
                    )

                reply = choices[0].get("message", {}).get("content", "")
                commands = extract_bash_commands(reply)

                return AIResponse(
                    content=reply,
                    commands=commands,
                    model=model,
                    is_success=True
                )

        except httpx.ConnectError:
            return AIResponse(
                content="",
                is_success=False,
                error_message="Connection to AI provider failed.",
                error_details=f"Could not connect to {endpoint}. Check internet connection or verify local model server (Ollama) is running."
            )
        except httpx.TimeoutException:
            return AIResponse(
                content="",
                is_success=False,
                error_message="Request timed out.",
                error_details=f"Provider did not respond within {timeout}s."
            )
        except Exception as e:
            return AIResponse(
                content="",
                is_success=False,
                error_message="Error contacting AI service.",
                error_details=str(e)
            )

_ai_client_instance: Optional[AIClient] = None

def get_ai_client() -> AIClient:
    global _ai_client_instance
    if _ai_client_instance is None:
        _ai_client_instance = AIClient()
    return _ai_client_instance

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import httpx

from zhirterminalassist.ai.prompt import get_system_prompt
from zhirterminalassist.ai.providers import PROVIDERS, extract_bash_commands
from zhirterminalassist.config import AppConfig, get_config

logger = logging.getLogger("zhirterminalassist.ai")

@dataclass
class AIResponse:
    content: str
    commands: List[str] = field(default_factory=list)
    model: str = ""
    is_success: bool = True
    error_message: Optional[str] = None
    error_details: Optional[str] = None

class AIClient:
    def __init__(self, config: Optional[AppConfig] = None):
        self.config = config or get_config()

    def query(
        self,
        user_message: str,
        history: Optional[List[Dict[str, str]]] = None,
        system_context: Optional[str] = None,
        timeout: float = 45.0
    ) -> AIResponse:
        provider_name = self.config.get("ai_provider", "openrouter")
        base_url = self.config.get("ai_base_url", "https://openrouter.ai/api/v1")
        api_key = self.config.get("ai_api_key", "").strip()
        model = self.config.get("ai_model", "google/gemini-2.5-flash").strip()
        temperature = float(self.config.get("ai_temperature", 0.7))
        max_tokens = int(self.config.get("ai_max_tokens", 2048))

        provider_info = PROVIDERS.get(provider_name, PROVIDERS["openrouter"])

        # Check API key requirement
        if provider_info.requires_key and not api_key:
            return AIResponse(
                content="",
                is_success=False,
                error_message="API Key is missing for the configured AI provider.",
                error_details=(
                    f"Selected provider '{provider_info.display_name}' requires an API key.\n\n"
                    "Please configure your API key in the Settings page or via your .env file:\n"
                    "• Open Settings tab in GUI\n"
                    "• Or set AI_API_KEY=your_key in ~/.config/zhirterminalassist/.env"
                )
            )

        # Normalize base_url
        clean_base_url = base_url.rstrip("/")
        if not clean_base_url.endswith("/v1") and "/v1" not in clean_base_url:
            clean_base_url = f"{clean_base_url}/v1"
        endpoint = f"{clean_base_url}/chat/completions"

        # Build messages
        system_prompt = get_system_prompt(custom_context=system_context)
        messages = [{"role": "system", "content": system_prompt}]

        if history:
            for item in history[-8:]:  # keep last 8 turns for context window efficiency
                messages.append({
                    "role": item.get("role", "user"),
                    "content": item.get("content", "")
                })

        messages.append({"role": "user", "content": user_message})

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "ZhirTerminalAssist/1.0"
        }
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        if provider_name == "openrouter":
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
                        error_message="Authentication failed (HTTP 401 Unauthorized).",
                        error_details="The API key provided was rejected by the provider. Please check the key in Settings."
                    )
                elif resp.status_code == 429:
                    return AIResponse(
                        content="",
                        is_success=False,
                        error_message="Rate limit or quota exceeded (HTTP 429).",
                        error_details="Your account exceeded its rate limit or token credit quota. Try again shortly or change provider/model."
                    )
                elif resp.status_code >= 400:
                    try:
                        err_json = resp.json()
                        detail_msg = err_json.get("error", {}).get("message", resp.text)
                    except Exception:
                        detail_msg = resp.text
                    return AIResponse(
                        content="",
                        is_success=False,
                        error_message=f"AI Provider returned error (HTTP {resp.status_code}).",
                        error_details=str(detail_msg)
                    )

                data = resp.json()
                choices = data.get("choices", [])
                if not choices:
                    return AIResponse(
                        content="",
                        is_success=False,
                        error_message="AI returned an empty response.",
                        error_details="No choices were returned in the API response."
                    )

                reply_text = choices[0].get("message", {}).get("content", "")
                commands = extract_bash_commands(reply_text)

                return AIResponse(
                    content=reply_text,
                    commands=commands,
                    model=model,
                    is_success=True
                )

        except httpx.ConnectError:
            return AIResponse(
                content="",
                is_success=False,
                error_message="Unable to connect to AI provider.",
                error_details=(
                    f"Failed to connect to endpoint: {endpoint}\n\n"
                    "Please check:\n"
                    "• Internet connection\n"
                    "• API URL in Settings\n"
                    "• If using a local model, ensure Ollama/vLLM is running"
                )
            )
        except httpx.TimeoutException:
            return AIResponse(
                content="",
                is_success=False,
                error_message="Request timed out.",
                error_details=f"The AI provider did not respond within {timeout} seconds. The server might be overloaded."
            )
        except Exception as e:
            logger.exception("AI client general failure")
            return AIResponse(
                content="",
                is_success=False,
                error_message="Something went wrong while contacting the AI service.",
                error_details=f"Error details: {str(e)}"
            )

_ai_client_instance = None

def get_ai_client() -> AIClient:
    global _ai_client_instance
    if _ai_client_instance is None:
        _ai_client_instance = AIClient()
    return _ai_client_instance

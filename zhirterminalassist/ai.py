import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import httpx

from zhirterminalassist.config import AppConfig, get_config
from zhirterminalassist.i18n import get_language
from zhirterminalassist.system import format_system_summary_for_ai

logger = logging.getLogger("zhirterminalassist.ai")

AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "Execute a shell command in the project directory. Use this to run scripts, install packages, check system services, run tests, or inspect directories.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The bash command line to run"}
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read file content with line numbers. Use this to inspect code, configuration files, and logs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to file"},
                    "offset": {"type": "integer", "description": "Starting line number (1-based, default: 1)"},
                    "limit": {"type": "integer", "description": "Maximum number of lines to read (default: 200)"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write or overwrite a file with given text content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to file to write"},
                    "content": {"type": "string", "description": "Full file text content"}
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "Replace a specific unique snippet of text in a file with new text. A diff preview will be shown before applying.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to file"},
                    "old_str": {"type": "string", "description": "The exact string or lines to replace"},
                    "new_str": {"type": "string", "description": "The replacement content"}
                },
                "required": ["path", "old_str", "new_str"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_dir",
            "description": "List files and subdirectories in a folder to inspect project structure.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path (default: '.')"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "git_status",
            "description": "Show Git repository status (modified, untracked, and staged files).",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "git_diff",
            "description": "Show unstaged and staged Git diffs.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "git_commit",
            "description": "Stage all changes and commit with the given commit message.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Meaningful git commit message"}
                },
                "required": ["message"]
            }
        }
    }
]

SYSTEM_PROMPT = """You are ZhirTerminalAssist, an autonomous AI Terminal & Coding Agent operating directly in the user's Linux terminal.
You solve real programming, DevOps, debugging, and Linux administration tasks.

OPERATING GUIDELINES:
1. AUTONOMOUS ACTION:
   - When asked to create, fix, investigate, or test something, DO NOT merely give advice. USE YOUR TOOLS directly.
   - For example: if asked "create a hello world python app", call `list_dir` or `write_file`, write the code, and then run it with `bash(command='python3 main.py')` to verify it works!
   - If a command fails or throws an error (e.g. ModuleNotFoundError), analyze the error, fix the file or install dependencies, and re-run.

2. MINIMALIST TERMINAL OUTPUT:
   - Do not print verbose chain-of-thought or conversational filler.
   - Let your tool actions tell the story.
   - When presenting final conclusions, be concise, direct, and technical.

3. SAFETY & RESTRICTIONS:
   - Work within the current project directory.
   - Do not run catastrophic commands (`rm -rf /`).
   - If user confirmation is needed for a command or file change, the system will handle prompting the user.

4. LANGUAGE:
   - Currently active UI language: {lang}.
   - Reply and explain in this language.

HOST SYSTEM ENVIRONMENT:
{sys_summary}
Working Directory: {cwd}
"""

@dataclass
class ToolCall:
    id: str
    name: str
    arguments: Dict[str, Any]

@dataclass
class AgentMessage:
    role: str
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None

class AIProvider:
    def __init__(self, config: Optional[AppConfig] = None):
        self.config = config or get_config()

    def get_system_prompt(self, cwd: str) -> str:
        lang = get_language()
        lang_str = "Russian (Русский)" if lang == "ru" else "English"
        sys_summary = format_system_summary_for_ai()
        return SYSTEM_PROMPT.format(lang=lang_str, sys_summary=sys_summary, cwd=cwd)

    def send_messages(
        self,
        messages: List[Dict[str, Any]],
        cwd: str,
        timeout: float = 60.0
    ) -> Tuple[Optional[str], List[ToolCall], Optional[str]]:
        """
        Sends messages to LLM with tools enabled.
        Returns: (text_content, list_of_tool_calls, error_message)
        """
        provider = self.config.get("provider", "openrouter")
        base_url = self.config.get("base_url", "https://openrouter.ai/api/v1")
        api_key = self.config.get("api_key", "").strip()
        model = self.config.get("model", "google/gemini-2.5-flash").strip()
        temperature = float(self.config.get("temperature", 0.4))
        max_tokens = int(self.config.get("max_tokens", 2048))

        if provider != "local" and not api_key:
            return None, [], "API key is missing. Set with: /config or zhirta config set api-key <KEY>"

        clean_base_url = base_url.rstrip("/")
        if not clean_base_url.endswith("/v1") and "/v1" not in clean_base_url:
            clean_base_url = f"{clean_base_url}/v1"
        endpoint = f"{clean_base_url}/chat/completions"

        # Build full payload
        sys_prompt = self.get_system_prompt(cwd)
        payload_messages = [{"role": "system", "content": sys_prompt}] + messages

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "ZhirTerminalAssist-Agent/1.1"
        }
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        if provider == "openrouter":
            headers["HTTP-Referer"] = "https://github.com/priyanikkk/ZhirTerminalAssist"
            headers["X-Title"] = "ZhirTerminalAssist"

        payload = {
            "model": model,
            "messages": payload_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "tools": AGENT_TOOLS,
            "tool_choice": "auto"
        }

        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.post(endpoint, json=payload, headers=headers)
                if resp.status_code == 401:
                    return None, [], "Authentication failed (HTTP 401). Check your API key via /config."
                elif resp.status_code >= 400:
                    try:
                        err_msg = resp.json().get("error", {}).get("message", resp.text)
                    except Exception:
                        err_msg = resp.text
                    return None, [], f"Provider error (HTTP {resp.status_code}): {err_msg}"

                data = resp.json()
                choices = data.get("choices", [])
                if not choices:
                    return None, [], "AI provider returned empty response choices."

                choice = choices[0]
                message = choice.get("message", {})
                content = message.get("content") or ""
                raw_tool_calls = message.get("tool_calls") or []

                parsed_tool_calls = []
                for tc in raw_tool_calls:
                    fn = tc.get("function", {})
                    fn_name = fn.get("name", "")
                    raw_args = fn.get("arguments", "{}")
                    try:
                        if isinstance(raw_args, str):
                            args = json.loads(raw_args)
                        else:
                            args = raw_args
                    except Exception:
                        args = {}
                    parsed_tool_calls.append(ToolCall(
                        id=tc.get("id", f"call_{len(parsed_tool_calls)}"),
                        name=fn_name,
                        arguments=args
                    ))

                # Fallback: check if text response has XML/markdown code blocks intended as tool calls
                if not parsed_tool_calls and content:
                    parsed_tool_calls = self._parse_text_tool_calls(content)

                return content, parsed_tool_calls, None

        except httpx.ConnectError:
            return None, [], f"Connection error: could not connect to {endpoint}. Check internet or local server."
        except httpx.TimeoutException:
            return None, [], f"Request timed out ({timeout}s)."
        except Exception as e:
            return None, [], f"Unexpected error: {str(e)}"

    def _parse_text_tool_calls(self, text: str) -> List[ToolCall]:
        """Fallback tool parser for models that output tool tags or commands in text."""
        calls = []
        # Check <tool name="bash">cmd</tool>
        xml_matches = re.findall(r'<tool\s+name="([^"]+)"[^>]*>([\s\S]*?)</tool>', text, re.IGNORECASE)
        for name, body in xml_matches:
            try:
                args = json.loads(body.strip())
            except Exception:
                args = {"command": body.strip()} if name == "bash" else {}
            calls.append(ToolCall(id=f"call_{len(calls)}", name=name, arguments=args))

        # Check bash ```bash ... ``` if user asked to run something
        if not calls and ("```bash" in text or "```sh" in text):
            match = re.search(r"```(?:bash|sh)?\s*\n([\s\S]*?)```", text, re.IGNORECASE)
            if match:
                cmd = match.group(1).strip()
                # If command is short, single line and looks executable
                if "\n" not in cmd and not cmd.startswith("#"):
                    calls.append(ToolCall(id="call_0", name="bash", arguments={"command": cmd}))

        return calls

_provider_instance: Optional[AIProvider] = None

def get_ai_provider() -> AIProvider:
    global _provider_instance
    if _provider_instance is None:
        _provider_instance = AIProvider()
    return _provider_instance

def extract_bash_commands(text: str) -> List[str]:
    """Extract bash commands from markdown code blocks."""
    blocks = re.findall(r"```(?:bash|sh)\s*\n([\s\S]*?)```", text, re.IGNORECASE)
    commands = []
    for block in blocks:
        for line in block.strip().split("\n"):
            line = line.strip()
            if line and not line.startswith("#"):
                commands.append(line)
    return commands

@dataclass
class AIResponse:
    content: str = ""
    commands: List[str] = field(default_factory=list)
    is_success: bool = True
    error_message: str = ""
    error_details: str = ""

class AIClient:
    def __init__(self, config: Optional[AppConfig] = None):
        self.config = config or get_config()
        self.provider = AIProvider(self.config)

    def query(self, prompt: str, history: Optional[List[Dict[str, str]]] = None) -> AIResponse:
        api_key = self.config.get("api_key", "")
        provider = self.config.get("provider", "openrouter")
        if provider != "local" and not api_key:
            return AIResponse(
                is_success=False,
                error_message="API Key is not configured.",
                error_details="Set it using: zhirta config set api_key <YOUR_KEY> or export AI_API_KEY"
            )
        messages = list(history or [])
        messages.append({"role": "user", "content": prompt})
        content, tool_calls, err = self.provider.send_messages(messages)
        if err:
            return AIResponse(is_success=False, error_message=err, error_details=err)
        cmds = extract_bash_commands(content or "")
        return AIResponse(content=content or "", commands=cmds, is_success=True)

def get_ai_client() -> AIClient:
    return AIClient()


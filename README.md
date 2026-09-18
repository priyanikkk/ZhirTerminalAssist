# ⚡ ZhirTerminalAssist

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.11+](https://img.shields.io/badge/python-3.11+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Platform: Linux](https://img.shields.io/badge/platform-Linux-FCC624.svg?logo=linux&logoColor=black)](https://kernel.org)
[![Pure CLI/TUI](https://img.shields.io/badge/Interface-Autonomous%20AI%20Terminal%20Agent-00d7ff.svg?logo=gnometerminal&logoColor=white)](https://github.com/priyanikkk/ZhirTerminalAssist)
[![Arch / CachyOS](https://img.shields.io/badge/Optimized-Arch%20%2F%20CachyOS-1793D1.svg?logo=arch-linux&logoColor=white)](https://archlinux.org/)

> **ZhirTerminalAssist** (`zhirta`) is an autonomous **AI Linux Terminal & Coding Agent** operating directly inside your command line — inspired by Claude Code.
> It doesn't just chat: it actively inspects files, edits code with diff previews, executes bash commands with security guardrails, runs tests, manages Git commits, and diagnoses Linux system issues.

```text
╭──────────────────────────────────────────────╮
│ ZhirTerminalAssist                           │
│ AI Terminal Agent                            │
╰──────────────────────────────────────────────╯

  Model: google/gemini-2.5-flash
  Directory: /home/user/myproject
  Language: ru (Русский)

  Type /help for available commands

zhir ❯ почини упавшие тесты и сделай коммит
● Inspecting project...
● Running command...
$ pytest
✗ Error (code 1)
● Reading tests/test_calc.py...
✓ Read tests/test_calc.py
● Editing tests/test_calc.py...
--- a/tests/test_calc.py
+++ b/tests/test_calc.py
@@ -5,3 +5,3 @@
-    assert add(2, 2) == 5
+    assert add(2, 2) == 4
Применить изменения? [Y/n]: y
✓ Updated tests/test_calc.py
● Running command...
$ pytest
✓ Done
● Git Commit Proposal
Message: "fix: correct assertion in test_calc"
Создать коммит с этим сообщением? [Y/n]: y
✓ Коммит успешно создан: [main 7f2e1a4] fix: correct assertion in test_calc
✓ Done
```

---

## 🌟 Key Features

- 🤖 **Autonomous Multi-Step Agent Loop**:
  - Automatically breaks tasks down into investigative and remedial steps: inspects directories, reads files, modifies code, runs commands, analyzes outputs, and iterates until the goal is achieved.
  - Native function calling + fallback tool parser compatible with OpenRouter, OpenAI, and local Ollama models.
- ⚡ **Modern Terminal UX (`prompt_toolkit`)**:
  - Styled `zhir ❯ ` prompt.
  - Persistent input history across sessions with arrow navigation (↑/↓) and auto-suggestions.
  - **Bilingual & Layout-Friendly**: Seamless support for both Russian 🇷🇺 and English 🇬🇧 keyboards without artifacts or broken navigation.
- 📝 **Safe File Editing & Visual Diffs**:
  - View files with line numbers.
  - Interactive unified diff previews before modifications are written.
  - Protection against accidental path traversal outside the project directory (`os.getcwd()`).
- 🛡️ **Comprehensive Security Guardrails**:
  - `BLOCKED`: Hard-prevents catastrophic commands (`rm -rf /`, `rm -rf ~`, fork bombs, raw drive wiping).
  - `DANGEROUS`: Highlights destructive commands (`rm`, `mkfs`, `dd`, `chmod -R`, `pacman -R`, `curl ... | sh`) with red warning panels and requires confirmation.
  - `CONFIRM`: Warns before package installations, service restarts, or system changes.
  - `SAFE`: Fast read-only inspection commands (`ls`, `cat`, `git status`, `uptime`, etc.).
- 🐙 **Integrated Git Workflow**:
  - Inspect repository status (`git_status`), uncommitted unified diffs (`git_diff`), and create structured commits (`git_commit`) with user confirmation.
- 🎛️ **Slash Commands**:
  - `/help`: Interactive commands reference.
  - `/clear`: Clear terminal screen and re-render header.
  - `/status`: Real-time system telemetry and agent session status.
  - `/model [name]`: Switch AI model on the fly.
  - `/config [show | set <key> <val>]`: Inspect and modify configurations.
  - `/history [search]`: Search execution history.
  - `/commands`: List available agent tools and parameters.
  - `/files [path]`: View directory structure and files.
  - `/diff`: Display unified diff of modified files or Git diff.
  - `/reset`: Clear agent conversation context.
  - `/language [ru | en]`: Switch interface language between Russian and English.
  - `/exit`, `/quit`: Exit the agent session.
- 🔍 **Built-in Linux Diagnostics & Explainer**:
  - `zhirta system`: View live CPU load %, RAM/Swap, disk usage, GPU, kernel, and desktop session.
  - `zhirta diagnose`: Hardware, Audio (PipeWire/WirePlumber), Network, GPU, and Systemd diagnostics.
  - `zhirta explain "<cmd>"`: Detailed explanation of Linux commands and flags.
  - `zhirta analyze`: Direct UNIX pipeline analyzer (`journalctl -p 3 -xb | zhirta analyze`).

---

## 📋 Requirements

- **Linux** (CachyOS, Arch Linux, Fedora, Ubuntu, Debian, openSUSE, Alpine, etc.)
- **Python** 3.11+ (Python 3.12 recommended)
- `bash` (or `zsh`, `fish`)
- `uv` (recommended) or standard `python3-venv`

---

## 🚀 Installation

Clone the repository and run `install.sh`:

```bash
git clone https://github.com/priyanikkk/ZhirTerminalAssist.git
cd ZhirTerminalAssist
chmod +x install.sh
./install.sh
```

Ensure `~/.local/bin` is in your `PATH`:
```bash
export PATH="$HOME/.local/bin:$PATH"
```

Now you can launch `zhirta` from anywhere!

---

## ⚙️ Configuration

Configuration is stored in `~/.config/zhirterminalassist/config.json` or can be configured via CLI:

```bash
# View configuration
zhirta config

# Set AI provider (openrouter, openai, local)
zhirta config set provider openrouter

# Set model
zhirta config set model google/gemini-2.5-flash
# or Claude:
zhirta config set model anthropic/claude-3.7-sonnet

# Set API Key
zhirta config set api_key sk-or-v1-xxxxxxxxxxxxxxxx

# Set default interface language (ru / en)
zhirta config set language ru

# Enable auto-execution for safe read-only commands without confirmation
zhirta config set auto_execute_safe true
```

### Environment Variables (`.env`)

You can also specify settings in `.env` or `~/.config/zhirterminalassist/.env`:

```env
AI_PROVIDER=openrouter
AI_API_KEY=your_api_key_here
AI_BASE_URL=https://openrouter.ai/api/v1
AI_MODEL=google/gemini-2.5-flash
AI_TEMPERATURE=0.7
AI_MAX_TOKENS=2048
```

---

## 💻 CLI Usage

### 1. Interactive Agent REPL
```bash
zhirta
```

Inside the session:
```text
zhir ❯ найди ошибку в тестах и исправь её
zhir ❯ покажи свободное место на диске и почисти кэш pacman
zhir ❯ /diff
zhir ❯ /model anthropic/claude-3.7-sonnet
zhir ❯ /language ru
zhir ❯ /status
zhir ❯ /exit
```

### 2. Direct Task Execution (One-Shot)
```bash
zhirta "проверь состояние WirePlumber и перезапусти если он упал"
zhirta "покажи самые прожорливые процессы по RAM"
```

### 3. Linux Diagnostics & System Info
```bash
zhirta system
zhirta diagnose
zhirta diagnose audio --ai
zhirta explain "sudo pacman -Syu"
```

### 4. Unix Pipeline Analysis
```bash
journalctl -p 3 -xb | zhirta analyze
dmesg | zhirta analyze
cat /var/log/pacman.log | zhirta analyze
```

---

## 🛠️ Development & Testing

```bash
git clone https://github.com/priyanikkk/ZhirTerminalAssist.git
cd ZhirTerminalAssist

uv venv --python 3.12
source .venv/bin/activate
uv pip install -e ".[dev]" pytest

# Run the 26 automated unit tests
pytest -v tests/
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file.

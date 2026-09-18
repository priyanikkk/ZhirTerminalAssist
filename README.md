# ⚡ ZhirTerminalAssist

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.11+](https://img.shields.io/badge/python-3.11+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Platform: Linux](https://img.shields.io/badge/platform-Linux-FCC624.svg?logo=linux&logoColor=black)](https://kernel.org)
[![Pure CLI/TUI](https://img.shields.io/badge/Interface-Pure%20Terminal%20CLI%2FTUI-black.svg?logo=gnometerminal&logoColor=white)](https://github.com/priyanikkk/ZhirTerminalAssist)
[![Arch / CachyOS](https://img.shields.io/badge/Optimized-Arch%20%2F%20CachyOS-1793D1.svg?logo=arch-linux&logoColor=white)](https://archlinux.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

> **ZhirTerminalAssist** (`zhirta`) is an intelligent AI-powered Linux terminal assistant and troubleshooting tool running **directly inside your native shell**. Zero GUI, zero browser dependencies, pure terminal efficiency.

```text
╭────────────────────────────────────────────────────────────╮
│ ⚡ ZhirTerminalAssist                                      │
│ AI Linux Terminal Assistant                                │
╰────────────────────────────────────────────────────────────╯
  System
  ├─ OS      CachyOS
  ├─ Kernel  7.1.8-1-cachyos
  ├─ CPU     AMD Ryzen 3 4300G with Radeon Graphics
  ├─ GPU     AMD Radeon Vega Graphics
  ├─ RAM     30.7 GB
  └─ Shell   bash

zhir > почему у меня нет звука?
```

---

## 🌟 Key Features

- 🖥️ **Pure Terminal Native**:
  - Runs in any Linux terminal (Alacritty, Kitty, Foot, Konsole, GNOME Terminal, tty).
  - No GUI windows, no Qt/Tkinter/Electron overhead.
  - Interactive REPL session (`zhir > `) with prompt history, banner, and clean exit handling (`Ctrl+C`, `Ctrl+D`, `exit`).
- 🤖 **Multi-Provider AI Intelligence**:
  - Connects to **OpenRouter**, **OpenAI-compatible APIs**, and **Local Endpoints** (Ollama, LM Studio, vLLM).
  - Senior Linux Sysadmin system prompt: grounds recommendations in actual system context, diagnoses issues before proposing fixes, respects distribution package managers, and never fabricates outputs.
- 🛡️ **Built-in Security Engine**:
  - Strict command risk classification:
    - `SAFE`: Read-only queries (`uname`, `lspci`, `journalctl`, `systemctl status`).
    - `DANGEROUS` / `CONFIRM`: Warns before running modifying commands (`rm`, `dd`, `mkfs`, `fdisk`, `chmod -R`, `chown -R`, `pacman -R`, `curl ... | sh`).
    - `BLOCKED`: Hard-prevents catastrophic commands (`rm -rf /`, `rm -rf ~`, fork bombs, raw drive wiping).
  - Confirmation prompt `Execute? [y/N]` before any suggested command runs.
- 🔍 **Subsystem Diagnostics**:
  - Built-in health checks across **Audio** (PipeWire/WirePlumber/ALSA), **Network**, **GPU** (Mesa/Vulkan), **Storage**, **Systemd** (failed units), **Packages** (pacman lock), **Display** (Wayland/X11), and **Gaming** (Steam, Wine, GameMode).
  - Run specific categories: `zhirta diagnose audio`, `zhirta diagnose gpu`, etc.
  - Pass diagnostic results to AI: `zhirta diagnose --ai`.
- 💡 **Deep Command Explainer**:
  - `zhirta explain "sudo pacman -Syu"` breaks down the binary, individual flags, permissions, and security risks.
- 📜 **Unix Pipeline & Log Analyzer**:
  - Supports UNIX pipes: `dmesg | zhirta analyze`, `journalctl -p 3 -xb | zhirta analyze`, `cat error.log | zhirta analyze`.
  - Instant inspection of journalctl error logs with `zhirta logs`.
- 📊 **Real-Time Telemetry**:
  - `zhirta system` displays live CPU load %, RAM/Swap, storage usage, active shell, desktop environment, and uptime.
- 🕒 **Persistent Local History**:
  - Auditable SQLite database in `~/.local/share/zhirterminalassist/history.db`.
- ⌨️ **Tab Completion**:
  - Built-in completion generator for **Bash**, **Zsh**, and **Fish**.

---

## 📋 Requirements

- **Linux** (CachyOS, Arch Linux, Fedora, Ubuntu, Debian, openSUSE, Alpine, etc.)
- **Python** 3.11+ (Python 3.12 recommended)
- `bash` (or `zsh`, `fish`)
- `uv` (recommended) or `python3-venv`

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

Now you can run `zhirta` from anywhere!

---

## ⚙️ Configuration

Settings are stored in `~/.config/zhirterminalassist/config.json` or `.env`.

### CLI Configuration Commands

```bash
# View current configuration (API key is automatically masked)
zhirta config

# Configure your AI provider (openrouter, openai, local)
zhirta config set provider openrouter

# Set model
zhirta config set model google/gemini-2.5-flash

# Set API Key
zhirta config set api-key sk-or-v1-xxxxxxxxxxxxxxxx

# Set custom API base URL (e.g. for Ollama)
zhirta config set api-url http://localhost:11434/v1
```

### Environment Variables (`.env`)

You can also place a `.env` in your project folder or `~/.config/zhirterminalassist/.env`:

```env
AI_PROVIDER=openrouter
AI_API_KEY=your_api_key_here
AI_BASE_URL=https://openrouter.ai/api/v1
AI_MODEL=google/gemini-2.5-flash
AI_TEMPERATURE=0.7
AI_MAX_TOKENS=2048
```

---

## 🤖 Supported AI Providers

| Provider | Base URL | Default Model | API Key |
| :--- | :--- | :--- | :--- |
| **OpenRouter** | `https://openrouter.ai/api/v1` | `google/gemini-2.5-flash` | Required |
| **OpenAI / Custom** | `https://api.openai.com/v1` | `gpt-4o-mini` | Required |
| **Local (Ollama)** | `http://localhost:11434/v1` | `qwen2.5:latest` | Not needed |

---

## 💻 CLI Usage & Examples

### 1. Interactive REPL Mode
```bash
zhirta
```
```text
[zhir] > почему не работает звук?

  🔍 Анализирую запрос и состояние системы...

  Проблема может быть связана с WirePlumber или отсутствием дефолтного аудио-выхода.
  
  Рекомендую проверить состояние сервисов:
  ```bash
  systemctl --user restart wireplumber
  ```

$ systemctl --user restart wireplumber
Execute? [y/N]: y
Running...
✓ Command completed successfully
```

### 2. Single-shot Queries
```bash
zhirta "почему у меня высокий load average?"
zhirta "покажи самые прожорливые процессы по RAM"
zhirta "как обновить систему на Arch Linux"
```

### 3. System Telemetry
```bash
zhirta system
```
```text
SYSTEM

OS        CachyOS
Kernel    7.1.8-1-cachyos (x86_64)
CPU       AMD Ryzen 3 4300G with Radeon Graphics
GPU       AMD Radeon Graphics
RAM       12.3 / 30.7 GB
Disk      92.4 / 116.3 GB
Shell     bash
DE        KDE
Session   wayland

CPU usage     5.0%
Memory        12.3 / 30.7 GB (40.2%)
Disk          92.4 / 116.3 GB (80.2%)
Uptime        1h 50m
```

### 4. System Diagnostics
```bash
# Run all checks
zhirta diagnose

# Check specific categories
zhirta diagnose audio
zhirta diagnose network
zhirta diagnose gpu
zhirta diagnose systemd

# Ask AI to analyze diagnostics and propose remediation
zhirta diagnose --ai
```

### 5. Command Breakdown & Risk Analysis
```bash
zhirta explain "sudo pacman -Syu"
```
```text
COMMAND
  sudo pacman -Syu

BREAKDOWN
sudo
  Run command with elevated superuser privileges.
pacman
  Arch Linux package manager.
-S
  Synchronize/install packages from remote repositories
-y
  Refresh package databases against servers
-u
  Upgrade all out-of-date packages on the system

RISK
  Medium
```

### 6. Pipeline & Log Stream Analysis
```bash
# Analyze recent systemd errors
zhirta logs

# Pipe command outputs directly to AI
journalctl -p 3 -xb | zhirta analyze
dmesg | zhirta analyze
cat error.log | zhirta analyze
```

### 7. Execution History
```bash
zhirta history
```

---

## 🛡️ Security Architecture

1. **Catastrophic Commands (`BLOCKED`)**:
   - Commands that destroy the operating system or root partitions (`rm -rf /`, `rm -rf ~`, fork bombs, raw block writes to `/dev/sda`) are **hard-blocked**.
2. **Dangerous Commands (`DANGEROUS`)**:
   - `rm`, `mkfs`, `dd`, `chmod -R`, `pacman -R`, `curl ... | sh` are flagged with `⚠ DANGEROUS COMMAND` and require explicit confirmation.
3. **Interactive Confirmation**:
   - No command proposed by AI is executed without the user explicitly pressing `y` or `yes`.

---

## ⌨️ Shell Tab Completion

Generate and enable completions:

```bash
# Bash
zhirta completion bash > ~/.local/share/bash-completion/completions/zhirta

# Zsh
zhirta completion zsh > ~/.zsh/completion/_zhirta

# Fish
zhirta completion fish > ~/.config/fish/completions/zhirta.fish
```

---

## 🛠️ Development & Testing

```bash
git clone https://github.com/priyanikkk/ZhirTerminalAssist.git
cd ZhirTerminalAssist

uv venv --python 3.12
source .venv/bin/activate
uv pip install -e ".[dev]" pytest

# Run automated tests
pytest -v tests/
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file.

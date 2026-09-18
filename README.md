# ⚡ ZhirTerminalAssist

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.11+](https://img.shields.io/badge/python-3.11+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Platform: Linux](https://img.shields.io/badge/platform-Linux-FCC624.svg?logo=linux&logoColor=black)](https://kernel.org)
[![GUI: PySide6](https://img.shields.io/badge/GUI-PySide6%20%2F%20Qt-41CD52.svg?logo=qt&logoColor=white)](https://www.qt.io/)
[![Arch / CachyOS](https://img.shields.io/badge/Optimized-Arch%20%2F%20CachyOS-1793D1.svg?logo=arch-linux&logoColor=white)](https://archlinux.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**ZhirTerminalAssist** is an intelligent AI-powered terminal assistant and desktop command operations center designed specifically for modern Linux distributions (with deep optimization for Arch Linux, CachyOS, Fedora, Ubuntu, and Debian).

It bridges the gap between natural language problem solving and Linux systems administration. Whether diagnosing broken PipeWire audio, deciphering obscure systemd journal errors, inspecting GPU drivers, or managing packages, ZhirTerminalAssist diagnoses root causes, suggests actionable bash commands, and safely executes them with security auditing.

---

## 🌟 Key Features

- 🤖 **Multi-Provider AI Intelligence**:
  - Native integration with **OpenRouter**, **OpenAI**, and **Local Endpoints** (Ollama, LM Studio, vLLM).
  - Grounded System Prompt tailored as a Senior Linux Administrator: never fabricates command output, gathers read-only diagnostics first, respects distribution differences, Wayland/X11 protocols, and user privilege boundaries.
- 🛡️ **Multi-Tier Security Engine**:
  - Automatically classifies commands into `SAFE` (read-only inspection), `CONFIRM` (state changes, service restarts, package operations), and `BLOCKED` (catastrophic actions like `rm -rf /` or raw drive formatting).
  - Explicit confirmation modal for sensitive operations (`[Cancel]` / `[Execute]`).
- 💻 **Embedded Interactive Terminal**:
  - Built-in asynchronous console running a live shell process with ANSI color striping and history navigation.
  - One-click **"💡 Explain Last Command"** to ask AI for deep explanations of commands and exit codes.
- 📊 **Real-Time System Dashboard**:
  - Live monitors for CPU cores & utilization, RAM, Swap, Disks, Network interfaces, GPU hardware, and system uptime updated every 2 seconds.
- 🔍 **Automated System Diagnostics**:
  - Comprehensive category audits: **Audio** (PipeWire/WirePlumber/ALSA), **Network** (gateway, DNS, connectivity), **GPU** (OpenGL, Vulkan loader, drivers), **Storage** (root partition usage, inodes), **Services** (failed systemd units), **Display** (Wayland socket / X11), **Gaming** (Steam, Wine, GameMode), and **Permissions** (user groups).
  - **"Ask AI to Analyze"** button instantly feeds diagnostic results to the assistant for troubleshooting recommendations.
- 📦 **Unified Native Package Manager**:
  - Detects native package managers (`pacman`, `yay`, `paru`, `apt`, `dnf`, `zypper`, `flatpak`).
  - Search packages, inspect repository metadata, install, remove, or trigger full system upgrades with security checks.
- 📜 **System Log Analyzer**:
  - One-click inspection of system errors (`journalctl -p 3 -xb`) and user session journals.
  - Open arbitrary `.log` files or paste stack traces; automatic detection of Segfaults and Out-Of-Memory (OOM) kills.
- 🕒 **Auditable SQLite History**:
  - Complete persistent local history of user queries, AI advice, executed commands, exit codes, and timestamps stored in `~/.config/zhirterminalassist/history.db`.
- ⚡ **Dual Interface**:
  - Rich CLI (`zhirta`) for fast terminal workflows + Modern Dark PySide6 Desktop GUI for deep management.

---

## 🖥️ UI Architecture

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ ⚡ ZhirTerminalAssist                                                 [ - □ ✕ ]│
├───────────────┬─────────────────────────────────────────────────────────────┤
│ 📊 Dashboard  │  🤖 AI Assistant                                           │
│ 🤖 Assistant  │                                                             │
│ 💻 Terminal   │  👤 You: почему у меня нет звука?                           │
│ 🔍 Diagnostics│                                                             │
│ 📦 Packages   │  ⚡ AI: Анализирую аудиоподсистему (PipeWire / WirePlumber)...│
│ 📜 Logs       │                                                             │
│ 🕒 History    │  [SAFE] pactl info                  [Copy] [Explain] [Exec] │
│ ⚙️ Settings    │  [SAFE] systemctl --user status pipewire                    │
│               │                                                             │
│               │  > Input: [ Enter question or terminal query... ]  [Ask AI] │
└───────────────┴─────────────────────────────────────────────────────────────┘
```

---

## 📋 Requirements

- **Operating System**: Linux (Arch, CachyOS, Debian, Ubuntu, Fedora, openSUSE, etc.)
- **Python**: 3.11 or newer (Python 3.12 recommended)
- **Display Server**: Wayland or X11 (desktop environment: KDE, GNOME, Hyprland, Sway, XFCE, etc.)
- **Core Utilities**: `bash`, `psutil`, `systemd` (optional but recommended)

---

## 🚀 Installation

### Automated Installer

Clone the repository and run the included `install.sh` script:

```bash
git clone https://github.com/priyanikkk/ZhirTerminalAssist.git
cd ZhirTerminalAssist
chmod +x install.sh
./install.sh
```

The installer will:
1. Initialize an isolated virtual environment (using `uv` or `python3 -m venv`).
2. Install all required dependencies.
3. Link the `zhirta` launcher to `~/.local/bin/zhirta`.
4. Install the desktop icon and `ZhirTerminalAssist.desktop` file into `~/.local/share/applications/`.

Make sure `~/.local/bin` is in your shell's `PATH`:
```bash
export PATH="$HOME/.local/bin:$PATH"
```

---

## ⚙️ Configuration

ZhirTerminalAssist respects standard XDG directory specifications:
- **Configuration**: `~/.config/zhirterminalassist/config.json`
- **History Database**: `~/.config/zhirterminalassist/history.db`
- **Application Logs**: `~/.local/share/zhirterminalassist/logs/app.log`

### Environment Variables (`.env`)

You can create a `.env` file in `~/.config/zhirterminalassist/.env` or in the project directory:

```env
AI_PROVIDER=openrouter
AI_API_KEY=your_api_key_here
AI_BASE_URL=https://openrouter.ai/api/v1
AI_MODEL=google/gemini-2.5-flash
AI_TEMPERATURE=0.7
AI_MAX_TOKENS=2048
AUTO_EXECUTE_SAFE_COMMANDS=false
```

> [!CAUTION]
> **Never commit your `.env` file or API keys to Git.** `.env` is ignored by `.gitignore`.

---

## 🤖 AI Providers

ZhirTerminalAssist supports any OpenAI-compatible API:

| Provider | Default Base URL | Recommended Models | API Key Needed |
| :--- | :--- | :--- | :--- |
| **OpenRouter** | `https://openrouter.ai/api/v1` | `google/gemini-2.5-flash`, `anthropic/claude-3.5-sonnet`, `deepseek/deepseek-chat` | Yes |
| **OpenAI / Custom** | `https://api.openai.com/v1` | `gpt-4o-mini`, `gpt-4o` | Yes |
| **Local (Ollama)** | `http://localhost:11434/v1` | `qwen2.5:latest`, `llama3.2:latest`, `deepseek-r1:latest` | No |

---

## 🛡️ Security Model

Safety is the foundational principle of ZhirTerminalAssist:

1. **Blocked Destructive Commands (`BLOCKED`)**:
   - Commands that cause irreversible catastrophe (e.g. `rm -rf /`, `rm -rf ~`, fork bombs, writing directly to `/dev/sda`) are **hard-blocked**.
2. **Commands Requiring Confirmation (`CONFIRM`)**:
   - Destructive operations (`rm`, `rmdir`, `dd`, `fdisk`), package modifications (`pacman -R`, `apt remove`), service shutdowns (`systemctl stop/disable`), and recursive permission alterations (`chmod -R`) trigger an explicit confirmation modal before execution.
3. **Safe Read-Only Commands (`SAFE`)**:
   - Inspection commands (`cat`, `uname`, `pactl info`, `lspci`, `systemctl status`, `journalctl`, `df -h`) can be executed directly or with confirmation depending on user preferences.

---

## 💻 CLI Usage (`zhirta`)

The `zhirta` CLI utility enables fast terminal troubleshooting:

```bash
# Ask a natural language troubleshooting question
zhirta "почему не работает звук"

# Run automated system diagnostics
zhirta diagnose

# Run diagnostics and automatically pass results to AI for remediation
zhirta diagnose --ai

# Display hardware and OS summary
zhirta system

# Ask AI to explain a specific shell command
zhirta explain "chmod 755 file"

# Launch the PySide6 Desktop GUI
zhirta --gui
```

---

## 🖥️ GUI Usage

Launch the GUI via application menu or terminal:
```bash
zhirta --gui
```

### Navigating the Interface:
- **Dashboard**: Live telemetry of CPU load, memory utilization, NVMe/SATA storage, and GPU info.
- **AI Assistant**: Conversational troubleshooting interface with quick prompt chips, formatted markdown, and interactive `[Copy]`, `[Explain]`, and `[Execute]` command cards.
- **Terminal**: Direct interactive bash shell with history recall (Up/Down arrows), ANSI output, process kill switch, and "Explain Last Command" shortcut.
- **Diagnostics**: Health check tree across 9 subsystems with status chips (✓ OK, ⚠ WARN, ✗ FAIL) and direct "Ask AI to analyze" dispatch.
- **Packages**: Search packages across native repositories, view package metadata, and perform safe install / remove / upgrade actions.
- **Log Analyzer**: Read journalctl errors, inspect `.log` files, and get automated AI root-cause analysis.
- **History**: Searchable audit log of executed commands, timestamps, and exit codes.
- **Settings**: Switch AI providers, update API keys, tune temperature and token budgets, and test endpoint connectivity.

---

## 🔧 Troubleshooting

### "API Key is missing for the configured AI provider"
- Open **Settings** tab in the GUI and enter your API key, or set `AI_API_KEY` in `~/.config/zhirterminalassist/.env`.
- If using **Ollama**, switch the provider to **Local Endpoint (Ollama)**; no API key is required.

### Wayland & Qt Environment
- ZhirTerminalAssist automatically detects Wayland and X11 sessions. If running in specialized Wayland compositors (e.g. Hyprland, Sway) with fractional scaling, standard Qt environment variables (`QT_QPA_PLATFORM=wayland;xcb`) are respected.

### Application Logs
Check runtime logs at:
```bash
tail -f ~/.local/share/zhirterminalassist/logs/app.log
```

---

## 🛠️ Development & Testing

```bash
# Clone repository
git clone https://github.com/priyanikkk/ZhirTerminalAssist.git
cd ZhirTerminalAssist

# Create virtual environment and install in editable mode
uv venv .venv --python 3.12
source .venv/bin/activate
uv pip install -e ".[dev]" pytest

# Run test suite
pytest -v tests/
```

---

## 🤝 Contributing

Contributions, bug reports, and suggestions are warmly welcome!
1. Fork the repository on GitHub.
2. Create a feature branch: `git checkout -b feature/amazing-feature`.
3. Commit your changes: `git commit -m 'Add amazing feature'`.
4. Push to the branch: `git push origin feature/amazing-feature`.
5. Open a Pull Request.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

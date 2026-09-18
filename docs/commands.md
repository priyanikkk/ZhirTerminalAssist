# ZhirTerminalAssist CLI Reference

ZhirTerminalAssist is a modern terminal assistant designed for direct CLI/TUI use in Linux.

## Command Reference

### Interactive REPL Mode
```bash
zhirta
```
Starts an interactive terminal session (`zhir > `). Type natural language questions, inspect suggestions, and execute commands with confirmation (`[y/N]`). Exit using `exit`, `quit`, `Ctrl+C`, or `Ctrl+D`.

### Single-shot Queries
```bash
zhirta "почему у меня нет звука?"
zhirta "покажи процессы которые используют больше всего RAM"
zhirta "как установить discord"
```

### System Hardware & Environment
```bash
zhirta system
```
Displays a clean summary of OS distribution, kernel, architecture, CPU, GPU, RAM, disk usage, active shell, desktop environment, and session protocol.

### Diagnostics
```bash
# Run all diagnostics
zhirta diagnose

# Run specific subsystem diagnostics
zhirta diagnose audio
zhirta diagnose network
zhirta diagnose gpu
zhirta diagnose storage
zhirta diagnose systemd
zhirta diagnose packages
zhirta diagnose display
zhirta diagnose gaming

# Run diagnostics and automatically analyze with AI
zhirta diagnose --ai
```

### Command Explainer
```bash
zhirta explain "sudo pacman -Syu"
zhirta explain "chmod 755 test.sh"
```
Breaks down the binary, individual flags, permissions mode, and risk level.

### System Error Logs & Pipeline Analysis
```bash
# View recent systemd journal errors
zhirta logs

# View a custom log file
zhirta logs /var/log/pacman.log

# Pipe logs or errors directly to AI
journalctl -p 3 -xb | zhirta analyze
dmesg | zhirta analyze
cat error.log | zhirta analyze
```

### Execution History
```bash
zhirta history
zhirta history pacman
```

### Configuration
```bash
# Show current configuration (API keys masked)
zhirta config

# Set AI provider (openrouter, openai, local)
zhirta config set provider openrouter

# Set model
zhirta config set model google/gemini-2.5-flash

# Set API URL
zhirta config set api-url https://openrouter.ai/api/v1

# Set API Key
zhirta config set api-key sk-or-v1-xxxxxxxx
```

### Tab Completion
```bash
# Bash
zhirta completion bash > ~/.local/share/bash-completion/completions/zhirta

# Zsh
zhirta completion zsh > ~/.zsh/completion/_zhirta

# Fish
zhirta completion fish > ~/.config/fish/completions/zhirta.fish
```

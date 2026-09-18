#!/usr/bin/env bash
set -e

echo "=========================================================="
echo "⚡ Installing ZhirTerminalAssist (Pure Terminal CLI/TUI)..."
echo "=========================================================="

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
INSTALL_PREFIX="${HOME}/.local"
BIN_DIR="${INSTALL_PREFIX}/bin"
PKG_DATA_DIR="${INSTALL_PREFIX}/share/zhirterminalassist"
BASH_COMP_DIR="${INSTALL_PREFIX}/share/bash-completion/completions"

mkdir -p "${BIN_DIR}"
mkdir -p "${PKG_DATA_DIR}"
mkdir -p "${BASH_COMP_DIR}"
mkdir -p "${HOME}/.config/zhirterminalassist"
mkdir -p "${PKG_DATA_DIR}/logs"

# 1. Setup isolated virtual environment
PYTHON_BIN=""
if command -v uv >/dev/null 2>&1; then
    echo "✓ Setting up virtual environment with uv..."
    uv venv "${PKG_DATA_DIR}/venv" --python 3.12 --clear --quiet
    VIRTUAL_ENV="${PKG_DATA_DIR}/venv" uv pip install -e "${SCRIPT_DIR}" --quiet
    PYTHON_BIN="${PKG_DATA_DIR}/venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    echo "✓ Setting up virtual environment with python3 -m venv..."
    python3 -m venv "${PKG_DATA_DIR}/venv"
    "${PKG_DATA_DIR}/venv/bin/pip" install -e "${SCRIPT_DIR}" --quiet
    PYTHON_BIN="${PKG_DATA_DIR}/venv/bin/python"
else
    echo "❌ Error: Neither uv nor python3 were found on this system."
    exit 1
fi

# 2. Create launcher binary in ~/.local/bin/zhirta
cat << LAUNCHER_EOF > "${BIN_DIR}/zhirta"
#!/usr/bin/env bash
exec "${PYTHON_BIN}" -m zhirterminalassist.cli "\$@"
LAUNCHER_EOF
chmod +x "${BIN_DIR}/zhirta"

# 3. Generate bash completion
"${BIN_DIR}/zhirta" completion bash > "${BASH_COMP_DIR}/zhirta" 2>/dev/null || true

echo ""
echo "=========================================================="
echo "✅ ZhirTerminalAssist has been installed successfully!"
echo "=========================================================="
echo "• CLI Executable:   ${BIN_DIR}/zhirta"
echo "• Config File:      ~/.config/zhirterminalassist/config.json"
echo "• History Database: ~/.local/share/zhirterminalassist/history.db"
echo ""
echo "Quick Start:"
echo "  zhirta                            # Start interactive REPL"
echo "  zhirta \"почему нет звука\"         # Ask a question"
echo "  zhirta system                     # View system hardware & stats"
echo "  zhirta diagnose                   # Run diagnostics"
echo "  zhirta explain \"sudo pacman -Syu\" # Explain command"
echo "  zhirta config set api-key <KEY>   # Set your AI API key"

#!/usr/bin/env bash
set -e

echo "=========================================================="
echo "⚡ Installing ZhirTerminalAssist..."
echo "=========================================================="

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
INSTALL_PREFIX="${HOME}/.local"
BIN_DIR="${INSTALL_PREFIX}/bin"
APP_DIR="${INSTALL_PREFIX}/share/applications"
ICON_DIR="${INSTALL_PREFIX}/share/icons/hicolor"
PKG_DATA_DIR="${INSTALL_PREFIX}/share/zhirterminalassist"

mkdir -p "${BIN_DIR}"
mkdir -p "${APP_DIR}"
mkdir -p "${ICON_DIR}/256x256/apps"
mkdir -p "${ICON_DIR}/scalable/apps"
mkdir -p "${PKG_DATA_DIR}"
mkdir -p "${HOME}/.config/zhirterminalassist"
mkdir -p "${PKG_DATA_DIR}/logs"

# 1. Choose Python runtime
PYTHON_BIN=""
if command -v uv >/dev/null 2>&1; then
    echo "✓ Found 'uv' package manager. Setting up optimized Python 3.12 environment..."
    uv venv "${PKG_DATA_DIR}/venv" --python 3.12 --quiet
    VIRTUAL_ENV="${PKG_DATA_DIR}/venv" uv pip install -e "${SCRIPT_DIR}" --quiet
    PYTHON_BIN="${PKG_DATA_DIR}/venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    echo "✓ Setting up virtual environment via python3 -m venv..."
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

# Create symlink for zhirterminalassist
ln -sf "${BIN_DIR}/zhirta" "${BIN_DIR}/zhirterminalassist"

# 3. Install icons
if [ -f "${SCRIPT_DIR}/assets/icon.png" ]; then
    cp "${SCRIPT_DIR}/assets/icon.png" "${ICON_DIR}/256x256/apps/zhirterminalassist.png"
fi
if [ -f "${SCRIPT_DIR}/assets/icon.svg" ]; then
    cp "${SCRIPT_DIR}/assets/icon.svg" "${ICON_DIR}/scalable/apps/zhirterminalassist.svg"
fi

# 4. Install Desktop Entry
sed -e "s|Exec=zhirta --gui|Exec=${BIN_DIR}/zhirta --gui|g" \
    "${SCRIPT_DIR}/ZhirTerminalAssist.desktop" > "${APP_DIR}/ZhirTerminalAssist.desktop"
chmod +x "${APP_DIR}/ZhirTerminalAssist.desktop"

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "${APP_DIR}" >/dev/null 2>&1 || true
fi

echo ""
echo "=========================================================="
echo "✅ ZhirTerminalAssist has been installed successfully!"
echo "=========================================================="
echo "• CLI Command:      ${BIN_DIR}/zhirta"
echo "• Desktop Menu:     ZhirTerminalAssist"
echo "• Config Directory: ~/.config/zhirterminalassist/"
echo "• Log Directory:    ~/.local/share/zhirterminalassist/logs/"
echo ""
echo "Make sure ${BIN_DIR} is in your PATH."
echo "Run: zhirta system"
echo "Run: zhirta diagnose"
echo "Run: zhirta --gui"

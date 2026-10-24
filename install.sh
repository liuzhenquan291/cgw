#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo "=========================================="
echo "  cgw - Claude Gateway Installer"
echo "=========================================="
echo ""

# ── 1. Detect Python ─────────────────────────────
PYTHON=""
for p in python3.12 python3.11 python3.10 python3.9 python3.8 python3; do
    if command -v "$p" &>/dev/null; then PYTHON="$p"; break; fi
done
if [ -z "$PYTHON" ]; then echo "Error: Python 3.7+ not found"; exit 1; fi
echo "Python: $PYTHON ($("$PYTHON" --version 2>&1))"

# ── 2. Create virtual environment ─────────────────
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    "$PYTHON" -m venv .venv
fi
source .venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet fastapi uvicorn httpx
echo "Dependencies installed"

# ── 3. Create config directory ────────────────────
CONFIG_DIR="$HOME/.claude-gateway"
mkdir -p "$CONFIG_DIR"

# ── 4. Interactive first profile setup ────────────
PROFILES_FILE="$CONFIG_DIR/profiles.json"
if [ ! -f "$PROFILES_FILE" ]; then
    echo ""
    echo "Create your first profile (press Enter to skip, configure later via Web UI):"
    printf "Profile name [default]: "
    read -r P_NAME
    P_NAME="${P_NAME:-default}"
    printf "Upstream URL [https://api.your-provider.com/anthropic]: "
    read -r P_URL
    P_URL="${P_URL:-https://api.your-provider.com/anthropic}"
    printf "API Key: "
    read -r P_KEY

    if [ -n "$P_KEY" ]; then
        cat > "$PROFILES_FILE" << EOF
{
  "version": 2,
  "active": "$P_NAME",
  "profiles": {
    "$P_NAME": {
      "upstream_url": "$P_URL",
      "api_key": "$P_KEY",
      "auth_scheme": "api-key",
      "models": [
        {"id": "claude-opus-4-6", "upstream": "your-model-pro", "display_name": "Your Model Pro"},
        {"id": "claude-sonnet-4-5", "upstream": "your-model-flash", "display_name": "Your Model Flash"}
      ]
    }
  }
}
EOF
        echo "MIMO_API_KEY=$P_KEY" > .env
        echo "OK: Profile '$P_NAME' created successfully"
    else
        echo '{}' > "$PROFILES_FILE"
        echo "MIMO_API_KEY=" > .env
        echo "Skipped. Run 'cgw add' or visit the Web UI to configure."
    fi
else
    echo "Existing config found: $PROFILES_FILE"
fi

# ── 5. Install cgw command ────────────────────────
BIN_DIR="$HOME/.local/bin"
mkdir -p "$BIN_DIR"
cat > "$BIN_DIR/cgw" << EOF
#!/usr/bin/env bash
exec "$DIR/.venv/bin/python" "$DIR/cli.py" "\$@"
EOF
chmod +x "$BIN_DIR/cgw"
echo "OK: cgw installed to $BIN_DIR/cgw"

# PATH configuration
SHELL_RC="$HOME/.zshrc"
PATH_LINE='export PATH="$HOME/.local/bin:$PATH"'
if [ -f "$SHELL_RC" ]; then
    if ! grep -q "$PATH_LINE" "$SHELL_RC" 2>/dev/null; then
        echo "" >> "$SHELL_RC"
        echo "# Claude Gateway" >> "$SHELL_RC"
        echo "$PATH_LINE" >> "$SHELL_RC"
        echo "OK: PATH added to ~/.zshrc (run 'source ~/.zshrc' to apply)"
    fi
fi

# ── 6. Start Gateway ─────────────────────────────
PID_FILE="$DIR/gateway.pid"
if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    echo ""
    echo "Gateway already running (PID: $(cat "$PID_FILE"))"
else
    source .env 2>/dev/null || true
    nohup python -m uvicorn gateway:app --host 127.0.0.1 --port 8787 > gateway.log 2>&1 &
    echo $! > "$PID_FILE"
    sleep 2
    if kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo ""
        echo "=========================================="
        echo "  Installation complete!"
        echo "=========================================="
        echo ""
        echo "  Admin page: http://127.0.0.1:8787/admin"
        echo "  Log file:   $DIR/gateway.log"
        echo ""
        echo "  cgw commands:"
        echo "    cgw status    - Show status"
        echo "    cgw profiles  - List profiles"
        echo "    cgw switch    - Switch profile"
        echo "    cgw web       - Open admin page"
        echo "    cgw restart   - Restart gateway"
        echo "    cgw help      - Show help"
        echo ""
    else
        echo "Startup failed. Check log: $DIR/gateway.log"
        tail -5 "$DIR/gateway.log"
        exit 1
    fi
fi

# cgw — Claude Gateway

A multi-profile model gateway that lets Claude Desktop use third-party LLM providers (MiMo, DeepSeek, Qwen, etc.) through a local proxy. Switch between providers with one command or click.

[中文文档](README.zh-CN.md)

## Features

- **Multi-profile management** — configure multiple LLM providers, switch instantly
- **Model mapping** — map Claude-style model IDs to any upstream model
- **Web admin UI** — manage profiles, models, and Claude Desktop integration in the browser
- **CLI tool (`cgw`)** — check status, switch profiles, manage the gateway from the terminal
- **Claude Desktop integration** — one-click sync and restart for third-party inference
- **Hot reload** — model changes take effect without restarting the gateway

## Architecture

```
Claude Desktop
    │  (Claude-style model IDs)
    ▼
Local Gateway (cgw)
    │  (rewrites model names, routes to active profile)
    ▼
Third-party LLM API (MiMo, DeepSeek, Qwen, ...)
```

## Quick Start

```bash
git clone <repo-url> && cd claude_desktop_gateway
./install.sh
```

The installer will:
1. Create a Python virtual environment and install dependencies
2. Prompt for your first provider configuration (API key, upstream URL)
3. Install the `cgw` command to your PATH
4. Start the gateway

Then open **http://127.0.0.1:8787/admin** to manage everything from the browser.

## CLI Commands

```bash
cgw status              # Show gateway and profile status
cgw profiles            # List all profiles
cgw active              # Show active profile
cgw switch <name>       # Switch to a profile
cgw add                 # Add a new profile (interactive)
cgw edit <name>         # Edit a profile
cgw remove <name>       # Remove a profile
cgw start               # Start the gateway
cgw stop                # Stop the gateway
cgw restart             # Restart the gateway
cgw web                 # Open the web admin page
cgw logs                # View gateway logs
```

## Makefile

```bash
make install            # One-click install
make start              # Start gateway
make stop               # Stop gateway
make restart            # Restart gateway
make status             # Show status
make profiles           # List profiles
make switch PROFILE=x   # Switch profile
make web                # Open admin page
make logs               # View logs
```

## Configuration

### Profiles

Profiles are stored in `~/.claude-gateway/profiles.json`:

```json
{
  "version": 2,
  "active": "my-provider",
  "profiles": {
    "my-provider": {
      "upstream_url": "https://api.example.com/anthropic",
      "api_key": "your-api-key",
      "auth_scheme": "api-key",
      "models": [
        {
          "id": "claude-opus-4-6",
          "upstream": "provider-model-name",
          "display_name": "My Model"
        }
      ]
    }
  }
}
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `MIMO_API_KEY` | API key (also stored in `.env` file) |

### Model ID Requirements

Claude Desktop validates model IDs. They must:
- Contain `claude`, `opus`, `sonnet`, `haiku`, `fable`, or `anthropic`
- NOT match known competitor names (blocklist enforced by Claude Desktop)

Use Claude-style IDs (e.g., `claude-opus-4-6`) and map them to real upstream model names.

## Web Admin

Access at `http://127.0.0.1:8787/admin`:

- **Profile switcher** — top-right badge, click to manage environments
- **Model management** — add/edit/delete model mappings
- **Claude Desktop sync** — push config to Desktop, restart with confirmation
- **API key management** — configure provider API keys

## Project Structure

```
├── gateway.py           # FastAPI proxy server
├── profile_manager.py   # Multi-profile configuration manager
├── cli.py               # cgw command-line tool
├── admin_page.py        # Web admin UI (single-file HTML)
├── desktop_sync.py      # Claude Desktop integration
├── config_store.py      # Legacy config store (backward compatible)
├── install.sh           # One-click installer
├── Makefile             # Build/run commands
└── .gitignore           # Excludes secrets and runtime files
```

## Requirements

- Python 3.7+
- macOS (for Claude Desktop integration)
- Dependencies: `fastapi`, `uvicorn`, `httpx` (installed automatically)

## License

MIT

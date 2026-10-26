"""Claude Desktop third-party inference config sync.

Reads/writes Claude-3p configLibrary files, detects Desktop installation,
manages pending/apply state, and restarts the 3p instance.
"""

import json
import os
import signal
import subprocess
import time
from typing import Any, Dict, List, Optional

CLAUDE_3P_BASE = os.path.expanduser(
    "~/Library/Application Support/Claude-3p"
)
CONFIG_LIBRARY_DIR = os.path.join(CLAUDE_3P_BASE, "configLibrary")
META_PATH = os.path.join(CONFIG_LIBRARY_DIR, "_meta.json")
DESKTOP_APP = "/Applications/Claude.app"

DEFAULT_GATEWAY_BASE_URL = "http://127.0.0.1:8787"


def infer_tier(model_id):
    mid = model_id.lower()
    if "opus" in mid:
        return "opus"
    if "haiku" in mid:
        return "haiku"
    return "sonnet"


class DesktopSync:
    def __init__(self, base_path=None, gateway_base_url=None):
        self._base = base_path or CLAUDE_3P_BASE
        self._lib_dir = os.path.join(self._base, "configLibrary")
        self._meta_path = os.path.join(self._lib_dir, "_meta.json")
        self._gateway_base_url = gateway_base_url or DEFAULT_GATEWAY_BASE_URL

    # ── detection ───────────────────────────────

    def is_installed(self):
        return os.path.isdir(DESKTOP_APP)

    def is_running(self):
        return len(self.get_running_pids()) > 0

    def get_running_pids(self):
        # Match only Claude Desktop app, NOT Claude Code CLI or other tools
        try:
            out = subprocess.check_output(
                ["pgrep", "-f", "Claude.app/Contents/MacOS/Claude"],
                stderr=subprocess.DEVNULL,
            )
            return [int(p) for p in out.strip().split(b"\n") if p]
        except (subprocess.CalledProcessError, FileNotFoundError):
            return []

    # ── config library read/write ───────────────

    def _read_meta(self):
        if not os.path.exists(self._meta_path):
            return {"appliedId": None, "entries": []}
        try:
            with open(self._meta_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (ValueError, OSError):
            return {"appliedId": None, "entries": []}

    def _write_meta(self, meta):
        os.makedirs(self._lib_dir, exist_ok=True)
        tmp = self._meta_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)
            f.write("\n")
        os.replace(tmp, self._meta_path)

    def get_applied_id(self):
        meta = self._read_meta()
        return meta.get("appliedId")

    def get_applied_config(self):
        applied_id = self.get_applied_id()
        if not applied_id:
            return None
        path = os.path.join(self._lib_dir, applied_id + ".json")
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (ValueError, OSError):
            return None

    def write_config(self, config_data, name="Default"):
        os.makedirs(self._lib_dir, exist_ok=True)
        meta = self._read_meta()
        entries = meta.get("entries", [])
        if not isinstance(entries, list):
            entries = []

        target_id = None
        if entries and isinstance(entries[0], dict):
            target_id = entries[0].get("id")

        if not target_id:
            import uuid
            target_id = str(uuid.uuid4())
            entries = [{"id": target_id, "name": name}]

        path = os.path.join(self._lib_dir, target_id + ".json")
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        os.replace(tmp, path)

        meta["entries"] = entries
        meta["appliedId"] = target_id
        self._write_meta(meta)
        return target_id

    # ── sync: gateway → desktop ─────────────────

    def sync_from_gateway(self, models, api_key=""):
        inference_models = []
        for m in models:
            mid = m.get("id", "")
            inference_models.append({
                "name": mid,
                "labelOverride": m.get("display_name", mid),
                "anthropicFamilyTier": infer_tier(mid),
            })

        config = {
            "inferenceGatewayBaseUrl": self._gateway_base_url,
            "inferenceGatewayApiKey": api_key or "local-gateway",
            "inferenceGatewayAuthScheme": "x-api-key",
            "modelPrefer1mContext": True,
            "inferenceModels": inference_models,
            "inferenceProvider": "gateway",
            "inferenceCredentialKind": "static",
        }

        config_id = self.write_config(config)
        self._mark_pending()
        return {"config_id": config_id, "models": inference_models}

    def _mark_pending(self):
        state_path = os.path.join(self._base, ".gateway_sync_pending")
        with open(state_path, "w") as f:
            f.write(str(time.time()))

    def _clear_pending(self):
        state_path = os.path.join(self._base, ".gateway_sync_pending")
        if os.path.exists(state_path):
            os.remove(state_path)

    def is_pending(self):
        state_path = os.path.join(self._base, ".gateway_sync_pending")
        return os.path.exists(state_path)

    def get_pending_since(self):
        state_path = os.path.join(self._base, ".gateway_sync_pending")
        if not os.path.exists(state_path):
            return None
        try:
            with open(state_path, "r") as f:
                ts = float(f.read().strip())
            return ts
        except (ValueError, OSError):
            return None

    # ── sync: desktop → gateway ─────────────────

    def sync_to_gateway(self):
        config = self.get_applied_config()
        if not config:
            return []

        models = []
        for im in config.get("inferenceModels", []):
            models.append({
                "id": im.get("name", ""),
                "display_name": im.get("labelOverride", im.get("name", "")),
                "tier": im.get("anthropicFamilyTier", "sonnet"),
            })
        return models

    # ── apply & restart ─────────────────────────

    def apply_and_restart(self):
        result = self.restart_desktop()
        if result.get("ok"):
            self._clear_pending()
        return result

    def discard_pending(self):
        """Remove all synced configs and clear pending state."""
        meta = self._read_meta()
        applied_id = meta.get("appliedId")
        if applied_id:
            path = os.path.join(self._lib_dir, applied_id + ".json")
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass
        meta["entries"] = []
        meta["appliedId"] = None
        self._write_meta(meta)
        self._clear_pending()
        return True

    def restart_desktop(self):
        if not self.is_installed():
            return {"ok": False, "error": "Claude Desktop not installed"}

        pids = self.get_running_pids()
        for pid in pids:
            try:
                os.kill(pid, signal.SIGTERM)
            except (ProcessLookupError, PermissionError):
                pass

        # Wait for processes to actually exit (max 5 seconds)
        if pids:
            for _ in range(10):
                remaining = [p for p in pids if self._pid_alive(p)]
                if not remaining:
                    break
                time.sleep(0.5)
            # Force kill any stragglers
            for p in pids:
                if self._pid_alive(p):
                    try:
                        os.kill(p, signal.SIGKILL)
                    except (ProcessLookupError, PermissionError):
                        pass
            time.sleep(0.5)

        try:
            subprocess.Popen(
                ["open", "-a", "Claude"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return {"ok": True, "restarted": True, "killed_pids": pids}
        except FileNotFoundError:
            return {"ok": False, "error": "Cannot launch Claude Desktop"}

    @staticmethod
    def _pid_alive(pid):
        try:
            os.kill(pid, 0)
            return True
        except (ProcessLookupError, PermissionError):
            return False

    # ── status ──────────────────────────────────

    def get_status(self):
        return {
            "installed": self.is_installed(),
            "running": self.is_running(),
            "pending": self.is_pending(),
            "pending_since": self.get_pending_since(),
            "config": self.get_applied_config(),
        }

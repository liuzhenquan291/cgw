"""Model mapping configuration store with hot-reload support.

Persists model mappings to a JSON file. Supports add/update/delete without
restart via mtime-based file change detection.
Also manages API key via .env file.
"""

import json
import os
import threading
from typing import Any, Dict, List, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "model_config.json")
ENV_PATH = os.path.join(BASE_DIR, ".env")

DEFAULT_MODELS = [
    {
        "id": "claude-opus-4-6",
        "upstream": "mimo-v2.6-pro",
        "display_name": "MiMo V2.6 Pro",
        "notes": "",
    },
    {
        "id": "claude-sonnet-4-5-20241022",
        "upstream": "mimo-v2.6-flash",
        "display_name": "MiMo V2.6 Flash",
        "notes": "",
    },
]


class ConfigStore:
    def __init__(self, path: str = CONFIG_PATH) -> None:
        self._path = path
        self._lock = threading.Lock()
        self._models = []  # type: List[Dict[str, Any]]
        self._mtime = None  # type: Optional[float]
        self._config_error = None  # type: Optional[str]
        self._load_or_create()

    # ── private ──────────────────────────────────────────

    def _load_or_create(self) -> None:
        if not os.path.exists(self._path):
            self._models = [dict(m) for m in DEFAULT_MODELS]
            self._save_locked()
            return
        self._load_from_disk()

    def _load_from_disk(self) -> None:
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                data = json.load(f)
            raw = data.get("models", [])
            models = []
            for item in raw:
                if not isinstance(item, dict):
                    continue
                mid = str(item.get("id", "")).strip()
                upstream = str(item.get("upstream", "")).strip()
                if not mid or not upstream:
                    continue
                models.append({
                    "id": mid,
                    "upstream": upstream,
                    "display_name": str(item.get("display_name", "")).strip() or mid,
                    "notes": str(item.get("notes", "")).strip(),
                })
            self._models = models
            self._config_error = None
            self._mtime = os.path.getmtime(self._path)
        except (OSError, ValueError, KeyError) as e:
            self._config_error = str(e)

    def _maybe_reload(self) -> None:
        try:
            mtime = os.path.getmtime(self._path)
        except OSError:
            # File deleted — recreate from in-memory data
            self._save_locked()
            return
        if self._mtime is not None and mtime != self._mtime:
            self._load_from_disk()

    def _save_locked(self) -> None:
        data = {
            "version": 1,
            "models": self._models,
        }
        tmp = self._path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        os.replace(tmp, self._path)
        self._mtime = os.path.getmtime(self._path)
        self._config_error = None

    def _find_index(self, model_id: str) -> int:
        for i, m in enumerate(self._models):
            if m["id"] == model_id:
                return i
        return -1

    # ── public read ──────────────────────────────────────

    def get_upstream(self, model_id: str) -> Optional[str]:
        with self._lock:
            self._maybe_reload()
            idx = self._find_index(model_id)
            if idx >= 0:
                return self._models[idx]["upstream"]
            return None

    def list_models(self) -> List[Dict[str, Any]]:
        with self._lock:
            self._maybe_reload()
            return [dict(m) for m in self._models]

    def status(self) -> Dict[str, Any]:
        with self._lock:
            self._maybe_reload()
            return {
                "ok": self._config_error is None,
                "model_count": len(self._models),
                "config_path": self._path,
                "config_error": self._config_error,
            }

    # ── public write ─────────────────────────────────────

    def add_model(self, model_id: str, upstream: str,
                  display_name: str = "", notes: str = "") -> Dict[str, Any]:
        model_id = model_id.strip()
        upstream = upstream.strip()
        display_name = display_name.strip() or model_id
        notes = notes.strip()

        if not model_id:
            raise ValueError("Model ID cannot be empty")
        if not upstream:
            raise ValueError("Upstream model cannot be empty")

        with self._lock:
            self._maybe_reload()
            if self._find_index(model_id) >= 0:
                raise KeyError("Model ID already exists: {}".format(model_id))
            entry = {
                "id": model_id,
                "upstream": upstream,
                "display_name": display_name,
                "notes": notes,
            }
            self._models.append(entry)
            self._save_locked()
            return dict(entry)

    def update_model(self, model_id: str, upstream: str = None,
                     display_name: str = None, notes: str = None) -> Dict[str, Any]:
        with self._lock:
            self._maybe_reload()
            idx = self._find_index(model_id)
            if idx < 0:
                raise KeyError("Model not found: {}".format(model_id))

            entry = self._models[idx]
            if upstream is not None:
                upstream = upstream.strip()
                if not upstream:
                    raise ValueError("Upstream model cannot be empty")
                entry["upstream"] = upstream
            if display_name is not None:
                entry["display_name"] = display_name.strip() or model_id
            if notes is not None:
                entry["notes"] = notes.strip()

            self._save_locked()
            return dict(entry)

    def delete_model(self, model_id: str) -> bool:
        with self._lock:
            self._maybe_reload()
            idx = self._find_index(model_id)
            if idx < 0:
                raise KeyError("Model not found: {}".format(model_id))
            self._models.pop(idx)
            self._save_locked()
            return True

    def reset_to_defaults(self) -> None:
        with self._lock:
            self._models = [dict(m) for m in DEFAULT_MODELS]
            self._save_locked()


# ── .env API key management ─────────────────────────────


def read_env_api_key():
    if not os.path.exists(ENV_PATH):
        return ""
    with open(ENV_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("MIMO_API_KEY="):
                return line.split("=", 1)[1].strip()
    return ""


def write_env_api_key(api_key):
    lines = []
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip().startswith("MIMO_API_KEY="):
                    lines.append(line.rstrip("\n"))
    lines.append("MIMO_API_KEY={}".format(api_key))
    tmp = ENV_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    os.replace(tmp, ENV_PATH)

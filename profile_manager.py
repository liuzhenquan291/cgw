"""Multi-profile management for Claude Gateway.

Stores profiles in ~/.claude-gateway/profiles.json
Each profile: upstream_url, api_key, auth_scheme, models[]
"""

import json
import os
import threading
from typing import Any, Dict, List, Optional

CONFIG_DIR = os.path.expanduser("~/.claude-gateway")
PROFILES_PATH = os.path.join(CONFIG_DIR, "profiles.json")

DEFAULT_AUTH_SCHEME = "api-key"


class ProfileManager:
    def __init__(self, path=None):
        self._path = path or PROFILES_PATH
        self._lock = threading.Lock()
        self._data = {"version": 2, "active": "", "profiles": {}}
        self._load_or_create()

    def _load_or_create(self):
        if not os.path.exists(self._path):
            self._save_locked()
            return
        self._load_from_disk()

    def _load_from_disk(self):
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._data = {
                "version": 2,
                "active": str(data.get("active", "")),
                "profiles": data.get("profiles", {}),
            }
        except (OSError, ValueError):
            pass

    def _save_locked(self):
        os.makedirs(os.path.dirname(self._path), exist_ok=True)
        tmp = self._path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        os.replace(tmp, self._path)

    def _validate_profile(self, name, upstream_url, api_key, models):
        name = (name or "").strip()
        upstream_url = (upstream_url or "").strip().rstrip("/")
        api_key = (api_key or "").strip()
        if not name:
            raise ValueError("Profile name cannot be empty")
        if not upstream_url:
            raise ValueError("Upstream URL cannot be empty")
        if not api_key:
            raise ValueError("API key cannot be empty")
        validated = []
        for m in (models or []):
            mid = str(m.get("id", "")).strip()
            upstream = str(m.get("upstream", "")).strip()
            if not mid or not upstream:
                continue
            validated.append({
                "id": mid,
                "upstream": upstream,
                "display_name": str(m.get("display_name", "")).strip() or mid,
            })
        return name, upstream_url, api_key, validated

    def list_profiles(self):
        with self._lock:
            self._load_from_disk()
            return {
                "active": self._data["active"],
                "profiles": dict(self._data["profiles"]),
            }

    def get_profile(self, name):
        with self._lock:
            self._load_from_disk()
            p = self._data["profiles"].get(name)
            return dict(p) if p else None

    def get_active_profile(self):
        with self._lock:
            self._load_from_disk()
            name = self._data["active"]
            if not name:
                return None
            p = self._data["profiles"].get(name)
            if not p:
                return None
            result = dict(p)
            result["name"] = name
            return result

    def get_active_upstream(self):
        p = self.get_active_profile()
        if not p:
            return None
        return p.get("upstream_url")

    def get_active_api_key(self):
        p = self.get_active_profile()
        if not p:
            return None
        return p.get("api_key")

    def get_active_auth_scheme(self):
        p = self.get_active_profile()
        if not p:
            return DEFAULT_AUTH_SCHEME
        return p.get("auth_scheme", DEFAULT_AUTH_SCHEME)

    def get_active_models(self):
        p = self.get_active_profile()
        if not p:
            return []
        return p.get("models", [])

    def get_upstream_model(self, model_id):
        for m in self.get_active_models():
            if m["id"] == model_id:
                return m["upstream"]
        return None

    def add_profile(self, name, upstream_url, api_key, models=None, auth_scheme=DEFAULT_AUTH_SCHEME):
        name, upstream_url, api_key, validated = self._validate_profile(
            name, upstream_url, api_key, models
        )
        with self._lock:
            self._load_from_disk()
            if name in self._data["profiles"]:
                raise KeyError("Profile already exists: {}".format(name))
            self._data["profiles"][name] = {
                "upstream_url": upstream_url,
                "api_key": api_key,
                "auth_scheme": auth_scheme or DEFAULT_AUTH_SCHEME,
                "models": validated,
            }
            if not self._data["active"]:
                self._data["active"] = name
            self._save_locked()
            return {"name": name, "upstream_url": upstream_url, "models": validated}

    def update_profile(self, name, upstream_url=None, api_key=None, models=None, auth_scheme=None):
        with self._lock:
            self._load_from_disk()
            if name not in self._data["profiles"]:
                raise KeyError("Profile not found: {}".format(name))
            p = self._data["profiles"][name]
            if upstream_url is not None:
                u = upstream_url.strip().rstrip("/")
                if not u:
                    raise ValueError("Upstream URL cannot be empty")
                p["upstream_url"] = u
            if api_key is not None:
                k = api_key.strip()
                if not k:
                    raise ValueError("API key cannot be empty")
                p["api_key"] = k
            if auth_scheme is not None:
                p["auth_scheme"] = auth_scheme or DEFAULT_AUTH_SCHEME
            if models is not None:
                _, _, _, validated = self._validate_profile(name, p["upstream_url"], p["api_key"], models)
                p["models"] = validated
            self._save_locked()
            return dict(p)

    def delete_profile(self, name):
        with self._lock:
            self._load_from_disk()
            if name not in self._data["profiles"]:
                raise KeyError("Profile not found: {}".format(name))
            del self._data["profiles"][name]
            if self._data["active"] == name:
                remaining = list(self._data["profiles"].keys())
                self._data["active"] = remaining[0] if remaining else ""
            self._save_locked()
            return True

    def switch_profile(self, name):
        with self._lock:
            self._load_from_disk()
            if name not in self._data["profiles"]:
                raise KeyError("Profile not found: {}".format(name))
            self._data["active"] = name
            self._save_locked()
            return dict(self._data["profiles"][name])

    def add_model_to_profile(self, profile_name, model_id, upstream, display_name=""):
        with self._lock:
            self._load_from_disk()
            if profile_name not in self._data["profiles"]:
                raise KeyError("Profile not found: {}".format(profile_name))
            p = self._data["profiles"][profile_name]
            for m in p["models"]:
                if m["id"] == model_id:
                    raise KeyError("Model already exists: {}".format(model_id))
            p["models"].append({
                "id": model_id,
                "upstream": upstream,
                "display_name": display_name or model_id,
            })
            self._save_locked()

    def update_model_in_profile(self, profile_name, model_id, upstream=None, display_name=None):
        with self._lock:
            self._load_from_disk()
            if profile_name not in self._data["profiles"]:
                raise KeyError("Profile not found: {}".format(profile_name))
            p = self._data["profiles"][profile_name]
            for m in p["models"]:
                if m["id"] == model_id:
                    if upstream is not None:
                        u = upstream.strip()
                        if not u:
                            raise ValueError("Upstream cannot be empty")
                        m["upstream"] = u
                    if display_name is not None:
                        m["display_name"] = display_name.strip() or model_id
                    self._save_locked()
                    return
            raise KeyError("Model not found: {}".format(model_id))

    def remove_model_from_profile(self, profile_name, model_id):
        with self._lock:
            self._load_from_disk()
            if profile_name not in self._data["profiles"]:
                raise KeyError("Profile not found: {}".format(profile_name))
            p = self._data["profiles"][profile_name]
            before = len(p["models"])
            p["models"] = [m for m in p["models"] if m["id"] != model_id]
            if len(p["models"]) == before:
                raise KeyError("Model not found: {}".format(model_id))
            self._save_locked()

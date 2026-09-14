from __future__ import annotations

import hmac
import json
import os
import secrets
from pathlib import Path
from typing import Any

TOKEN_ENV = "CUICOMMANDER_API_TOKEN"
ACCESS_ENV = "CUICOMMANDER_ACCESS"
_ACCESS_ORDER = {"inspect": 0, "edit": 1, "full": 2}


def _state_directory() -> Path:
    import folder_paths

    getter = getattr(folder_paths, "get_system_user_directory", None)
    if callable(getter):
        return Path(getter("cuicommander"))
    return Path(folder_paths.get_user_directory()) / "__cuicommander"


def settings_path() -> Path:
    return _state_directory() / "connection.json"

def _load_file() -> dict[str, Any]:
    path = settings_path()
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def _write_file(value: dict[str, Any]) -> None:
    path = settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    try:
        os.chmod(temp, 0o600)
    except OSError:
        pass
    os.replace(temp, path)


def ensure_settings() -> dict[str, Any]:
    value = _load_file()
    changed = False
    if not isinstance(value.get("token"), str) or len(value["token"]) < 32:
        value["token"] = secrets.token_urlsafe(32)
        changed = True
    if value.get("accessLevel") not in _ACCESS_ORDER:
        value["accessLevel"] = "inspect"
        changed = True
    if changed:
        _write_file(value)
    return value


def token() -> str:
    configured = os.getenv(TOKEN_ENV, "").strip()
    if configured:
        return configured
    return str(ensure_settings()["token"])


def access_level() -> str:
    configured = os.getenv(ACCESS_ENV, "").strip().lower()
    if configured in _ACCESS_ORDER:
        return configured
    return str(ensure_settings()["accessLevel"])


def has_access(minimum: str) -> bool:
    return _ACCESS_ORDER.get(access_level(), -1) >= _ACCESS_ORDER[minimum]

def is_authorized(request: Any) -> bool:
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return False
    supplied = header[7:].strip()
    expected = token()
    return bool(supplied) and hmac.compare_digest(supplied, expected)


def public_connection_info() -> dict[str, str]:
    return {
        "accessLevel": access_level(),
        "credentialFile": str(settings_path()),
        "tokenEnvironmentVariable": TOKEN_ENV,
        "accessEnvironmentVariable": ACCESS_ENV,
    }


def internal_state_directory() -> Path:
    return _state_directory().resolve()

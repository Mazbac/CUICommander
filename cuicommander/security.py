from __future__ import annotations

import hmac
import json
import os
import secrets
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

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


def _normalize_public_base_url(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    parsed = urlsplit(text)
    if parsed.scheme.lower() != "https" or not parsed.hostname:
        raise ValueError("Public endpoint must be an https:// origin.")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("Public endpoint may not contain credentials, query, or fragment.")
    if parsed.path not in {"", "/"}:
        raise ValueError("Public endpoint must be an origin without a path.")
    host = parsed.hostname
    if not host:
        raise ValueError("Public endpoint must include a hostname.")
    port = parsed.port
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    authority = host if port in {None, 443} else f"{host}:{port}"
    return f"https://{authority}"


def custom_gpt_compatible_origin(value: Any) -> bool:
    try:
        normalized = _normalize_public_base_url(value)
    except ValueError:
        return False
    if not normalized:
        return False
    parsed = urlsplit(normalized)
    return parsed.scheme == "https" and parsed.port in {None, 443}


def ensure_settings() -> dict[str, Any]:
    value = _load_file()
    changed = False
    if not isinstance(value.get("token"), str) or len(value["token"]) < 32:
        value["token"] = secrets.token_urlsafe(32)
        changed = True
    if value.get("accessLevel") not in _ACCESS_ORDER:
        value["accessLevel"] = "inspect"
        changed = True
    public_base_url = value.get("publicBaseUrl")
    if public_base_url is not None:
        try:
            normalized = _normalize_public_base_url(public_base_url)
        except ValueError:
            normalized = ""
        if normalized != public_base_url:
            if normalized:
                value["publicBaseUrl"] = normalized
            else:
                value.pop("publicBaseUrl", None)
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


def public_base_url() -> str:
    return str(ensure_settings().get("publicBaseUrl", ""))


def has_access(minimum: str) -> bool:
    return _ACCESS_ORDER.get(access_level(), -1) >= _ACCESS_ORDER[minimum]


def set_access_level(value: Any) -> str:
    normalized = str(value).strip().lower()
    if normalized not in _ACCESS_ORDER:
        raise ValueError("accessLevel must be inspect, edit, or full.")
    if os.getenv(ACCESS_ENV, "").strip():
        raise RuntimeError(f"Access level is controlled by {ACCESS_ENV}.")
    settings = ensure_settings()
    settings["accessLevel"] = normalized
    _write_file(settings)
    return normalized


def set_public_base_url(value: Any) -> str:
    normalized = _normalize_public_base_url(value)
    settings = ensure_settings()
    if normalized:
        settings["publicBaseUrl"] = normalized
    else:
        settings.pop("publicBaseUrl", None)
    _write_file(settings)
    return normalized


def rotate_token() -> str:
    if os.getenv(TOKEN_ENV, "").strip():
        raise RuntimeError(f"Access key is controlled by {TOKEN_ENV}.")
    settings = ensure_settings()
    settings["token"] = secrets.token_urlsafe(32)
    _write_file(settings)
    return str(settings["token"])


def environment_overrides() -> dict[str, bool]:
    return {
        "accessLevel": bool(os.getenv(ACCESS_ENV, "").strip()),
        "accessKey": bool(os.getenv(TOKEN_ENV, "").strip()),
    }


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
        "publicBaseUrl": public_base_url(),
        "tokenEnvironmentVariable": TOKEN_ENV,
        "accessEnvironmentVariable": ACCESS_ENV,
    }


def internal_state_directory() -> Path:
    return _state_directory().resolve()

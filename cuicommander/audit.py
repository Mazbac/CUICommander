from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from typing import Any

from .security import internal_state_directory

MAX_ACTIVITY = 500


def _path() -> Path:
    return internal_state_directory() / "activity.json"


def _now_ms() -> int:
    return int(time.time() * 1000)


def _safe_detail(value: dict[str, Any] | None) -> dict[str, Any]:
    if not value:
        return {}
    allowed = {
        "root", "path", "targetRoot", "targetPath", "type", "method", "route",
        "jobId", "kind", "accessLevel", "provider", "funnelPort", "status",
    }
    return {str(key): value[key] for key in allowed if key in value}


def _load() -> list[dict[str, Any]]:
    try:
        path = _path()
        if not path.exists():
            return []
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ImportError, ValueError):
        return []
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)][-MAX_ACTIVITY:]


def _write(items: list[dict[str, Any]]) -> None:
    path = _path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(items[-MAX_ACTIVITY:], indent=2) + "\n", encoding="utf-8")
    try:
        os.chmod(temp, 0o600)
    except OSError:
        pass
    os.replace(temp, path)


def record_activity(action: str, detail: dict[str, Any] | None = None) -> dict[str, Any]:
    item = {
        "id": str(uuid.uuid4()),
        "at": _now_ms(),
        "action": str(action),
        "detail": _safe_detail(detail),
    }
    try:
        items = _load()
        items.append(item)
        _write(items)
    except (OSError, ImportError, TypeError, ValueError):
        pass
    return item


def list_activity(limit: int = 100) -> list[dict[str, Any]]:
    bounded = max(1, min(int(limit), MAX_ACTIVITY))
    return list(reversed(_load()[-bounded:]))


def clear_activity_for_tests() -> None:
    try:
        _path().unlink(missing_ok=True)
    except OSError:
        pass

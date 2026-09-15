from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from .security import internal_state_directory


def _safe_id(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9._-]+", "-", value.lower()).strip("-")
    return cleaned or "root"


def _root_record(root_id: str, label: str, path: str, source: str) -> dict[str, Any]:
    absolute = os.path.realpath(os.path.abspath(path))
    return {
        "id": root_id,
        "label": label,
        "path": absolute,
        "source": source,
        "exists": os.path.isdir(absolute),
    }


def discover_roots() -> list[dict[str, Any]]:
    import folder_paths

    roots: list[dict[str, Any]] = []
    roots.append(_root_record("comfyui", "ComfyUI base directory", folder_paths.base_path, "core"))

    named_getters = {
        "input": ("Input", folder_paths.get_input_directory),
        "output": ("Output", folder_paths.get_output_directory),
        "temp": ("Temp", folder_paths.get_temp_directory),
        "user": ("User data", folder_paths.get_user_directory),
    }
    for root_id, (label, getter) in named_getters.items():
        roots.append(_root_record(root_id, label, getter(), "core"))

    models_dir = getattr(folder_paths, "models_dir", None)
    if isinstance(models_dir, str) and models_dir:
        roots.append(_root_record("models", "Models", models_dir, "core"))

    used_ids = {item["id"] for item in roots}
    for folder_name, definition in folder_paths.folder_names_and_paths.items():
        paths = definition[0] if isinstance(definition, tuple) and definition else []
        for index, folder_path in enumerate(paths):
            base_id = f"registered.{_safe_id(str(folder_name))}.{index}"
            root_id = base_id
            suffix = 2
            while root_id in used_ids:
                root_id = f"{base_id}.{suffix}"
                suffix += 1
            used_ids.add(root_id)
            label = f"{folder_name} [{index + 1}]"
            roots.append(_root_record(root_id, label, str(folder_path), "folder_paths"))

    return roots


def roots_by_id() -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in discover_roots()}


def resolve_path(root_id: str, relative_path: str, allow_missing: bool = False) -> tuple[Path, Path]:
    roots = roots_by_id()
    if root_id not in roots:
        raise ValueError("Unknown ComfyUI root.")
    if not isinstance(relative_path, str) or "\x00" in relative_path:
        raise ValueError("Invalid relative path.")

    normalized = relative_path.replace("\\", "/")
    relative = Path(normalized)
    if normalized.startswith("/") or relative.is_absolute() or relative.drive:
        raise ValueError("Path must be relative to the selected ComfyUI root.")
    if any(part == ".." for part in relative.parts):
        raise ValueError("Path traversal is not allowed.")

    base = Path(roots[root_id]["path"]).resolve()
    candidate = base.joinpath(*relative.parts)
    if candidate.exists() or candidate.is_symlink():
        resolved = candidate.resolve()
        _require_inside(base, resolved)
        _require_not_internal(resolved)
        return base, candidate

    if not allow_missing:
        raise FileNotFoundError("ComfyUI resource does not exist.")

    ancestor = candidate.parent
    while not ancestor.exists() and ancestor != ancestor.parent:
        ancestor = ancestor.parent
    resolved_ancestor = ancestor.resolve()
    _require_inside(base, resolved_ancestor)
    _require_not_internal(resolved_ancestor)
    return base, candidate


def _require_inside(base: Path, candidate: Path) -> None:
    try:
        if os.path.commonpath((str(base), str(candidate))) != str(base):
            raise ValueError("Path escaped its ComfyUI root.")
    except ValueError as error:
        raise ValueError("Path escaped its ComfyUI root.") from error


def _require_not_internal(candidate: Path) -> None:
    internal = internal_state_directory().resolve()
    try:
        inside = os.path.commonpath((str(internal), str(candidate))) == str(internal)
    except ValueError:
        inside = False
    if inside:
        raise PermissionError("CUICommander internal credential state is not a managed resource.")


def contains_internal_state(candidate: Path) -> bool:
    if candidate.is_symlink():
        return False
    internal = internal_state_directory().resolve()
    resolved = candidate.resolve()
    try:
        return os.path.commonpath((str(resolved), str(internal))) == str(resolved)
    except ValueError:
        return False

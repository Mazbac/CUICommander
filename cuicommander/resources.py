from __future__ import annotations

import base64
import errno
import hashlib
import mimetypes
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from .roots import contains_internal_state, resolve_path

MAX_PREVIEW_BYTES = 65536
MAX_READ_BYTES = 128 * 1024
DEFAULT_READ_BYTES = 64 * 1024
MAX_PATCH_BYTES = 256 * 1024
MAX_DIRECTORY_ITEMS = 250
CONTENT_HASH_LIMIT = 32 * 1024 * 1024
LARGE_FILE_SAMPLE_BYTES = 64 * 1024


def _resource_type(path: Path) -> str:
    if path.is_symlink():
        return "symlink"
    if path.is_dir():
        return "directory"
    return "file"


def _metadata(path: Path) -> dict[str, Any]:
    stat = path.lstat()
    resource_type = _resource_type(path)
    result: dict[str, Any] = {
        "name": path.name,
        "type": resource_type,
        "size": stat.st_size if resource_type != "directory" else None,
        "modifiedNs": stat.st_mtime_ns,
    }
    if resource_type == "symlink":
        result["target"] = os.readlink(path)
    return result


def fingerprint(path: Path) -> tuple[str, str]:
    if path.is_symlink():
        value = f"symlink:{os.readlink(path)}"
        return hashlib.sha256(value.encode("utf-8")).hexdigest(), "symlink"

    stat = path.stat()
    if path.is_dir():
        return _directory_fingerprint(path), "tree-metadata"

    if stat.st_size <= CONTENT_HASH_LIMIT:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest(), "sha256"

    digest = hashlib.sha256()
    digest.update(f"{stat.st_size}:{stat.st_mtime_ns}".encode("utf-8"))
    with path.open("rb") as handle:
        digest.update(handle.read(LARGE_FILE_SAMPLE_BYTES))
        if stat.st_size > LARGE_FILE_SAMPLE_BYTES:
            handle.seek(max(0, stat.st_size - LARGE_FILE_SAMPLE_BYTES))
            digest.update(handle.read(LARGE_FILE_SAMPLE_BYTES))
    return digest.hexdigest(), "sampled-sha256"


def _directory_fingerprint(path: Path) -> str:
    digest = hashlib.sha256()
    root_stat = path.stat()
    digest.update(f"root:{root_stat.st_mtime_ns}".encode("utf-8"))

    for current_root, dir_names, file_names in os.walk(path, followlinks=False):
        dir_names.sort()
        file_names.sort()
        current = Path(current_root)
        for name in [*dir_names, *file_names]:
            item = current / name
            relative = item.relative_to(path).as_posix()
            stat = item.lstat()
            digest.update(f"{relative}:{stat.st_mode}:{stat.st_size}:{stat.st_mtime_ns}".encode("utf-8"))
            if item.is_symlink():
                digest.update(os.readlink(item).encode("utf-8", errors="surrogatepass"))
    return digest.hexdigest()


def inspect_resource(
    root: str,
    relative_path: str,
    *,
    offset: int = 0,
    limit: int = MAX_DIRECTORY_ITEMS,
    expected_fingerprint: str | None = None,
) -> dict[str, Any]:
    _, path = resolve_path(root, relative_path)
    info = _metadata(path)
    info["root"] = root
    info["path"] = relative_path.replace("\\", "/")
    current, mode = fingerprint(path)
    if expected_fingerprint and current != str(expected_fingerprint).lower():
        raise RuntimeError("Resource changed while it was being paged; inspect again from offset 0.")
    info["fingerprint"] = current
    info["fingerprintMode"] = mode

    if path.is_symlink():
        info["preview"] = None
        return info
    if path.is_dir():
        info.update(_inspect_directory(path, offset=offset, limit=limit))
    else:
        info.update(_inspect_file(path))
    return info


def _inspect_directory(path: Path, *, offset: int = 0, limit: int = MAX_DIRECTORY_ITEMS) -> dict[str, Any]:
    if offset < 0:
        raise ValueError("offset must be zero or greater.")
    bounded_limit = max(1, min(int(limit), MAX_DIRECTORY_ITEMS))
    items: list[dict[str, Any]] = []
    with os.scandir(path) as entries:
        for entry in entries:
            try:
                items.append(_metadata(Path(entry.path)))
            except OSError:
                items.append({"name": entry.name, "type": "unreadable"})
    items.sort(key=lambda item: (item.get("type") != "directory", str(item.get("name", "")).lower()))
    page = items[offset : offset + bounded_limit]
    next_offset = offset + len(page)
    complete = next_offset >= len(items)
    return {
        "items": page,
        "itemOffset": offset,
        "itemLimit": bounded_limit,
        "totalItems": len(items),
        "nextOffset": None if complete else next_offset,
        "truncated": not complete,
    }


def _inspect_file(path: Path) -> dict[str, Any]:
    mime, _ = mimetypes.guess_type(path.name)
    result: dict[str, Any] = {"mimeType": mime or "application/octet-stream"}
    if path.stat().st_size > MAX_PREVIEW_BYTES:
        result["preview"] = None
        result["previewTruncated"] = True
        return result

    raw = path.read_bytes()
    try:
        result["preview"] = raw.decode("utf-8")
        result["previewEncoding"] = "utf-8"
    except UnicodeDecodeError:
        result["preview"] = base64.b64encode(raw).decode("ascii")
        result["previewEncoding"] = "base64"
    result["previewTruncated"] = False
    return result



def _bounded_read_size(value: Any) -> int:
    requested = DEFAULT_READ_BYTES if value is None else int(value)
    if requested < 1024:
        raise ValueError("maxBytes must be at least 1024.")
    return min(requested, MAX_READ_BYTES)


def _decode_utf8_prefix(raw: bytes, limit: int) -> tuple[str, int] | None:
    candidate = raw[:limit]
    try:
        return candidate.decode("utf-8"), len(candidate)
    except UnicodeDecodeError as error:
        if error.reason == "unexpected end of data" and error.end == len(candidate):
            complete = candidate[: error.start]
            if complete:
                return complete.decode("utf-8"), len(complete)
        return None


def read_resource(input_data: dict[str, Any]) -> dict[str, Any]:
    root_id = str(input_data.get("root", ""))
    relative_path = str(input_data.get("path", ""))
    offset = int(input_data.get("offset", 0))
    if offset < 0:
        raise ValueError("offset must be zero or greater.")
    max_bytes = _bounded_read_size(input_data.get("maxBytes"))
    encoding = str(input_data.get("encoding", "auto")).lower()
    if encoding not in {"auto", "utf-8", "base64"}:
        raise ValueError("encoding must be auto, utf-8, or base64.")

    _, path = resolve_path(root_id, relative_path)
    if path.is_symlink() or not path.is_file():
        raise ValueError("Chunked read targets regular files only.")
    current, mode = fingerprint(path)
    expected = input_data.get("expectedFingerprint")
    if expected and current != str(expected).lower():
        raise RuntimeError("Resource changed during chunked read; restart from offset 0.")
    total = path.stat().st_size
    if offset > total:
        raise ValueError("offset exceeds file size.")

    mime, _ = mimetypes.guess_type(path.name)
    with path.open("rb") as handle:
        handle.seek(offset)
        raw = handle.read(max_bytes + 4)

    payload = raw[:max_bytes]
    result: dict[str, Any] = {
        "root": root_id,
        "path": relative_path.replace("\\", "/"),
        "size": total,
        "offset": offset,
        "fingerprint": current,
        "fingerprintMode": mode,
        "mimeType": mime or "application/octet-stream",
    }
    decoded = None if encoding == "base64" else _decode_utf8_prefix(raw, max_bytes)
    if decoded is not None:
        text, consumed = decoded
        result["encoding"] = "utf-8"
        result["content"] = text
    elif encoding == "utf-8":
        raise ValueError("Requested chunk is not valid UTF-8 at this byte offset.")
    else:
        consumed = len(payload)
        result["encoding"] = "base64"
        result["contentBase64"] = base64.b64encode(payload).decode("ascii")

    next_offset = offset + consumed
    eof = next_offset >= total
    result["bytesRead"] = consumed
    result["eof"] = eof
    result["nextOffset"] = None if eof else next_offset
    return result

def _decode_content(input_data: dict[str, Any]) -> bytes:
    has_text = "content" in input_data
    has_base64 = "contentBase64" in input_data
    if has_text == has_base64:
        raise ValueError("Provide exactly one of content or contentBase64.")
    if has_base64:
        try:
            return base64.b64decode(str(input_data["contentBase64"]), validate=True)
        except ValueError as error:
            raise ValueError("contentBase64 is not valid Base64.") from error
    return str(input_data["content"]).encode("utf-8")


def _require_fingerprint(path: Path, expected: str | None) -> None:
    if not expected:
        raise ValueError("A fresh expectedFingerprint from inspect is required.")
    current, _ = fingerprint(path)
    if current != str(expected).lower():
        raise RuntimeError("Resource changed after inspection.")


def _require_non_root(relative_path: str, operation: str) -> None:
    if not relative_path.replace("\\", "/").strip("/"):
        raise ValueError(f"{operation} a root is not allowed.")


def _ensure_parent(path: Path, create: bool) -> None:
    if path.parent.exists():
        return
    if not create:
        raise FileNotFoundError("Parent directory does not exist.")
    path.parent.mkdir(parents=True, exist_ok=True)


def create_resource(input_data: dict[str, Any]) -> dict[str, Any]:
    root = str(input_data.get("root", ""))
    relative_path = str(input_data.get("path", ""))
    resource_type = str(input_data.get("type", "file"))
    _, path = resolve_path(root, relative_path, allow_missing=True)
    if path.exists() or path.is_symlink():
        raise FileExistsError("Target already exists.")

    create_parents = bool(input_data.get("parents", True))
    if resource_type == "directory":
        path.mkdir(parents=create_parents, exist_ok=False)
    elif resource_type == "file":
        _ensure_parent(path, create_parents)
        data = _decode_content(input_data)
        with tempfile.NamedTemporaryFile(delete=False, dir=path.parent) as handle:
            handle.write(data)
            temp_name = handle.name
        os.replace(temp_name, path)
    else:
        raise ValueError("type must be file or directory.")
    return inspect_resource(root, relative_path)


def update_resource(input_data: dict[str, Any]) -> dict[str, Any]:
    root = str(input_data.get("root", ""))
    relative_path = str(input_data.get("path", ""))
    _, path = resolve_path(root, relative_path)
    if path.is_symlink() or not path.is_file():
        raise ValueError("Structured update targets regular files only.")
    _require_fingerprint(path, input_data.get("expectedFingerprint"))
    data = _decode_content(input_data)
    with tempfile.NamedTemporaryFile(delete=False, dir=path.parent) as handle:
        handle.write(data)
        temp_name = handle.name
    os.replace(temp_name, path)
    return inspect_resource(root, relative_path)



def patch_resource(input_data: dict[str, Any]) -> dict[str, Any]:
    root_id = str(input_data.get("root", ""))
    relative_path = str(input_data.get("path", ""))
    _, path = resolve_path(root_id, relative_path)
    if path.is_symlink() or not path.is_file():
        raise ValueError("Chunked patch targets regular files only.")
    _require_fingerprint(path, input_data.get("expectedFingerprint"))

    offset = int(input_data.get("offset", 0))
    delete_bytes = int(input_data.get("deleteBytes", 0))
    size = path.stat().st_size
    if offset < 0 or offset > size:
        raise ValueError("offset must be within the current file.")
    if delete_bytes < 0 or offset + delete_bytes > size:
        raise ValueError("deleteBytes exceeds the current file bounds.")
    replacement = _decode_content(input_data)
    if len(replacement) > MAX_PATCH_BYTES:
        raise ValueError("Patch content exceeds 256 KiB; apply multiple smaller patches.")

    temp_name = ""
    try:
        with path.open("rb") as source, tempfile.NamedTemporaryFile(
            delete=False, dir=path.parent
        ) as target:
            temp_name = target.name
            remaining = offset
            while remaining:
                chunk = source.read(min(1024 * 1024, remaining))
                if not chunk:
                    raise OSError("Unexpected end of file while copying patch prefix.")
                target.write(chunk)
                remaining -= len(chunk)

            target.write(replacement)
            source.seek(offset + delete_bytes)
            shutil.copyfileobj(source, target, length=1024 * 1024)
            target.flush()
            os.fsync(target.fileno())
        os.replace(temp_name, path)
        temp_name = ""
    finally:
        if temp_name:
            try:
                Path(temp_name).unlink(missing_ok=True)
            except OSError:
                pass
    return inspect_resource(root_id, relative_path)

def move_resource(input_data: dict[str, Any]) -> dict[str, Any]:
    root = str(input_data.get("root", ""))
    relative_path = str(input_data.get("path", ""))
    target_root = str(input_data.get("targetRoot", root))
    target_path = str(input_data.get("targetPath", ""))
    _require_non_root(relative_path, "Moving")
    _require_non_root(target_path, "Moving to")
    _, source = resolve_path(root, relative_path)
    _, target = resolve_path(target_root, target_path, allow_missing=True)
    if source.is_dir() and not source.is_symlink() and contains_internal_state(source):
        raise PermissionError("Cannot move a directory that contains CUICommander credential state.")
    _require_fingerprint(source, input_data.get("expectedFingerprint"))
    if target.exists() or target.is_symlink():
        raise FileExistsError("Move target already exists.")
    target.parent.mkdir(parents=True, exist_ok=True)
    _move_path(source, target)
    return inspect_resource(target_root, target_path)


def _move_path(source: Path, target: Path) -> None:
    try:
        os.replace(source, target)
        return
    except OSError as error:
        if error.errno != errno.EXDEV and getattr(error, "winerror", None) != 17:
            raise

    shutil.move(str(source), str(target))


def delete_resource(input_data: dict[str, Any]) -> dict[str, Any]:
    root = str(input_data.get("root", ""))
    relative_path = str(input_data.get("path", ""))
    _require_non_root(relative_path, "Deleting")
    _, path = resolve_path(root, relative_path)
    if path.is_dir() and not path.is_symlink() and contains_internal_state(path):
        raise PermissionError("Cannot delete a directory that contains CUICommander credential state.")
    _require_fingerprint(path, input_data.get("expectedFingerprint"))

    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        if any(path.iterdir()) and not bool(input_data.get("recursive")):
            raise ValueError("Directory is not empty; recursive=true is required.")
        if bool(input_data.get("recursive")):
            shutil.rmtree(path)
        else:
            path.rmdir()
    return {"root": root, "path": relative_path.replace("\\", "/"), "deleted": True}

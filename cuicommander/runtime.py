from __future__ import annotations

import base64
import os
import re
import tempfile
import uuid
from collections import OrderedDict
from typing import Any, BinaryIO
from urllib.parse import urlencode

MAX_RESPONSE_BYTES = 2 * 1024 * 1024
MAX_RESPONSE_CHUNK_BYTES = 128 * 1024
DEFAULT_RESPONSE_CHUNK_BYTES = 64 * 1024
DEFAULT_MAX_SPOOLED_RESPONSE_BYTES = 256 * 1024 * 1024
MAX_RETAINED_RESPONSES = 4
_ALLOWED_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}
_RESPONSES: OrderedDict[str, dict[str, Any]] = OrderedDict()


def _max_spooled_response_bytes() -> int:
    configured = os.getenv("CUICOMMANDER_MAX_NATIVE_RESPONSE_BYTES", "").strip()
    if not configured:
        return DEFAULT_MAX_SPOOLED_RESPONSE_BYTES
    try:
        value = int(configured)
    except ValueError:
        return DEFAULT_MAX_SPOOLED_RESPONSE_BYTES
    return max(MAX_RESPONSE_BYTES + 1, value)


def _native_origin() -> tuple[str, bool]:
    from comfy.cli_args import args

    listen = str(getattr(args, "listen", "127.0.0.1") or "127.0.0.1")
    host = listen.split(",", 1)[0].strip()
    if host in {"0.0.0.0", "127.0.0.1", "localhost", ""}:
        host = "127.0.0.1"
    elif host in {"::", "::1"}:
        host = "[::1]"
    port = int(getattr(args, "port", 8188))
    tls = bool(getattr(args, "tls_keyfile", None) or getattr(args, "tls_certfile", None))
    scheme = "https" if tls else "http"
    return f"{scheme}://{host}:{port}", tls


def _route_exists(method: str, path: str) -> bool:
    from server import PromptServer

    for route in PromptServer.instance.app.router.routes():
        if str(getattr(route, "method", "")).upper() not in {method, "*"}:
            continue
        resource = getattr(route, "resource", None)
        if resource is None:
            continue
        info = resource.get_info() if hasattr(resource, "get_info") else {}
        pattern = info.get("pattern") if isinstance(info, dict) else None
        if pattern is not None and pattern.fullmatch(path):
            return True
        canonical = str(getattr(resource, "canonical", ""))
        if canonical == path or _canonical_matches(canonical, path):
            return True
    return False


def _canonical_matches(canonical: str, path: str) -> bool:
    if not canonical or "{" not in canonical:
        return False
    escaped = re.escape(canonical)
    expression = re.sub(r"\\\{[^}]+\\\}", r"[^/]+", escaped)
    return re.fullmatch(expression, path) is not None


def _validate_request(input_data: dict[str, Any]) -> tuple[str, str, dict[str, Any], Any]:
    method = str(input_data.get("method", "GET")).upper()
    path = str(input_data.get("route", ""))
    query = input_data.get("query") or {}
    body = input_data.get("body")
    if method not in _ALLOWED_METHODS:
        raise ValueError("method must be GET, POST, PUT, PATCH, or DELETE.")
    if not path.startswith("/") or "://" in path or "?" in path or "#" in path:
        raise ValueError("route must be an absolute ComfyUI path without host, query, or fragment.")
    if path.startswith("/cuicommander/"):
        raise ValueError("CUICommander routes cannot be recursively executed.")
    if not isinstance(query, dict):
        raise ValueError("query must be an object.")
    if method != "GET" and input_data.get("confirmed") is not True:
        raise PermissionError("Mutating native route execution requires confirmed=true.")
    if not _route_exists(method, path):
        raise ValueError("The requested method/path is not present in the live ComfyUI route table.")
    return method, path, query, body


def _register_response(handle: BinaryIO, size: int, content_type: str) -> str:
    response_id = str(uuid.uuid4())
    _RESPONSES[response_id] = {
        "handle": handle,
        "size": int(size),
        "contentType": str(content_type or "application/octet-stream"),
    }
    _RESPONSES.move_to_end(response_id)
    while len(_RESPONSES) > MAX_RETAINED_RESPONSES:
        _, item = _RESPONSES.popitem(last=False)
        item["handle"].close()
    return response_id


def _store_response_bytes(raw: bytes, content_type: str) -> str:
    if len(raw) > _max_spooled_response_bytes():
        raise RuntimeError("Native response exceeds the configured spool safety limit.")
    handle = tempfile.SpooledTemporaryFile(max_size=MAX_RESPONSE_BYTES, mode="w+b")
    handle.write(raw)
    handle.seek(0)
    return _register_response(handle, len(raw), content_type)


def _bounded_chunk_size(value: Any) -> int:
    requested = DEFAULT_RESPONSE_CHUNK_BYTES if value is None else int(value)
    if requested < 1024:
        raise ValueError("maxBytes must be at least 1024.")
    return min(requested, MAX_RESPONSE_CHUNK_BYTES)


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


def read_runtime_response(input_data: dict[str, Any]) -> dict[str, Any]:
    response_id = str(input_data.get("responseId", ""))
    item = _RESPONSES.get(response_id)
    if item is None:
        raise KeyError("Unknown or expired native response id.")
    _RESPONSES.move_to_end(response_id)

    offset = int(input_data.get("offset", 0))
    total = int(item["size"])
    if offset < 0 or offset > total:
        raise ValueError("offset must be within the retained response.")
    max_bytes = _bounded_chunk_size(input_data.get("maxBytes"))
    encoding = str(input_data.get("encoding", "auto")).lower()
    if encoding not in {"auto", "utf-8", "base64"}:
        raise ValueError("encoding must be auto, utf-8, or base64.")

    handle = item["handle"]
    handle.seek(offset)
    raw = handle.read(max_bytes + 4)
    payload = raw[:max_bytes]
    decoded = None if encoding == "base64" else _decode_utf8_prefix(raw, max_bytes)
    result: dict[str, Any] = {
        "responseId": response_id,
        "size": total,
        "offset": offset,
        "contentType": item["contentType"],
    }
    if decoded is not None:
        text, consumed = decoded
        result["encoding"] = "utf-8"
        result["content"] = text
    elif encoding == "utf-8":
        raise ValueError("Requested response chunk is not valid UTF-8 at this byte offset.")
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


async def execute_native(input_data: dict[str, Any]) -> dict[str, Any]:
    import aiohttp

    method, path, query, body = _validate_request(input_data)
    origin, tls = _native_origin()
    query_string = urlencode(query, doseq=True)
    url = f"{origin}{path}"
    if query_string:
        url = f"{url}?{query_string}"

    timeout = aiohttp.ClientTimeout(total=120, connect=15, sock_read=120)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        request_kwargs: dict[str, Any] = {"ssl": False if tls else None}
        if body is not None:
            request_kwargs["json"] = body
        async with session.request(method, url, **request_kwargs) as response:
            raw = await response.content.read(MAX_RESPONSE_BYTES + 1)
            if len(raw) <= MAX_RESPONSE_BYTES:
                return {
                    "method": method,
                    "route": path,
                    "status": response.status,
                    "contentType": response.content_type,
                    "body": _decode_response(raw, response.content_type),
                    "bodyTruncated": False,
                    "responseId": None,
                    "responseSize": len(raw),
                    "nextOffset": None,
                }

            handle = tempfile.SpooledTemporaryFile(max_size=MAX_RESPONSE_BYTES, mode="w+b")
            size = 0
            try:
                handle.write(raw)
                size = len(raw)
                limit = _max_spooled_response_bytes()
                async for chunk in response.content.iter_chunked(1024 * 1024):
                    size += len(chunk)
                    if size > limit:
                        raise RuntimeError(
                            "Native response exceeds the configured spool safety limit. "
                            "Increase CUICOMMANDER_MAX_NATIVE_RESPONSE_BYTES if this route legitimately needs more."
                        )
                    handle.write(chunk)
                handle.seek(0)
                response_id = _register_response(handle, size, response.content_type)
                handle = None
            finally:
                if handle is not None:
                    handle.close()

            return {
                "method": method,
                "route": path,
                "status": response.status,
                "contentType": response.content_type,
                "body": None,
                "bodyTruncated": True,
                "responseId": response_id,
                "responseSize": size,
                "nextOffset": 0,
            }


def _decode_response(raw: bytes, content_type: str) -> Any:
    if not raw:
        return None
    if content_type == "application/json" or content_type.endswith("+json"):
        import json

        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            pass
    if content_type.startswith("text/"):
        return raw.decode("utf-8", errors="replace")
    return {"encoding": "base64", "data": base64.b64encode(raw).decode("ascii")}


def _clear_responses_for_tests() -> None:
    while _RESPONSES:
        _, item = _RESPONSES.popitem(last=False)
        item["handle"].close()

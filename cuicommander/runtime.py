from __future__ import annotations

import base64
import re
from typing import Any
from urllib.parse import urlencode

MAX_RESPONSE_BYTES = 2 * 1024 * 1024
_ALLOWED_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}


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
            truncated = len(raw) > MAX_RESPONSE_BYTES
            raw = raw[:MAX_RESPONSE_BYTES]
            return {
                "method": method,
                "route": path,
                "status": response.status,
                "contentType": response.content_type,
                "body": _decode_response(raw, response.content_type),
                "bodyTruncated": truncated,
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

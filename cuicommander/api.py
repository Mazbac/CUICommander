from __future__ import annotations

import json
from typing import Any

from aiohttp import web

from .discovery import discover
from .openapi import build_schema
from .resources import create_resource, delete_resource, inspect_resource, move_resource, update_resource
from .roots import discover_roots
from .security import access_level, has_access, is_authorized, public_connection_info

VERSION = "0.1.0-dev"
_REGISTERED = False


def _error(status: int, code: str, message: str) -> web.Response:
    return web.json_response({"error": code, "message": message}, status=status)


def _exception_response(error: Exception) -> web.Response:
    if isinstance(error, FileNotFoundError):
        return _error(404, "not_found", str(error))
    if isinstance(error, FileExistsError):
        return _error(409, "already_exists", str(error))
    if isinstance(error, PermissionError):
        return _error(403, "forbidden", str(error))
    if isinstance(error, RuntimeError):
        return _error(409, "stale_resource", str(error))
    if isinstance(error, (ValueError, TypeError, json.JSONDecodeError)):
        return _error(400, "invalid_request", str(error))
    return _error(500, "operation_failed", type(error).__name__)

async def _json(request: web.Request) -> dict[str, Any]:
    value = await request.json()
    if not isinstance(value, dict):
        raise ValueError("JSON request body must be an object.")
    return value


def _authorized(request: web.Request, minimum: str = "inspect") -> web.Response | None:
    if not is_authorized(request):
        return _error(401, "unauthorized", "A valid CUICommander bearer credential is required.")
    if not has_access(minimum):
        return _error(403, "access_level", f"This operation requires {minimum} access.")
    return None


async def openapi_handler(request: web.Request) -> web.Response:
    server_url = f"{request.scheme}://{request.host}"
    schema = build_schema(server_url, VERSION)
    return web.json_response(schema)


async def manifest_handler(request: web.Request) -> web.Response:
    denied = _authorized(request)
    if denied:
        return denied
    return web.json_response(
        {
            "version": VERSION,
            "accessLevel": access_level(),
            "connection": public_connection_info(),
            "rootCount": len(discover_roots()),
            "machineModel": "Discover/Inspect -> Create/Read/Update/Delete -> Execute",
            "noAdapterInvariant": True,
        }
    )

async def discover_handler(request: web.Request) -> web.Response:
    denied = _authorized(request)
    if denied:
        return denied
    try:
        body = await _json(request)
        result = discover(
            str(body.get("kind", "")),
            str(body.get("query", "")),
            int(body.get("limit", 100)),
        )
        return web.json_response({"items": result})
    except Exception as error:
        return _exception_response(error)


async def inspect_handler(request: web.Request) -> web.Response:
    denied = _authorized(request)
    if denied:
        return denied
    try:
        body = await _json(request)
        return web.json_response(
            inspect_resource(str(body.get("root", "")), str(body.get("path", "")))
        )
    except Exception as error:
        return _exception_response(error)


async def create_handler(request: web.Request) -> web.Response:
    denied = _authorized(request, "edit")
    if denied:
        return denied
    try:
        return web.json_response(create_resource(await _json(request)))
    except Exception as error:
        return _exception_response(error)

async def update_handler(request: web.Request) -> web.Response:
    denied = _authorized(request, "edit")
    if denied:
        return denied
    try:
        return web.json_response(update_resource(await _json(request)))
    except Exception as error:
        return _exception_response(error)


async def move_handler(request: web.Request) -> web.Response:
    denied = _authorized(request, "edit")
    if denied:
        return denied
    try:
        return web.json_response(move_resource(await _json(request)))
    except Exception as error:
        return _exception_response(error)


async def delete_handler(request: web.Request) -> web.Response:
    denied = _authorized(request, "edit")
    if denied:
        return denied
    try:
        body = await _json(request)
        if body.get("confirmed") is not True:
            return _error(400, "confirmation_required", "Delete requires clear user intent.")
        return web.json_response(delete_resource(body))
    except Exception as error:
        return _exception_response(error)

def register_routes() -> None:
    global _REGISTERED
    if _REGISTERED:
        return

    from server import PromptServer

    routes = PromptServer.instance.routes
    routes.get("/cuicommander/v1/openapi")(openapi_handler)
    routes.get("/cuicommander/v1/manifest")(manifest_handler)
    routes.post("/cuicommander/v1/discover")(discover_handler)
    routes.post("/cuicommander/v1/resources/inspect")(inspect_handler)
    routes.post("/cuicommander/v1/resources/create")(create_handler)
    routes.post("/cuicommander/v1/resources/update")(update_handler)
    routes.post("/cuicommander/v1/resources/move")(move_handler)
    routes.post("/cuicommander/v1/resources/delete")(delete_handler)
    _REGISTERED = True

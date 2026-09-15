from __future__ import annotations

import json
from typing import Any

from aiohttp import web

from .audit import list_activity, record_activity
from .discovery import discover
from .downloads import start_download
from .jobs import cancel_job, get_job, list_jobs, restore_jobs
from .local_admin import (
    is_local_admin_request,
    local_setup_payload,
    rotate_local_access_key,
    update_local_setup,
)
from .openapi import build_schema
from .resources import (
    create_resource,
    delete_resource,
    inspect_resource,
    move_resource,
    patch_resource,
    read_resource,
    update_resource,
)
from .roots import discover_roots
from .runtime import execute_native, read_runtime_response
from .security import access_level, has_access, is_authorized, public_connection_info
from .ui import register_ui_routes
from .version import VERSION

_REGISTERED = False


def _comfyui_version() -> str:
    try:
        import comfyui_version

        return str(comfyui_version.__version__)
    except (ImportError, AttributeError):
        return "unknown"


def _error(status: int, code: str, message: str) -> web.Response:
    return web.json_response({"error": code, "message": message}, status=status)


def _exception_response(error: Exception) -> web.Response:
    if isinstance(error, (FileNotFoundError, KeyError)):
        return _error(404, "not_found", str(error))
    if isinstance(error, FileExistsError):
        return _error(409, "already_exists", str(error))
    if isinstance(error, PermissionError):
        return _error(403, "forbidden", str(error))
    if isinstance(error, RuntimeError):
        return _error(409, "operation_conflict", str(error))
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


def _local_admin_denied(request: web.Request) -> web.Response | None:
    if is_local_admin_request(request):
        return None
    return _error(403, "local_only", "Local setup is available only from the loopback ComfyUI origin.")


def _no_store_json(value: Any, status: int = 200) -> web.Response:
    response = web.json_response(value, status=status)
    response.headers["Cache-Control"] = "no-store"
    return response


async def openapi_handler(request: web.Request) -> web.Response:
    server_url = f"{request.scheme}://{request.host}"
    return web.json_response(build_schema(server_url, VERSION))


async def manifest_handler(request: web.Request) -> web.Response:
    denied = _authorized(request)
    if denied:
        return denied
    return web.json_response(
        {
            "version": VERSION,
            "comfyVersion": _comfyui_version(),
            "accessLevel": access_level(),
            "schemaUrl": f"{request.scheme}://{request.host}/cuicommander/v1/openapi",
            "uiUrl": f"{request.scheme}://{request.host}/cuicommander/",
            "connection": public_connection_info(),
            "rootCount": len(discover_roots()),
            "machineModel": "Discover/Inspect -> Create/Read/Update/Delete -> Execute",
            "noAdapterInvariant": True,
            "capabilities": {
                "filesystemCrud": True,
                "chunkedResourceIo": True,
                "backgroundDownloads": True,
                "nativeRouteExecution": True,
                "chunkedNativeResponses": True,
            },
        }
    )


async def local_setup_handler(request: web.Request) -> web.Response:
    denied = _local_admin_denied(request)
    if denied:
        return denied
    try:
        return _no_store_json(local_setup_payload(request))
    except Exception as error:
        return _exception_response(error)


async def local_setup_update_handler(request: web.Request) -> web.Response:
    denied = _local_admin_denied(request)
    if denied:
        return denied
    try:
        result = update_local_setup(request, await _json(request))
        record_activity("setup.update", {"accessLevel": result.get("accessLevel")})
        return _no_store_json(result)
    except Exception as error:
        return _exception_response(error)


async def local_rotate_handler(request: web.Request) -> web.Response:
    denied = _local_admin_denied(request)
    if denied:
        return denied
    try:
        body = await _json(request)
        result = rotate_local_access_key(request, body.get("confirmed") is True)
        record_activity("credential.rotate")
        return _no_store_json(result)
    except Exception as error:
        return _exception_response(error)


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
            int(body.get("offset", 0)),
        )
        return web.json_response(result)
    except Exception as error:
        return _exception_response(error)


async def inspect_handler(request: web.Request) -> web.Response:
    denied = _authorized(request)
    if denied:
        return denied
    try:
        body = await _json(request)
        return web.json_response(
            inspect_resource(
                str(body.get("root", "")),
                str(body.get("path", "")),
                offset=int(body.get("offset", 0)),
                limit=int(body.get("limit", 250)),
                expected_fingerprint=body.get("expectedFingerprint"),
            )
        )
    except Exception as error:
        return _exception_response(error)


async def read_handler(request: web.Request) -> web.Response:
    denied = _authorized(request)
    if denied:
        return denied
    try:
        return web.json_response(read_resource(await _json(request)))
    except Exception as error:
        return _exception_response(error)


async def patch_handler(request: web.Request) -> web.Response:
    denied = _authorized(request, "edit")
    if denied:
        return denied
    try:
        body = await _json(request)
        result = patch_resource(body)
        record_activity(
            "resource.patch",
            {
                "root": body.get("root"),
                "path": body.get("path"),
                "offset": body.get("offset", 0),
                "deleteBytes": body.get("deleteBytes", 0),
            },
        )
        return web.json_response(result)
    except Exception as error:
        return _exception_response(error)


async def create_handler(request: web.Request) -> web.Response:
    denied = _authorized(request, "edit")
    if denied:
        return denied
    try:
        body = await _json(request)
        result = create_resource(body)
        record_activity("resource.create", body)
        return web.json_response(result)
    except Exception as error:
        return _exception_response(error)


async def update_handler(request: web.Request) -> web.Response:
    denied = _authorized(request, "edit")
    if denied:
        return denied
    try:
        body = await _json(request)
        result = update_resource(body)
        record_activity("resource.update", body)
        return web.json_response(result)
    except Exception as error:
        return _exception_response(error)


async def move_handler(request: web.Request) -> web.Response:
    denied = _authorized(request, "edit")
    if denied:
        return denied
    try:
        body = await _json(request)
        result = move_resource(body)
        record_activity("resource.move", body)
        return web.json_response(result)
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
        result = delete_resource(body)
        record_activity("resource.delete", body)
        return web.json_response(result)
    except Exception as error:
        return _exception_response(error)


async def download_handler(request: web.Request) -> web.Response:
    denied = _authorized(request, "edit")
    if denied:
        return denied
    try:
        body = await _json(request)
        result = start_download(body)
        record_activity("download.start", {**body, "jobId": result.get("id")})
        return web.json_response(result, status=202)
    except Exception as error:
        return _exception_response(error)


async def jobs_handler(request: web.Request) -> web.Response:
    denied = _authorized(request)
    if denied:
        return denied
    try:
        limit = int(request.rel_url.query.get("limit", 50))
        return web.json_response({"items": list_jobs(limit)})
    except Exception as error:
        return _exception_response(error)


async def activity_handler(request: web.Request) -> web.Response:
    denied = _authorized(request)
    if denied:
        return denied
    try:
        limit = int(request.rel_url.query.get("limit", 100))
        return web.json_response({"items": list_activity(limit)})
    except Exception as error:
        return _exception_response(error)


async def job_handler(request: web.Request) -> web.Response:
    denied = _authorized(request)
    if denied:
        return denied
    try:
        return web.json_response(get_job(str(request.match_info.get("job_id", ""))))
    except Exception as error:
        return _exception_response(error)


async def cancel_job_handler(request: web.Request) -> web.Response:
    denied = _authorized(request, "edit")
    if denied:
        return denied
    try:
        body = await _json(request)
        if body.get("confirmed") is not True:
            return _error(400, "confirmation_required", "Cancelling a job requires clear user intent.")
        job_id = str(request.match_info.get("job_id", ""))
        result = cancel_job(job_id)
        record_activity("job.cancel", {"jobId": job_id, "status": result.get("status")})
        return web.json_response(result)
    except Exception as error:
        return _exception_response(error)


async def runtime_response_handler(request: web.Request) -> web.Response:
    denied = _authorized(request, "full")
    if denied:
        return denied
    try:
        return web.json_response(read_runtime_response(await _json(request)))
    except Exception as error:
        return _exception_response(error)


async def execute_handler(request: web.Request) -> web.Response:
    denied = _authorized(request, "full")
    if denied:
        return denied
    try:
        body = await _json(request)
        result = await execute_native(body)
        record_activity("runtime.execute", {**body, "status": result.get("status")})
        return web.json_response(result)
    except Exception as error:
        return _exception_response(error)


def register_routes() -> None:
    global _REGISTERED
    if _REGISTERED:
        return

    from server import PromptServer

    restore_jobs()
    routes = PromptServer.instance.routes
    routes.get("/cuicommander/v1/openapi")(openapi_handler)
    routes.get("/cuicommander/v1/manifest")(manifest_handler)
    routes.get("/cuicommander/v1/local/setup")(local_setup_handler)
    routes.post("/cuicommander/v1/local/setup")(local_setup_update_handler)
    routes.post("/cuicommander/v1/local/credential/rotate")(local_rotate_handler)
    routes.post("/cuicommander/v1/discover")(discover_handler)
    routes.post("/cuicommander/v1/resources/inspect")(inspect_handler)
    routes.post("/cuicommander/v1/resources/read")(read_handler)
    routes.post("/cuicommander/v1/resources/patch")(patch_handler)
    routes.post("/cuicommander/v1/resources/create")(create_handler)
    routes.post("/cuicommander/v1/resources/update")(update_handler)
    routes.post("/cuicommander/v1/resources/move")(move_handler)
    routes.post("/cuicommander/v1/resources/delete")(delete_handler)
    routes.post("/cuicommander/v1/downloads")(download_handler)
    routes.get("/cuicommander/v1/jobs")(jobs_handler)
    routes.get("/cuicommander/v1/activity")(activity_handler)
    routes.get("/cuicommander/v1/jobs/{job_id}")(job_handler)
    routes.post("/cuicommander/v1/jobs/{job_id}/cancel")(cancel_job_handler)
    routes.post("/cuicommander/v1/execute")(execute_handler)
    routes.post("/cuicommander/v1/runtime/responses/read")(runtime_response_handler)
    register_ui_routes(routes)
    _REGISTERED = True

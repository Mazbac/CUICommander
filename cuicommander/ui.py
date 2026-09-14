from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from aiohttp import web

UI_ROOT = Path(__file__).resolve().parents[1] / "web" / "console"
ASSET_ROOT = UI_ROOT / "assets"


def _inside(base: Path, candidate: Path) -> bool:
    try:
        return os.path.commonpath([str(base), str(candidate)]) == str(base)
    except ValueError:
        return False


async def ui_index_handler(_: web.Request) -> web.StreamResponse:
    index = UI_ROOT / "index.html"
    if not index.is_file():
        return web.Response(
            status=503,
            text="CUICommander UI build is missing. Run npm run build in the CUICommander package.",
            content_type="text/plain",
        )
    response = web.FileResponse(index)
    response.headers["Cache-Control"] = "no-cache"
    return response


async def ui_asset_handler(request: web.Request) -> web.StreamResponse:
    relative = str(request.match_info.get("asset", "")).replace("\\", "/")
    if not relative or relative.startswith("/"):
        raise web.HTTPNotFound()
    base = ASSET_ROOT.resolve()
    candidate = (ASSET_ROOT / relative).resolve()
    if not _inside(base, candidate) or not candidate.is_file():
        raise web.HTTPNotFound()
    response = web.FileResponse(candidate)
    response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    return response


def register_ui_routes(routes: Any) -> None:
    routes.get("/cuicommander")(ui_index_handler)
    routes.get("/cuicommander/")(ui_index_handler)
    routes.get("/cuicommander/assets/{asset:.*}")(ui_asset_handler)

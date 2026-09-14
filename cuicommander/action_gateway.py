from __future__ import annotations

import json
from typing import Any

from .openapi import build_schema
from .runtime import _native_origin

MAX_PROXY_RESPONSE_BYTES = 4 * 1024 * 1024
_FORWARDED_REQUEST_HEADERS = {"authorization", "accept", "content-type"}


class ActionGateway:
    def __init__(self) -> None:
        self._runner: Any = None
        self._site: Any = None
        self._port: int | None = None
        self._public_origin = ""
        self._version = ""

    @property
    def running(self) -> bool:
        return self._runner is not None

    @property
    def port(self) -> int | None:
        return self._port

    async def start(self, public_origin: str, port: int, version: str) -> None:
        from aiohttp import web

        normalized_origin = public_origin.rstrip("/")
        if self.running:
            if self._port == port and self._public_origin == normalized_origin:
                return
            raise RuntimeError("Action gateway is already running with different settings.")
        if not 1024 <= int(port) <= 65535:
            raise ValueError("Gateway port must be between 1024 and 65535.")

        app = web.Application(client_max_size=4 * 1024 * 1024)
        app.router.add_get("/cuicommander/v1/openapi", self._schema)
        schema = build_schema(normalized_origin, version)
        for path, operations in schema["paths"].items():
            for method in operations:
                app.router.add_route(method.upper(), path, self._proxy)

        runner = web.AppRunner(app, access_log=None)
        await runner.setup()
        site = web.TCPSite(runner, "127.0.0.1", int(port))
        try:
            await site.start()
        except Exception:
            await runner.cleanup()
            raise

        self._runner = runner
        self._site = site
        self._port = int(port)
        self._public_origin = normalized_origin
        self._version = version

    async def stop(self) -> None:
        if self._runner is None:
            self._site = None
            self._port = None
            self._public_origin = ""
            self._version = ""
            return
        runner = self._runner
        self._runner = None
        self._site = None
        self._port = None
        self._public_origin = ""
        self._version = ""
        await runner.cleanup()

    async def _schema(self, request: Any) -> Any:
        from aiohttp import web

        return web.json_response(build_schema(self._public_origin, self._version))

    def _rewrite_public_payload(
        self,
        path: str,
        raw: bytes,
        content_type: str,
    ) -> tuple[bytes, str]:
        if "json" not in content_type.lower():
            return raw, content_type
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return raw, content_type
        if not isinstance(payload, dict):
            return raw, content_type

        if path == "/cuicommander/v1/openapi":
            payload["servers"] = [{"url": self._public_origin}]
        elif path == "/cuicommander/v1/manifest":
            payload["schemaUrl"] = (
                f"{self._public_origin}/cuicommander/v1/openapi"
            )
            connection = payload.get("connection")
            if isinstance(connection, dict):
                connection["publicBaseUrl"] = self._public_origin
        return (
            json.dumps(payload, separators=(",", ":")).encode("utf-8"),
            "application/json; charset=utf-8",
        )

    async def _proxy(self, request: Any) -> Any:
        from aiohttp import ClientSession, ClientTimeout, web

        origin, tls = _native_origin()
        target = f"{origin}{request.rel_url.path_qs}"
        headers = {
            name: value
            for name, value in request.headers.items()
            if name.lower() in _FORWARDED_REQUEST_HEADERS
        }
        body = await request.read()
        timeout = ClientTimeout(total=125, connect=10, sock_read=120)
        async with ClientSession(timeout=timeout) as session:
            async with session.request(
                request.method,
                target,
                headers=headers,
                data=body or None,
                ssl=False if tls else None,
                allow_redirects=False,
            ) as response:
                raw = await response.content.read(MAX_PROXY_RESPONSE_BYTES + 1)
                if len(raw) > MAX_PROXY_RESPONSE_BYTES:
                    return web.json_response(
                        {
                            "error": "response_too_large",
                            "message": "Action gateway response exceeded the safety limit.",
                        },
                        status=502,
                    )
                content_type = response.headers.get(
                    "Content-Type", "application/octet-stream"
                )
                raw, content_type = self._rewrite_public_payload(
                    request.path, raw, content_type
                )
                return web.Response(
                    body=raw,
                    status=response.status,
                    headers={"Content-Type": content_type},
                )


GATEWAY = ActionGateway()

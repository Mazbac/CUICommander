from __future__ import annotations

import asyncio
import json
import os
import shutil
import socket
import subprocess
from pathlib import Path
from typing import Any

from .action_gateway import GATEWAY
from .local_admin import is_local_admin_request
from .security import internal_state_directory, public_base_url, set_public_base_url

_ALLOWED_FUNNEL_PORTS = (443, 8443, 10000)
_GATEWAY_PORTS = tuple(range(8766, 8800))
_REGISTERED = False
_LAST_ERROR = ""


def _state_path() -> Path:
    return internal_state_directory() / "remote.json"


def _load_state() -> dict[str, Any]:
    path = _state_path()
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def _write_state(value: dict[str, Any]) -> None:
    path = _state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    try:
        os.chmod(temp, 0o600)
    except OSError:
        pass
    os.replace(temp, path)


def _tailscale_executable() -> str | None:
    found = shutil.which("tailscale")
    if found:
        return found
    if os.name == "nt":
        candidate = Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Tailscale" / "tailscale.exe"
        if candidate.exists():
            return str(candidate)
    return None


def _run_tailscale(arguments: list[str], timeout: int = 20) -> subprocess.CompletedProcess[str]:
    executable = _tailscale_executable()
    if not executable:
        raise FileNotFoundError("Tailscale is not installed.")
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    return subprocess.run(
        [executable, *arguments],
        capture_output=True,
        text=True,
        timeout=timeout,
        creationflags=flags,
        check=False,
    )


def _json_command(arguments: list[str]) -> dict[str, Any]:
    result = _run_tailscale(arguments)
    if result.returncode != 0:
        message = (result.stderr or result.stdout or "Tailscale command failed.").strip()
        raise RuntimeError(message[:1000])
    try:
        value = json.loads(result.stdout)
    except ValueError as error:
        raise RuntimeError("Tailscale returned invalid JSON.") from error
    if not isinstance(value, dict):
        raise RuntimeError("Tailscale returned an unexpected response.")
    return value


def _tailscale_snapshot() -> dict[str, Any]:
    executable = _tailscale_executable()
    if not executable:
        return {
            "installed": False,
            "version": "",
            "connected": False,
            "dnsName": "",
            "funnel": {},
        }
    version_result = _run_tailscale(["version"])
    version = (version_result.stdout.splitlines() or [""])[0].strip()
    status = _json_command(["status", "--json"])
    funnel = _json_command(["funnel", "status", "--json"])
    self_state = status.get("Self") if isinstance(status.get("Self"), dict) else {}
    dns_name = str(self_state.get("DNSName", "")).rstrip(".")
    connected = (
        status.get("BackendState") == "Running"
        and bool(dns_name)
        and self_state.get("Online") is not False
    )
    return {
        "installed": True,
        "version": version,
        "connected": connected,
        "dnsName": dns_name,
        "funnel": funnel,
    }


def _occupied_funnel_ports(config: dict[str, Any]) -> set[int]:
    occupied: set[int] = set()
    tcp = config.get("TCP")
    if isinstance(tcp, dict):
        for value in tcp:
            try:
                occupied.add(int(value))
            except (TypeError, ValueError):
                continue

    for section_name in ("Web", "AllowFunnel"):
        section = config.get(section_name)
        if not isinstance(section, dict):
            continue
        for endpoint in section:
            try:
                occupied.add(int(str(endpoint).rsplit(":", 1)[1]))
            except (IndexError, ValueError):
                continue
    return occupied


def _choose_funnel_port(config: dict[str, Any]) -> int:
    occupied = _occupied_funnel_ports(config)
    for port in _ALLOWED_FUNNEL_PORTS:
        if port not in occupied:
            return port
    raise RuntimeError("All Tailscale Funnel HTTPS ports are already in use.")


def _port_available(port: int) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", int(port)))
        return True
    except OSError:
        return False
    finally:
        sock.close()


def _choose_gateway_port() -> int:
    for port in _GATEWAY_PORTS:
        if _port_available(port):
            return port
    raise RuntimeError("No free local CUICommander gateway port was found.")


def _public_origin(dns_name: str, port: int) -> str:
    if not dns_name:
        raise RuntimeError("Tailscale did not report a MagicDNS hostname.")
    suffix = "" if int(port) == 443 else f":{int(port)}"
    return f"https://{dns_name}{suffix}"


def _gateway_target(port: int) -> str:
    return f"http://127.0.0.1:{int(port)}"


def _funnel_matches(
    config: dict[str, Any],
    dns_name: str,
    port: int,
    target: str,
) -> bool:
    key = f"{dns_name}:{int(port)}"
    web_config = config.get("Web")
    allow_funnel = config.get("AllowFunnel")
    if not isinstance(web_config, dict) or not isinstance(allow_funnel, dict):
        return False
    web_entry = web_config.get(key)
    if not isinstance(web_entry, dict) or allow_funnel.get(key) is not True:
        return False
    handlers = web_entry.get("Handlers")
    if not isinstance(handlers, dict):
        return False
    root_handler = handlers.get("/")
    return isinstance(root_handler, dict) and root_handler.get("Proxy") == target


def _status_payload() -> dict[str, Any]:
    global _LAST_ERROR
    state = _load_state()
    try:
        snapshot = _tailscale_snapshot()
        config = snapshot.get("funnel") if isinstance(snapshot.get("funnel"), dict) else {}
        occupied = sorted(_occupied_funnel_ports(config))
        suggested: int | None = None
        try:
            suggested = _choose_funnel_port(config)
        except RuntimeError:
            pass
        enabled = state.get("provider") == "tailscale" and state.get("enabled") is True
        gateway_port = int(state.get("gatewayPort", 0) or 0)
        funnel_port = int(state.get("funnelPort", 0) or 0)
        origin = str(state.get("publicBaseUrl", ""))
        target = _gateway_target(gateway_port) if gateway_port else ""
        matched = bool(
            enabled
            and snapshot["connected"]
            and funnel_port
            and target
            and _funnel_matches(config, snapshot["dnsName"], funnel_port, target)
        )
        if enabled and funnel_port in _ALLOWED_FUNNEL_PORTS:
            saved_mapping = bool(
                target
                and _funnel_matches(config, snapshot["dnsName"], funnel_port, target)
            )
            if saved_mapping or funnel_port not in occupied:
                suggested = funnel_port
        existing_services = len(config.get("Web", {})) if isinstance(config.get("Web"), dict) else 0
        return {
            "provider": "tailscale",
            "installed": snapshot["installed"],
            "version": snapshot["version"],
            "connected": snapshot["connected"],
            "dnsName": snapshot["dnsName"],
            "existingServices": existing_services,
            "occupiedFunnelPorts": occupied,
            "recommendedFunnelPort": suggested,
            "configured": enabled,
            "active": matched and GATEWAY.running,
            "gatewayRunning": GATEWAY.running,
            "gatewayPort": gateway_port or None,
            "funnelPort": funnel_port or None,
            "publicBaseUrl": origin,
            "lastError": _LAST_ERROR,
        }
    except Exception as error:
        _LAST_ERROR = str(error)
        return {
            "provider": "tailscale",
            "installed": _tailscale_executable() is not None,
            "version": "",
            "connected": False,
            "dnsName": "",
            "existingServices": 0,
            "occupiedFunnelPorts": [],
            "recommendedFunnelPort": None,
            "configured": state.get("enabled") is True,
            "active": False,
            "gatewayRunning": GATEWAY.running,
            "gatewayPort": state.get("gatewayPort"),
            "funnelPort": state.get("funnelPort"),
            "publicBaseUrl": str(state.get("publicBaseUrl", "")),
            "lastError": _LAST_ERROR,
        }


async def _verify_public_gateway(origin: str) -> None:
    from aiohttp import ClientSession, ClientTimeout

    timeout = ClientTimeout(total=12, connect=5, sock_read=8)
    last_error = "Public gateway did not become reachable."
    for attempt in range(8):
        try:
            async with ClientSession(timeout=timeout) as session:
                async with session.get(f"{origin}/cuicommander/v1/openapi") as response:
                    if response.status != 200:
                        raise RuntimeError(f"OpenAPI verification returned HTTP {response.status}.")
                    payload = await response.json()
                    if payload.get("servers") != [{"url": origin}]:
                        raise RuntimeError("Public OpenAPI server URL did not match the Funnel origin.")
                async with session.get(f"{origin}/system_stats") as response:
                    if response.status != 404:
                        raise RuntimeError("Raw ComfyUI routes are reachable through the public gateway.")
                async with session.get(f"{origin}/cuicommander/v1/local/setup") as response:
                    if response.status != 404:
                        raise RuntimeError("Local CUICommander administration is reachable publicly.")
            return
        except Exception as error:
            last_error = str(error)
            if attempt < 7:
                await asyncio.sleep(1.0)
    raise RuntimeError(last_error)


def _command_error(result: subprocess.CompletedProcess[str]) -> RuntimeError:
    message = (result.stderr or result.stdout or "Tailscale command failed.").strip()
    return RuntimeError(message[:1000])


async def enable_tailscale_remote_access() -> dict[str, Any]:
    global _LAST_ERROR
    snapshot = await asyncio.to_thread(_tailscale_snapshot)
    if not snapshot["installed"]:
        raise FileNotFoundError("Tailscale is not installed.")
    if not snapshot["connected"]:
        raise RuntimeError("Tailscale is installed but this PC is not connected to a tailnet.")

    config = snapshot["funnel"]
    state = _load_state()
    previous_state = dict(state)
    previous_public_url = public_base_url()
    gateway_port = int(state.get("gatewayPort", 0) or 0)
    if not gateway_port:
        gateway_port = _choose_gateway_port()
    elif not GATEWAY.running and not _port_available(gateway_port):
        raise RuntimeError("The saved CUICommander gateway port is now used by another process.")

    funnel_port = int(state.get("funnelPort", 0) or 0)
    target = _gateway_target(gateway_port)
    if funnel_port and funnel_port in _occupied_funnel_ports(config):
        if not _funnel_matches(config, snapshot["dnsName"], funnel_port, target):
            raise RuntimeError("The saved Tailscale Funnel port is now owned by another service.")
    if not funnel_port:
        funnel_port = _choose_funnel_port(config)
    origin = _public_origin(snapshot["dnsName"], funnel_port)
    existing_match = _funnel_matches(config, snapshot["dnsName"], funnel_port, target)
    owns_existing = bool(state.get("ownsFunnel")) and existing_match
    from .version import VERSION

    await GATEWAY.start(origin, gateway_port, VERSION)
    created_funnel = False
    try:
        if not existing_match:
            result = await asyncio.to_thread(
                _run_tailscale,
                ["funnel", "--bg", "--yes", f"--https={funnel_port}", target],
                30,
            )
            if result.returncode != 0:
                raise _command_error(result)
            created_funnel = True

        refreshed = await asyncio.to_thread(_tailscale_snapshot)
        if not _funnel_matches(refreshed["funnel"], refreshed["dnsName"], funnel_port, target):
            raise RuntimeError("Tailscale did not keep the requested CUICommander Funnel mapping.")
        await _verify_public_gateway(origin)

        next_state = {
            "provider": "tailscale",
            "enabled": True,
            "gatewayPort": gateway_port,
            "funnelPort": funnel_port,
            "publicBaseUrl": origin,
            "previousPublicBaseUrl": (
                previous_public_url if previous_public_url != origin else ""
            ),
            "ownsFunnel": created_funnel or owns_existing,
        }
        set_public_base_url(origin)
        try:
            _write_state(next_state)
        except Exception:
            try:
                set_public_base_url(previous_public_url)
            except Exception:
                pass
            try:
                _write_state(previous_state)
            except Exception:
                pass
            raise
    except Exception:
        if created_funnel:
            try:
                await asyncio.to_thread(
                    _run_tailscale,
                    ["funnel", "--yes", f"--https={funnel_port}", "off"],
                    20,
                )
            except Exception:
                pass
        await GATEWAY.stop()
        raise

    _LAST_ERROR = ""
    return await asyncio.to_thread(_status_payload)


async def disable_tailscale_remote_access() -> dict[str, Any]:
    global _LAST_ERROR
    state = _load_state()
    if state.get("provider") != "tailscale" or state.get("enabled") is not True:
        await GATEWAY.stop()
        return await asyncio.to_thread(_status_payload)

    gateway_port = int(state.get("gatewayPort", 0) or 0)
    funnel_port = int(state.get("funnelPort", 0) or 0)
    origin = str(state.get("publicBaseUrl", ""))
    previous_public_url = str(state.get("previousPublicBaseUrl", ""))
    owns_funnel = bool(state.get("ownsFunnel"))
    snapshot = await asyncio.to_thread(_tailscale_snapshot)
    target = _gateway_target(gateway_port) if gateway_port else ""
    if (
        owns_funnel
        and funnel_port
        and _funnel_matches(snapshot["funnel"], snapshot["dnsName"], funnel_port, target)
    ):
        result = await asyncio.to_thread(
            _run_tailscale,
            ["funnel", "--yes", f"--https={funnel_port}", "off"],
            20,
        )
        if result.returncode != 0:
            raise _command_error(result)

    await GATEWAY.stop()

    if origin and public_base_url() == origin:
        set_public_base_url(previous_public_url)

    _write_state(
        {
            "provider": "tailscale",
            "enabled": False,
            "gatewayPort": gateway_port,
            "funnelPort": funnel_port,
            "publicBaseUrl": "",
            "previousPublicBaseUrl": "",
            "ownsFunnel": False,
        }
    )
    _LAST_ERROR = ""
    return await asyncio.to_thread(_status_payload)


def _local_denied(request: Any) -> Any:
    from aiohttp import web

    if is_local_admin_request(request):
        return None
    return web.json_response(
        {"error": "local_only", "message": "Remote setup is loopback-only."},
        status=403,
    )


def _no_store(value: Any, status: int = 200) -> Any:
    from aiohttp import web
    response = web.json_response(value, status=status)
    response.headers["Cache-Control"] = "no-store"
    return response


async def _confirmation_error(request: Any, action: str) -> Any:
    try:
        body = await request.json()
    except Exception:
        body = None
    if not isinstance(body, dict) or body.get("confirmed") is not True:
        return _no_store(
            {
                "error": "confirmation_required",
                "message": f"{action} requires confirmed=true.",
            },
            status=400,
        )
    return None


async def remote_status_handler(request: Any) -> Any:
    denied = _local_denied(request)
    if denied:
        return denied
    return _no_store(await asyncio.to_thread(_status_payload))


async def remote_enable_handler(request: Any) -> Any:
    denied = _local_denied(request)
    if denied:
        return denied
    confirmation = await _confirmation_error(request, "Enabling public remote access")
    if confirmation:
        return confirmation
    try:
        result = await enable_tailscale_remote_access()
        return _no_store(result)
    except Exception as error:
        return _no_store(
            {"error": "remote_access_failed", "message": str(error)},
            status=409,
        )


async def remote_disable_handler(request: Any) -> Any:
    denied = _local_denied(request)
    if denied:
        return denied
    confirmation = await _confirmation_error(request, "Disabling public remote access")
    if confirmation:
        return confirmation
    try:
        result = await disable_tailscale_remote_access()
        return _no_store(result)
    except Exception as error:
        return _no_store(
            {"error": "remote_access_failed", "message": str(error)},
            status=409,
        )


async def _startup_remote_access(app: Any) -> None:
    global _LAST_ERROR
    state = _load_state()
    if state.get("provider") != "tailscale" or state.get("enabled") is not True:
        return
    try:
        gateway_port = int(state["gatewayPort"])
        origin = str(state["publicBaseUrl"])
        from .version import VERSION

        await GATEWAY.start(origin, gateway_port, VERSION)
        _LAST_ERROR = ""
    except Exception as error:
        _LAST_ERROR = str(error)


async def _cleanup_remote_access(app: Any) -> None:
    await GATEWAY.stop()


def register_remote_access() -> None:
    global _REGISTERED
    if _REGISTERED:
        return

    from server import PromptServer

    routes = PromptServer.instance.routes
    routes.get("/cuicommander/v1/local/remote")(remote_status_handler)
    routes.post("/cuicommander/v1/local/remote/tailscale/enable")(remote_enable_handler)
    routes.post("/cuicommander/v1/local/remote/tailscale/disable")(remote_disable_handler)
    PromptServer.instance.app.on_startup.append(_startup_remote_access)
    PromptServer.instance.app.on_cleanup.append(_cleanup_remote_access)
    _REGISTERED = True

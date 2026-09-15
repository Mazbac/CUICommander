from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
import socket
import subprocess
import time
from pathlib import Path
from typing import Any

from .action_gateway import GATEWAY
from .audit import record_activity
from .local_admin import is_local_admin_request
from .security import internal_state_directory, public_base_url, set_public_base_url

_ALLOWED_FUNNEL_PORTS = (443, 8443, 10000)
_GATEWAY_PORTS = tuple(range(8766, 8800))
_ACTION_NODE_SOCKET = r"\\.\pipe\ProtectedPrefix\Administrators\Tailscale\CUICommanderAction"
_ACTION_NODE_TASK_NAME = "CUICommander Action Tailscale"
_REGISTERED = False
_LAST_ERROR = ""
_ACTION_NODE_LOGIN_URL = ""


def _state_path() -> Path:
    return internal_state_directory() / "remote.json"


def _load_state() -> dict[str, Any]:
    path = _state_path()
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
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


def _run_tailscale(
    arguments: list[str],
    timeout: int = 20,
    socket_path: str | None = None,
) -> subprocess.CompletedProcess[str]:
    executable = _tailscale_executable()
    if not executable:
        raise FileNotFoundError("Tailscale is not installed.")
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    command = [executable]
    if socket_path:
        command.append(f"--socket={socket_path}")
    command.extend(arguments)
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout,
        creationflags=flags,
        check=False,
    )


def _json_command(
    arguments: list[str], socket_path: str | None = None
) -> dict[str, Any]:
    result = _run_tailscale(arguments, socket_path=socket_path)
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


def _tailscale_snapshot(socket_path: str | None = None) -> dict[str, Any]:
    executable = _tailscale_executable()
    if not executable:
        return {
            "installed": False,
            "version": "",
            "connected": False,
            "dnsName": "",
            "funnel": {},
        }
    version_result = _run_tailscale(["version"], socket_path=socket_path)
    version = (version_result.stdout.splitlines() or [""])[0].strip()
    status = _json_command(["status", "--json"], socket_path=socket_path)
    funnel = _json_command(["funnel", "status", "--json"], socket_path=socket_path)
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




def _state_socket(state: dict[str, Any]) -> str | None:
    if state.get("mode") == "action-node":
        return _ACTION_NODE_SOCKET
    return None


def _tailscaled_executable() -> str | None:
    cli = _tailscale_executable()
    if not cli:
        return None
    candidate = Path(cli).with_name("tailscaled.exe" if os.name == "nt" else "tailscaled")
    return str(candidate) if candidate.exists() else None


def _action_node_supported() -> bool:
    return os.name == "nt" and _tailscaled_executable() is not None


def _action_node_state_dir() -> Path:
    return internal_state_directory() / "tailscale-action-node"


def _action_node_hostname() -> str:
    base = re.sub(r"[^a-z0-9-]+", "-", socket.gethostname().lower()).strip("-")
    if not base:
        base = "host"
    return f"cuicommander-{base}"[:63].rstrip("-")


def _try_action_node_snapshot() -> dict[str, Any] | None:
    if not _action_node_supported():
        return None
    try:
        return _tailscale_snapshot(_ACTION_NODE_SOCKET)
    except Exception:
        return None


def _action_node_summary() -> dict[str, Any]:
    snapshot = _try_action_node_snapshot()
    if snapshot is None:
        return {
            "supported": _action_node_supported(),
            "running": False,
            "connected": False,
            "dnsName": "",
        }
    return {
        "supported": True,
        "running": True,
        "connected": bool(snapshot.get("connected")),
        "dnsName": str(snapshot.get("dnsName", "")),
    }


def _powershell_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _action_node_task_exists() -> bool:
    if os.name != "nt":
        return False
    result = subprocess.run(
        ["schtasks.exe", "/Query", "/TN", _ACTION_NODE_TASK_NAME],
        capture_output=True,
        text=True,
        timeout=10,
        creationflags=subprocess.CREATE_NO_WINDOW,
        check=False,
    )
    return result.returncode == 0


def _write_action_node_task_script() -> Path:
    tailscaled = _tailscaled_executable()
    if not tailscaled:
        raise FileNotFoundError("Tailscale daemon executable was not found.")
    state_dir = _action_node_state_dir()
    state_dir.mkdir(parents=True, exist_ok=True)
    script_path = state_dir / "install-action-node-task.ps1"
    state_file = state_dir / "tailscaled.state"
    lines = [
        '$ErrorActionPreference = "Stop"',
        f'$taskName = {_powershell_literal(_ACTION_NODE_TASK_NAME)}',
        f'$tailscaled = {_powershell_literal(tailscaled)}',
        f'$stateDir = {_powershell_literal(str(state_dir))}',
        f'$stateFile = {_powershell_literal(str(state_file))}',
        f'$socketPath = {_powershell_literal(_ACTION_NODE_SOCKET)}',
        '$userId = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name',
        "$argumentLine = '--tun=userspace-networking --port=0 --socket=\"' + $socketPath + '\" --statedir=\"' + $stateDir + '\" --state=\"' + $stateFile + '\" --no-logs-no-support'",
        '$action = New-ScheduledTaskAction -Execute $tailscaled -Argument $argumentLine',
        '$trigger = New-ScheduledTaskTrigger -AtLogOn -User $userId',
        '$principal = New-ScheduledTaskPrincipal -UserId $userId -LogonType Interactive -RunLevel Highest',
        '$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 10 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero)',
        'Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force | Out-Null',
        "$existing = Get-CimInstance Win32_Process -Filter \"Name='tailscaled.exe'\" | Where-Object { $_.CommandLine -and $_.CommandLine.Contains($stateDir) }",
        'if (-not $existing) { Start-ScheduledTask -TaskName $taskName }',
    ]
    script_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return script_path


def _install_action_node_task() -> None:
    if not _action_node_supported():
        raise RuntimeError("An isolated Tailscale Action node is currently supported on Windows only.")
    if _action_node_task_exists():
        return
    script_path = _write_action_node_task_script()
    powershell = shutil.which("powershell.exe") or shutil.which("powershell")
    if not powershell:
        raise RuntimeError("Windows PowerShell was not found.")
    command = (
        "$ErrorActionPreference='Stop'; "
        "$p=Start-Process -FilePath 'powershell.exe' "
        "-ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',"
        f"{_powershell_literal(str(script_path))}) -Verb RunAs -Wait -PassThru; "
        "exit $p.ExitCode"
    )
    result = subprocess.run(
        [powershell, "-NoProfile", "-NonInteractive", "-Command", command],
        capture_output=True,
        text=True,
        timeout=120,
        creationflags=subprocess.CREATE_NO_WINDOW,
        check=False,
    )
    if result.returncode != 0:
        message = (result.stderr or result.stdout or "Administrator approval was cancelled or failed.").strip()
        raise RuntimeError(message[:1000])


def _start_action_node_task() -> None:
    if os.name != "nt" or not _action_node_task_exists():
        return
    subprocess.run(
        ["schtasks.exe", "/Run", "/TN", _ACTION_NODE_TASK_NAME],
        capture_output=True,
        text=True,
        timeout=10,
        creationflags=subprocess.CREATE_NO_WINDOW,
        check=False,
    )


def _wait_for_action_node(timeout_seconds: float = 12.0) -> dict[str, Any] | None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        snapshot = _try_action_node_snapshot()
        if snapshot is not None:
            return snapshot
        time.sleep(0.4)
    return None


def _begin_action_node_login() -> str:
    global _ACTION_NODE_LOGIN_URL
    result = _run_tailscale(
        [
            "login",
            f"--hostname={_action_node_hostname()}",
            "--accept-dns=false",
            "--unattended=true",
            "--timeout=5s",
        ],
        timeout=10,
        socket_path=_ACTION_NODE_SOCKET,
    )
    text = "\n".join(part for part in (result.stdout, result.stderr) if part)
    match = re.search(r"https://login\.tailscale\.com/[^\s]+", text)
    if match:
        _ACTION_NODE_LOGIN_URL = match.group(0)
        return _ACTION_NODE_LOGIN_URL
    snapshot = _try_action_node_snapshot()
    if snapshot and snapshot.get("connected"):
        _ACTION_NODE_LOGIN_URL = ""
        return ""
    message = text.strip() or "Tailscale did not return a login URL for the isolated Action node."
    raise RuntimeError(message[:1000])


def prepare_tailscale_action_node() -> dict[str, Any]:
    global _ACTION_NODE_LOGIN_URL
    _install_action_node_task()
    _start_action_node_task()
    snapshot = _wait_for_action_node()
    if snapshot is None:
        raise RuntimeError("The isolated Tailscale Action node did not start after administrator approval.")
    if snapshot.get("connected"):
        _ACTION_NODE_LOGIN_URL = ""
    else:
        _begin_action_node_login()
    return _status_payload()

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
    enabled = state.get("provider") == "tailscale" and state.get("enabled") is True
    mode = str(state.get("mode", "system"))
    gateway_port = int(state.get("gatewayPort", 0) or 0)
    funnel_port = int(state.get("funnelPort", 0) or 0)
    origin = str(state.get("publicBaseUrl", ""))
    target = _gateway_target(gateway_port) if gateway_port else ""

    try:
        system_snapshot = _tailscale_snapshot()
        system_config = (
            system_snapshot.get("funnel")
            if isinstance(system_snapshot.get("funnel"), dict)
            else {}
        )
        system_occupied = sorted(_occupied_funnel_ports(system_config))
        system_443_available = 443 not in system_occupied
        existing_services = (
            len(system_config.get("Web", {}))
            if isinstance(system_config.get("Web"), dict)
            else 0
        )
    except Exception as error:
        _LAST_ERROR = str(error)
        system_snapshot = {
            "installed": _tailscale_executable() is not None,
            "version": "",
            "connected": False,
            "dnsName": "",
            "funnel": {},
        }
        system_occupied = []
        system_443_available = False
        existing_services = 0

    action_summary = _action_node_summary()
    action_snapshot = _try_action_node_snapshot()
    action_config = (
        action_snapshot.get("funnel")
        if action_snapshot and isinstance(action_snapshot.get("funnel"), dict)
        else {}
    )
    action_443_available = bool(
        action_snapshot
        and action_snapshot.get("connected")
        and (
            443 not in _occupied_funnel_ports(action_config)
            or (
                mode == "action-node"
                and enabled
                and gateway_port
                and _funnel_matches(
                    action_config,
                    str(action_snapshot.get("dnsName", "")),
                    443,
                    target,
                )
            )
        )
    )

    active_snapshot = action_snapshot if mode == "action-node" else system_snapshot
    if active_snapshot is None:
        active_snapshot = {
            "connected": False,
            "dnsName": "",
            "funnel": {},
        }
    active_config = (
        active_snapshot.get("funnel")
        if isinstance(active_snapshot.get("funnel"), dict)
        else {}
    )
    matched = bool(
        enabled
        and active_snapshot.get("connected")
        and funnel_port
        and target
        and _funnel_matches(
            active_config,
            str(active_snapshot.get("dnsName", "")),
            funnel_port,
            target,
        )
    )
    recommended = 443 if (system_443_available or action_443_available) else None
    active = matched and GATEWAY.running
    return {
        "provider": "tailscale",
        "mode": mode,
        "installed": bool(system_snapshot.get("installed")),
        "version": str(system_snapshot.get("version", "")),
        "connected": bool(system_snapshot.get("connected")),
        "dnsName": str(system_snapshot.get("dnsName", "")),
        "existingServices": existing_services,
        "occupiedFunnelPorts": system_occupied,
        "systemPort443Available": system_443_available,
        "recommendedFunnelPort": recommended,
        "configured": enabled,
        "active": active,
        "customGptCompatible": active and funnel_port == 443,
        "gatewayRunning": GATEWAY.running,
        "gatewayPort": gateway_port or None,
        "funnelPort": funnel_port or None,
        "publicBaseUrl": origin,
        "actionNodeSupported": bool(action_summary["supported"]),
        "actionNodeRunning": bool(action_summary["running"]),
        "actionNodeConnected": bool(action_summary["connected"]),
        "actionNodeDnsName": str(action_summary["dnsName"]),
        "actionNodeLoginUrl": _ACTION_NODE_LOGIN_URL,
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
    state = _load_state()
    previous_state = dict(state)
    previous_public_url = public_base_url()

    system_snapshot = await asyncio.to_thread(_tailscale_snapshot)
    if not system_snapshot["installed"]:
        raise FileNotFoundError("Tailscale is not installed.")
    if not system_snapshot["connected"]:
        raise RuntimeError("Tailscale is installed but this PC is not connected to a tailnet.")

    enabled = state.get("provider") == "tailscale" and state.get("enabled") is True
    if enabled:
        mode = str(state.get("mode", "system"))
        socket_path = _state_socket(state)
        snapshot = await asyncio.to_thread(_tailscale_snapshot, socket_path)
        if not snapshot.get("connected"):
            if mode == "action-node":
                raise RuntimeError(
                    "The isolated Tailscale Action node is not running. Use Repair isolated endpoint first."
                )
            raise RuntimeError("The configured Tailscale node is not connected.")
        funnel_port = int(state.get("funnelPort", 0) or 443)
    else:
        system_config = (
            system_snapshot.get("funnel")
            if isinstance(system_snapshot.get("funnel"), dict)
            else {}
        )
        if 443 not in _occupied_funnel_ports(system_config):
            mode = "system"
            socket_path = None
            snapshot = system_snapshot
        else:
            action_snapshot = await asyncio.to_thread(_try_action_node_snapshot)
            action_config = (
                action_snapshot.get("funnel")
                if action_snapshot and isinstance(action_snapshot.get("funnel"), dict)
                else {}
            )
            if (
                action_snapshot
                and action_snapshot.get("connected")
                and 443 not in _occupied_funnel_ports(action_config)
            ):
                mode = "action-node"
                socket_path = _ACTION_NODE_SOCKET
                snapshot = action_snapshot
            else:
                raise RuntimeError(
                    "HTTPS 443 is already used by an existing Tailscale service. "
                    "Set up the isolated Custom GPT endpoint first; CUICommander will preserve the existing service."
                )
        funnel_port = 443

    config = snapshot.get("funnel") if isinstance(snapshot.get("funnel"), dict) else {}
    gateway_port = int(state.get("gatewayPort", 0) or 0)
    if not gateway_port:
        gateway_port = _choose_gateway_port()
    elif not GATEWAY.running and not _port_available(gateway_port):
        raise RuntimeError("The saved CUICommander gateway port is now used by another process.")

    target = _gateway_target(gateway_port)
    if funnel_port in _occupied_funnel_ports(config):
        if not _funnel_matches(config, str(snapshot.get("dnsName", "")), funnel_port, target):
            raise RuntimeError("The selected Tailscale Funnel port is owned by another service.")
    origin = _public_origin(str(snapshot.get("dnsName", "")), funnel_port)
    existing_match = _funnel_matches(
        config,
        str(snapshot.get("dnsName", "")),
        funnel_port,
        target,
    )
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
                socket_path,
            )
            if result.returncode != 0:
                raise _command_error(result)
            created_funnel = True

        refreshed = await asyncio.to_thread(_tailscale_snapshot, socket_path)
        if not _funnel_matches(
            refreshed["funnel"],
            refreshed["dnsName"],
            funnel_port,
            target,
        ):
            raise RuntimeError("Tailscale did not keep the requested CUICommander Funnel mapping.")
        await _verify_public_gateway(origin)

        next_state = {
            "provider": "tailscale",
            "mode": mode,
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
                    socket_path,
                )
            except Exception:
                pass
        await GATEWAY.stop()
        raise

    _LAST_ERROR = ""
    record_activity(
        "remote.enable",
        {
            "provider": "tailscale",
            "mode": mode,
            "funnelPort": funnel_port,
            "status": "active",
        },
    )
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
    socket_path = _state_socket(state)
    snapshot = await asyncio.to_thread(_tailscale_snapshot, socket_path)
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
            socket_path,
        )
        if result.returncode != 0:
            raise _command_error(result)

    await GATEWAY.stop()

    if origin and public_base_url() == origin:
        set_public_base_url(previous_public_url)

    _write_state(
        {
            "provider": "tailscale",
            "mode": str(state.get("mode", "system")),
            "enabled": False,
            "gatewayPort": gateway_port,
            "funnelPort": funnel_port,
            "publicBaseUrl": "",
            "previousPublicBaseUrl": "",
            "ownsFunnel": False,
        }
    )
    _LAST_ERROR = ""
    record_activity(
        "remote.disable",
        {"provider": "tailscale", "funnelPort": funnel_port, "status": "disabled"},
    )
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


async def remote_prepare_action_node_handler(request: Any) -> Any:
    denied = _local_denied(request)
    if denied:
        return denied
    confirmation = await _confirmation_error(
        request, "Setting up the isolated Tailscale Action node"
    )
    if confirmation:
        return confirmation
    try:
        result = await asyncio.to_thread(prepare_tailscale_action_node)
        return _no_store(result)
    except Exception as error:
        return _no_store(
            {"error": "action_node_setup_failed", "message": str(error)},
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
        if state.get("mode") == "action-node" and _try_action_node_snapshot() is None:
            await asyncio.to_thread(_start_action_node_task)
            await asyncio.to_thread(_wait_for_action_node, 8.0)
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
    routes.post("/cuicommander/v1/local/remote/tailscale/action-node/prepare")(
        remote_prepare_action_node_handler
    )
    routes.post("/cuicommander/v1/local/remote/tailscale/disable")(remote_disable_handler)
    PromptServer.instance.app.on_startup.append(_startup_remote_access)
    PromptServer.instance.app.on_cleanup.append(_cleanup_remote_access)
    _REGISTERED = True

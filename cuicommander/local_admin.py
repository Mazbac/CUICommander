from __future__ import annotations

import ipaddress
from typing import Any
from urllib.parse import urlsplit

from .gpt_setup import setup_profile
from .security import (
    access_level,
    custom_gpt_compatible_origin,
    environment_overrides,
    public_base_url,
    rotate_token,
    set_access_level,
    set_public_base_url,
    token,
)


def _hostname(host_header: str) -> str:
    return str(urlsplit(f"//{host_header}").hostname or "").lower()


def _is_loopback_host(host_header: str) -> bool:
    host = _hostname(host_header)
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def _is_loopback_peer(value: Any) -> bool:
    try:
        return ipaddress.ip_address(str(value)).is_loopback
    except ValueError:
        return False


def is_local_admin_request(request: Any) -> bool:
    if not _is_loopback_host(str(getattr(request, "host", ""))):
        return False
    transport = getattr(request, "transport", None)
    if transport is None:
        return False
    peer = transport.get_extra_info("peername")
    if not peer or not _is_loopback_peer(peer[0]):
        return False

    headers = getattr(request, "headers", {})
    fetch_site = str(headers.get("Sec-Fetch-Site", "")).lower()
    if fetch_site and fetch_site != "same-origin":
        return False

    origin = str(headers.get("Origin", "")).rstrip("/")
    if origin:
        expected = f"{request.scheme}://{request.host}".rstrip("/")
        if origin != expected:
            return False
    return True


def local_setup_payload(request: Any) -> dict[str, Any]:
    configured_public_url = public_base_url()
    fallback_origin = f"{request.scheme}://{request.host}"
    current_access = access_level()
    profile = setup_profile(configured_public_url, fallback_origin)
    return {
        "localAdmin": True,
        "accessLevel": current_access,
        "accessKey": token(),
        "publicBaseUrl": configured_public_url,
        "environmentOverrides": environment_overrides(),
        "readiness": {
            "httpsEndpoint": bool(configured_public_url),
            "customGptOrigin": custom_gpt_compatible_origin(configured_public_url),
            "fullControl": current_access == "full",
            "readyForCustomGPT": custom_gpt_compatible_origin(configured_public_url)
            and current_access == "full",
        },
        "gpt": profile,
    }


def update_local_setup(request: Any, input_data: dict[str, Any]) -> dict[str, Any]:
    allowed = {"accessLevel", "publicBaseUrl"}
    unexpected = sorted(set(input_data) - allowed)
    if unexpected:
        raise ValueError(f"Unknown local setup fields: {', '.join(unexpected)}")
    if "accessLevel" in input_data:
        set_access_level(input_data["accessLevel"])
    if "publicBaseUrl" in input_data:
        set_public_base_url(input_data["publicBaseUrl"])
    return local_setup_payload(request)


def rotate_local_access_key(request: Any, confirmed: bool) -> dict[str, Any]:
    if confirmed is not True:
        raise PermissionError("Rotating the access key requires confirmed=true.")
    rotate_token()
    return local_setup_payload(request)

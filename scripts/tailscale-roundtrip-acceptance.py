from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

BASE_URL = os.environ.get("CUICOMMANDER_BASE_URL", "http://127.0.0.1:8190").rstrip("/")


def tailscale_executable() -> str:
    found = shutil.which("tailscale")
    if found:
        return found
    candidate = Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Tailscale" / "tailscale.exe"
    if candidate.exists():
        return str(candidate)
    raise RuntimeError("Tailscale is not installed.")


def funnel_snapshot() -> dict[str, Any]:
    result = subprocess.run(
        [tailscale_executable(), "funnel", "status", "--json"],
        capture_output=True,
        text=True,
        timeout=20,
        check=True,
    )
    value = json.loads(result.stdout)
    if not isinstance(value, dict):
        raise RuntimeError("Unexpected Tailscale status response.")
    return value


def stable_funnel_config(value: dict[str, Any]) -> dict[str, Any]:
    return {
        "TCP": value.get("TCP", {}),
        "Web": value.get("Web", {}),
        "AllowFunnel": value.get("AllowFunnel", {}),
    }


def request(
    url: str,
    *,
    method: str = "GET",
    body: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, bytes]:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    request_headers = {"Accept": "application/json", **(headers or {})}
    if data is not None:
        request_headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=request_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            return int(response.status), response.read()
    except urllib.error.HTTPError as error:
        return int(error.code), error.read()


def json_body(raw: bytes) -> dict[str, Any]:
    value = json.loads(raw.decode("utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError("Expected a JSON object response.")
    return value


def main() -> None:
    before = stable_funnel_config(funnel_snapshot())
    status, raw = request(f"{BASE_URL}/cuicommander/v1/local/remote")
    assert status == 200, status
    if json_body(raw).get("configured"):
        raise RuntimeError("Refusing acceptance test while CUICommander remote access is already configured.")

    enabled = False
    try:
        status, raw = request(f"{BASE_URL}/cuicommander/v1/local/setup")
        assert status == 200, status
        access_key = str(json_body(raw).get("accessKey", ""))
        assert access_key

        status, raw = request(
            f"{BASE_URL}/cuicommander/v1/local/remote/tailscale/enable",
            method="POST",
            body={"confirmed": True},
        )
        assert status == 200, (status, raw.decode("utf-8", errors="replace"))
        remote = json_body(raw)
        enabled = True
        assert remote.get("active") is True
        origin = str(remote.get("publicBaseUrl", "")).rstrip("/")
        assert origin.startswith("https://")
        time.sleep(1.0)

        status, raw = request(f"{origin}/cuicommander/v1/openapi")
        assert status == 200, status
        schema = json_body(raw)
        assert schema.get("servers") == [{"url": origin}]

        status, _ = request(f"{origin}/system_stats")
        assert status == 404, status
        status, _ = request(f"{origin}/cuicommander/v1/local/setup")
        assert status == 404, status
        status, _ = request(f"{origin}/cuicommander/v1/manifest")
        assert status == 401, status

        status, raw = request(
            f"{origin}/cuicommander/v1/manifest",
            headers={"Authorization": f"Bearer {access_key}"},
        )
        assert status == 200, status
        manifest = json_body(raw)
        assert manifest.get("schemaUrl") == f"{origin}/cuicommander/v1/openapi"
    finally:
        if enabled:
            status, raw = request(
                f"{BASE_URL}/cuicommander/v1/local/remote/tailscale/disable",
                method="POST",
                body={"confirmed": True},
            )
            assert status == 200, (status, raw.decode("utf-8", errors="replace"))
        after = stable_funnel_config(funnel_snapshot())
        assert after == before, "Existing Tailscale Funnel/Serve configuration changed."

    print("Tailscale remote access round-trip acceptance passed without changing existing services.")


if __name__ == "__main__":
    main()

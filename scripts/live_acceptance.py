from __future__ import annotations

import argparse
import json
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

TERMINAL_JOBS = {"succeeded", "failed", "cancelled"}


def _read_token(token_file: str | None) -> str:
    token = os.getenv("CUICOMMANDER_API_TOKEN", "").strip()
    if token:
        return token
    if token_file:
        value = json.loads(Path(token_file).read_text(encoding="utf-8-sig"))
        token = str(value.get("token", "")).strip()
    if not token:
        raise RuntimeError(
            "Set CUICOMMANDER_API_TOKEN or pass --token-file with a CUICommander connection.json file."
        )
    return token


def _request(
    base_url: str,
    token: str,
    path: str,
    *,
    method: str = "GET",
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = None if body is None else json.dumps(body).encode("utf-8")
    request = Request(
        f"{base_url.rstrip('/')}{path}",
        data=payload,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urlopen(request, timeout=20) as response:
            raw = response.read()
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {path} failed with HTTP {error.code}: {detail}") from error
    return json.loads(raw.decode("utf-8")) if raw else {}


def _post(base_url: str, token: str, path: str, body: dict[str, Any]) -> dict[str, Any]:
    return _request(base_url, token, path, method="POST", body=body)


def _wait_job(base_url: str, token: str, job_id: str, timeout: float = 30) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        job = _request(base_url, token, f"/cuicommander/v1/jobs/{job_id}")
        if str(job.get("status")) in TERMINAL_JOBS:
            return job
        time.sleep(0.25)
    raise RuntimeError(f"Job {job_id} did not finish within {timeout:.0f}s.")


def _wait_history(base_url: str, token: str, prompt_id: str, timeout: float = 20) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = _post(
            base_url,
            token,
            "/cuicommander/v1/execute",
            {"method": "GET", "route": f"/history/{prompt_id}"},
        )
        body = result.get("body") or {}
        if prompt_id in body:
            return body[prompt_id]
        time.sleep(0.25)
    raise RuntimeError(f"Prompt {prompt_id} did not enter history within {timeout:.0f}s.")


def _readonly_acceptance(base_url: str, token: str) -> dict[str, Any]:
    manifest = _request(base_url, token, "/cuicommander/v1/manifest")
    print(
        "manifest:",
        f"version={manifest.get('version')}",
        f"access={manifest.get('accessLevel')}",
        f"roots={manifest.get('rootCount')}",
    )
    for kind in ("roots", "nodes", "routes"):
        result = _post(
            base_url,
            token,
            "/cuicommander/v1/discover",
            {"kind": kind, "limit": 20},
        )
        items = result.get("items") or []
        if not items:
            raise RuntimeError(f"Live discovery returned no {kind}.")
        print(f"discover {kind}: {len(items)} sample items")
    return manifest


def _crud_acceptance(base_url: str, token: str, tag: str) -> None:
    path = f"cuicommander-acceptance/{tag}.txt"
    moved = f"cuicommander-acceptance/{tag}-moved.txt"
    created = _post(
        base_url,
        token,
        "/cuicommander/v1/resources/create",
        {"root": "temp", "path": path, "type": "file", "parents": True, "content": "live acceptance v1"},
    )
    inspected = _post(
        base_url,
        token,
        "/cuicommander/v1/resources/inspect",
        {"root": "temp", "path": path},
    )
    updated = _post(
        base_url,
        token,
        "/cuicommander/v1/resources/update",
        {
            "root": "temp",
            "path": path,
            "expectedFingerprint": inspected["fingerprint"],
            "content": "live acceptance v2",
        },
    )
    moved_result = _post(
        base_url,
        token,
        "/cuicommander/v1/resources/move",
        {
            "root": "temp",
            "path": path,
            "targetRoot": "temp",
            "targetPath": moved,
            "expectedFingerprint": updated["fingerprint"],
        },
    )
    deleted = _post(
        base_url,
        token,
        "/cuicommander/v1/resources/delete",
        {
            "root": "temp",
            "path": moved,
            "expectedFingerprint": moved_result["fingerprint"],
            "confirmed": True,
        },
    )
    if deleted.get("deleted") is not True:
        raise RuntimeError("CRUD cleanup did not report deleted=true.")
    print("crud: create -> inspect -> update -> move -> delete passed")


def _execute_acceptance(base_url: str, token: str, tag: str) -> None:
    system_stats = _post(
        base_url,
        token,
        "/cuicommander/v1/execute",
        {"method": "GET", "route": "/system_stats"},
    )
    if system_stats.get("status") != 200:
        raise RuntimeError("Native /system_stats execution did not return HTTP 200.")
    comfy_version = ((system_stats.get("body") or {}).get("system") or {}).get("comfyui_version")
    print(f"execute GET /system_stats: ComfyUI {comfy_version}")
    node_result = _post(
        base_url,
        token,
        "/cuicommander/v1/discover",
        {"kind": "nodes", "query": "Latent", "limit": 100},
    )
    node_names = {str(item.get("name")) for item in node_result.get("items") or []}
    if not {"EmptyLatentImage", "SaveLatent"}.issubset(node_names):
        print("prompt: skipped because EmptyLatentImage/SaveLatent were not discovered")
        return

    prefix = f"cuicommander-acceptance/live_{tag}"
    prompt = {
        "1": {
            "class_type": "EmptyLatentImage",
            "inputs": {"width": 64, "height": 64, "batch_size": 1},
        },
        "2": {
            "class_type": "SaveLatent",
            "inputs": {"samples": ["1", 0], "filename_prefix": prefix},
        },
    }
    submitted = _post(
        base_url,
        token,
        "/cuicommander/v1/execute",
        {"method": "POST", "route": "/prompt", "confirmed": True, "body": {"prompt": prompt}},
    )
    prompt_id = str((submitted.get("body") or {}).get("prompt_id", ""))
    if not prompt_id:
        raise RuntimeError("Native /prompt execution did not return prompt_id.")
    history = _wait_history(base_url, token, prompt_id)
    status = history.get("status") or {}
    if status.get("status_str") != "success" or status.get("completed") is not True:
        raise RuntimeError(f"Prompt did not complete successfully: {status}")
    print(f"prompt: {prompt_id} completed successfully")

    directory = _post(
        base_url,
        token,
        "/cuicommander/v1/resources/inspect",
        {"root": "output", "path": "cuicommander-acceptance"},
    )
    for item in directory.get("items") or []:
        name = str(item.get("name", ""))
        if not name.startswith(f"live_{tag}"):
            continue
        resource_path = f"cuicommander-acceptance/{name}"
        resource = _post(
            base_url,
            token,
            "/cuicommander/v1/resources/inspect",
            {"root": "output", "path": resource_path},
        )
        _post(
            base_url,
            token,
            "/cuicommander/v1/resources/delete",
            {
                "root": "output",
                "path": resource_path,
                "expectedFingerprint": resource["fingerprint"],
                "confirmed": True,
            },
        )

    directory = _post(
        base_url,
        token,
        "/cuicommander/v1/resources/inspect",
        {"root": "output", "path": "cuicommander-acceptance"},
    )
    if not directory.get("items"):
        _post(
            base_url,
            token,
            "/cuicommander/v1/resources/delete",
            {
                "root": "output",
                "path": "cuicommander-acceptance",
                "expectedFingerprint": directory["fingerprint"],
                "confirmed": True,
            },
        )
    print("prompt cleanup: passed")


def _download_acceptance(base_url: str, token: str, tag: str, url: str) -> None:
    path = f"cuicommander-acceptance/download-{tag}.bin"
    job = _post(
        base_url,
        token,
        "/cuicommander/v1/downloads",
        {"root": "temp", "path": path, "url": url},
    )
    final = _wait_job(base_url, token, str(job["id"]), timeout=60)
    if final.get("status") != "succeeded":
        raise RuntimeError(f"Download job failed: {final.get('error')}")
    resource = _post(
        base_url,
        token,
        "/cuicommander/v1/resources/inspect",
        {"root": "temp", "path": path},
    )
    _post(
        base_url,
        token,
        "/cuicommander/v1/resources/delete",
        {
            "root": "temp",
            "path": path,
            "expectedFingerprint": resource["fingerprint"],
            "confirmed": True,
        },
    )
    print(f"download: {final.get('bytesReceived')} bytes, cleanup passed")


def _cleanup_empty_directory(base_url: str, token: str, root: str, path: str) -> None:
    try:
        directory = _post(
            base_url,
            token,
            "/cuicommander/v1/resources/inspect",
            {"root": root, "path": path},
        )
    except RuntimeError as error:
        if "HTTP 404" in str(error):
            return
        raise
    if directory.get("type") != "directory" or directory.get("items"):
        return
    _post(
        base_url,
        token,
        "/cuicommander/v1/resources/delete",
        {
            "root": root,
            "path": path,
            "expectedFingerprint": directory["fingerprint"],
            "confirmed": True,
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run controlled live acceptance against CUICommander.")
    parser.add_argument(
        "--base-url",
        default=os.getenv("CUICOMMANDER_BASE_URL", "http://127.0.0.1:8188"),
    )
    parser.add_argument(
        "--token-file",
        default=os.getenv("CUICOMMANDER_TOKEN_FILE"),
        help="Path to connection.json; token contents are never printed.",
    )
    parser.add_argument(
        "--mutating",
        action="store_true",
        help="Also run CRUD and native prompt execution. Requires Full control.",
    )
    parser.add_argument(
        "--download-url",
        help="Optional public HTTP(S) URL used to live-test the background downloader.",
    )
    args = parser.parse_args()

    token = _read_token(args.token_file)
    tag = uuid.uuid4().hex[:10]
    try:
        manifest = _readonly_acceptance(args.base_url, token)
        if not args.mutating:
            print("Live read-only acceptance passed.")
            return 0
        if manifest.get("accessLevel") != "full":
            raise RuntimeError("--mutating requires CUICommander Full control access.")
        _crud_acceptance(args.base_url, token, tag)
        _execute_acceptance(args.base_url, token, tag)
        if args.download_url:
            _download_acceptance(args.base_url, token, tag, args.download_url)
        _cleanup_empty_directory(
            args.base_url,
            token,
            "temp",
            "cuicommander-acceptance",
        )
        print("Live mutating acceptance passed.")
        return 0
    except Exception as error:
        print(f"Live acceptance failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())


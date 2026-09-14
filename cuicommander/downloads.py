from __future__ import annotations

import asyncio
import hashlib
import ipaddress
import os
import socket
import time
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlsplit

from .jobs import create_job, start_job, update_job
from .resources import inspect_resource
from .roots import resolve_path

CHUNK_SIZE = 1024 * 1024
MAX_REDIRECTS = 5
MAX_ATTEMPTS = 3
DEFAULT_MAX_BYTES = 256 * 1024 * 1024 * 1024
_ALLOWED_HEADERS = {"authorization", "user-agent", "accept"}


class TransientDownloadError(RuntimeError):
    pass


def _now_ms() -> int:
    return int(time.time() * 1000)


def _max_bytes() -> int:
    value = os.getenv("CUICOMMANDER_MAX_DOWNLOAD_BYTES", "").strip()
    if not value:
        return DEFAULT_MAX_BYTES
    try:
        return max(1, int(value))
    except ValueError:
        return DEFAULT_MAX_BYTES


def _validated_url(url: str) -> str:
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Download URL must use http or https with a hostname.")
    if parsed.username or parsed.password:
        raise ValueError("Credentials must be supplied as headers, not in the URL.")
    _require_public_host(parsed.hostname, parsed.port, parsed.scheme)
    return url


def _require_public_host(host: str, port: int | None, scheme: str) -> None:
    try:
        addresses = [ipaddress.ip_address(host)]
    except ValueError:
        service_port = port or (443 if scheme == "https" else 80)
        try:
            infos = socket.getaddrinfo(host, service_port, type=socket.SOCK_STREAM)
        except socket.gaierror as error:
            raise ValueError("Download hostname could not be resolved.") from error
        addresses = [ipaddress.ip_address(info[4][0]) for info in infos]
    if not addresses or any(not _is_public_address(address) for address in addresses):
        raise PermissionError("Download URLs may not target private, local, or reserved networks.")


def _is_public_address(address: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    return not (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_multicast
        or address.is_reserved
        or address.is_unspecified
    )


def _safe_headers(value: Any) -> dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError("headers must be an object.")
    result: dict[str, str] = {}
    for key, header_value in value.items():
        normalized = str(key).strip().lower()
        if normalized not in _ALLOWED_HEADERS:
            raise ValueError(f"Header {key!s} is not allowed for downloads.")
        text_value = str(header_value)
        if "\r" in text_value or "\n" in text_value:
            raise ValueError("Download header values may not contain line breaks.")
        result[str(key)] = text_value
    return result


def _public_resolver_class(aiohttp_module: Any):
    class PublicResolver(aiohttp_module.abc.AbstractResolver):
        def __init__(self) -> None:
            self._resolver = aiohttp_module.resolver.DefaultResolver()

        async def resolve(
            self,
            host: str,
            port: int = 0,
            family: int = socket.AF_UNSPEC,
        ):
            records = await self._resolver.resolve(host, port, family)
            if not records:
                raise OSError("Download hostname did not resolve.")
            for record in records:
                address = ipaddress.ip_address(record["host"])
                if not _is_public_address(address):
                    raise PermissionError(
                        "Download resolved to a private, local, or reserved network."
                    )
            return records

        async def close(self) -> None:
            await self._resolver.close()

    return PublicResolver


def _public_url(value: str) -> str:
    parsed = urlsplit(value)
    port = f":{parsed.port}" if parsed.port else ""
    return f"{parsed.scheme}://{parsed.hostname}{port}{parsed.path}"


def _origin_key(value: str) -> tuple[str, str, int]:
    parsed = urlsplit(value)
    default_port = 443 if parsed.scheme.lower() == "https" else 80
    return parsed.scheme.lower(), (parsed.hostname or "").lower(), parsed.port or default_port


def _redirect_headers(current_url: str, next_url: str, headers: dict[str, str]) -> dict[str, str]:
    if _origin_key(current_url) == _origin_key(next_url):
        return headers
    return {key: value for key, value in headers.items() if key.lower() != "authorization"}

def _expected_sha256(value: Any) -> str | None:
    if value in {None, ""}:
        return None
    digest = str(value).strip().lower()
    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        raise ValueError("expectedSha256 must be a 64-character hexadecimal digest.")
    return digest


def start_download(input_data: dict[str, Any]) -> dict[str, Any]:
    root = str(input_data.get("root", ""))
    relative_path = str(input_data.get("path", ""))
    url = _validated_url(str(input_data.get("url", "")))
    headers = _safe_headers(input_data.get("headers"))
    expected_sha256 = _expected_sha256(input_data.get("expectedSha256"))
    _, target = resolve_path(root, relative_path, allow_missing=True)
    if target.exists() or target.is_symlink():
        raise FileExistsError("Download target already exists.")
    if not relative_path.replace("\\", "/").strip("/"):
        raise ValueError("Download target must be a file path inside a root.")

    job = create_job(
        "download",
        {
            "root": root,
            "path": relative_path.replace("\\", "/"),
            "source": _public_url(url),
            "bytesReceived": 0,
            "totalBytes": None,
            "attempt": 0,
            "maxAttempts": MAX_ATTEMPTS,
        },
    )

    async def worker(job_id: str) -> None:
        await _run_download(
            job_id,
            root,
            relative_path,
            target,
            url,
            headers,
            expected_sha256,
        )

    return start_job(job, worker)


async def _run_download(
    job_id: str,
    root: str,
    relative_path: str,
    target: Path,
    url: str,
    headers: dict[str, str],
    expected_sha256: str | None,
) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.parent / f".{target.name}.cuicommander-{job_id}.part"
    update_job(job_id, status="running", startedAt=_now_ms())
    try:
        digest, received = await _download_with_retries(
            job_id, partial, url, headers
        )
        if expected_sha256 and digest != expected_sha256:
            raise RuntimeError("Downloaded file SHA-256 did not match expectedSha256.")
        if target.exists() or target.is_symlink():
            raise FileExistsError("Download target appeared while the job was running.")
        os.replace(partial, target)
        result = inspect_resource(root, relative_path)
        update_job(
            job_id,
            status="succeeded",
            finishedAt=_now_ms(),
            bytesReceived=received,
            sha256=digest,
            result=result,
        )
    except asyncio.CancelledError:
        partial.unlink(missing_ok=True)
        update_job(job_id, status="cancelled", finishedAt=_now_ms())
        raise
    except Exception as error:
        partial.unlink(missing_ok=True)
        update_job(
            job_id,
            status="failed",
            finishedAt=_now_ms(),
            error={"type": type(error).__name__, "message": str(error)},
        )


async def _download_with_retries(
    job_id: str,
    partial: Path,
    url: str,
    headers: dict[str, str],
) -> tuple[str, int]:
    import aiohttp

    retryable = (aiohttp.ClientError, asyncio.TimeoutError, TransientDownloadError)
    for attempt in range(1, MAX_ATTEMPTS + 1):
        partial.unlink(missing_ok=True)
        update_job(job_id, attempt=attempt, bytesReceived=0, totalBytes=None)
        try:
            return await _stream_download(job_id, partial, url, headers)
        except asyncio.CancelledError:
            raise
        except retryable:
            if attempt >= MAX_ATTEMPTS:
                raise
            delay = min(2 ** (attempt - 1), 4)
            update_job(job_id, retrying=True, retryAfterSeconds=delay)
            await asyncio.sleep(delay)
            update_job(job_id, retrying=False, retryAfterSeconds=None)
    raise RuntimeError("Download retry loop ended unexpectedly.")


async def _stream_download(
    job_id: str,
    partial: Path,
    url: str,
    headers: dict[str, str],
) -> tuple[str, int]:
    import aiohttp

    PublicResolver = _public_resolver_class(aiohttp)
    connector = aiohttp.TCPConnector(resolver=PublicResolver())
    timeout = aiohttp.ClientTimeout(
        total=None,
        connect=30,
        sock_connect=30,
        sock_read=120,
    )
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        current_url = url
        current_headers = headers.copy()
        for redirect_count in range(MAX_REDIRECTS + 1):
            _validated_url(current_url)
            async with session.get(
                current_url,
                headers=current_headers,
                allow_redirects=False,
            ) as response:
                if 300 <= response.status < 400:
                    if redirect_count >= MAX_REDIRECTS:
                        raise RuntimeError("Download exceeded the redirect limit.")
                    location = response.headers.get("Location")
                    if not location:
                        raise RuntimeError(
                            "Download redirect did not include a Location header."
                        )
                    next_url = urljoin(current_url, location)
                    _validated_url(next_url)
                    current_headers = _redirect_headers(current_url, next_url, current_headers)
                    current_url = next_url
                    continue
                if response.status in {408, 425, 429} or response.status >= 500:
                    raise TransientDownloadError(
                        f"Download temporarily failed with HTTP {response.status}."
                    )
                if response.status not in {200, 206}:
                    raise RuntimeError(f"Download failed with HTTP {response.status}.")
                return await _write_response(job_id, partial, response)
    raise RuntimeError("Download could not be completed.")


async def _write_response(
    job_id: str,
    partial: Path,
    response: Any,
) -> tuple[str, int]:
    total_header = response.headers.get("Content-Length")
    total = int(total_header) if total_header and total_header.isdigit() else None
    maximum = _max_bytes()
    if total is not None and total > maximum:
        raise ValueError("Download exceeds the configured maximum size.")
    update_job(job_id, totalBytes=total)

    digest = hashlib.sha256()
    received = 0
    with partial.open("wb") as handle:
        async for chunk in response.content.iter_chunked(CHUNK_SIZE):
            received += len(chunk)
            if received > maximum:
                raise ValueError("Download exceeds the configured maximum size.")
            handle.write(chunk)
            digest.update(chunk)
            update_job(job_id, bytesReceived=received, totalBytes=total)
        handle.flush()
        os.fsync(handle.fileno())
    return digest.hexdigest(), received


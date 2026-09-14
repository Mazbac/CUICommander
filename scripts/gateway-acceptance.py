from __future__ import annotations

import asyncio
import socket
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cuicommander.action_gateway import ActionGateway
from cuicommander.security import token

PUBLIC_ORIGIN = "https://gateway.acceptance.invalid"


def free_loopback_port() -> int:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])
    finally:
        sock.close()


async def main() -> None:
    from aiohttp import ClientSession, ClientTimeout

    gateway = ActionGateway()
    port = free_loopback_port()
    await gateway.start(PUBLIC_ORIGIN, port, "acceptance")
    try:
        base = f"http://127.0.0.1:{port}"
        timeout = ClientTimeout(total=20)
        async with ClientSession(timeout=timeout) as session:
            async with session.get(f"{base}/cuicommander/v1/openapi") as response:
                assert response.status == 200, response.status
                schema = await response.json()
                assert schema["servers"] == [{"url": PUBLIC_ORIGIN}]

            async with session.get(f"{base}/system_stats") as response:
                assert response.status == 404, response.status

            async with session.get(
                f"{base}/cuicommander/v1/local/setup"
            ) as response:
                assert response.status == 404, response.status

            async with session.get(f"{base}/cuicommander/v1/manifest") as response:
                assert response.status == 401, response.status

            async with session.get(
                f"{base}/cuicommander/v1/manifest",
                headers={"Authorization": f"Bearer {token()}"},
            ) as response:
                assert response.status == 200, response.status
                manifest = await response.json()
                assert manifest["schemaUrl"] == (
                    f"{PUBLIC_ORIGIN}/cuicommander/v1/openapi"
                )
                assert manifest["connection"]["publicBaseUrl"] == PUBLIC_ORIGIN

        print("Action gateway isolation acceptance passed.")
    finally:
        await gateway.stop()


if __name__ == "__main__":
    asyncio.run(main())

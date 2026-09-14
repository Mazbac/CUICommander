from __future__ import annotations

import unittest

from cuicommander.local_admin import is_local_admin_request


class FakeTransport:
    def __init__(self, peer: str) -> None:
        self.peer = peer

    def get_extra_info(self, name: str):
        if name == "peername":
            return (self.peer, 50000)
        return None


class FakeRequest:
    def __init__(
        self,
        *,
        host: str = "127.0.0.1:8188",
        peer: str = "127.0.0.1",
        origin: str | None = "http://127.0.0.1:8188",
        fetch_site: str | None = "same-origin",
    ) -> None:
        self.host = host
        self.scheme = "http"
        self.transport = FakeTransport(peer)
        self.headers: dict[str, str] = {}
        if origin is not None:
            self.headers["Origin"] = origin
        if fetch_site is not None:
            self.headers["Sec-Fetch-Site"] = fetch_site


class LocalAdminBoundaryTests(unittest.TestCase):
    def test_loopback_same_origin_request_is_allowed(self) -> None:
        self.assertTrue(is_local_admin_request(FakeRequest()))
        self.assertTrue(
            is_local_admin_request(
                FakeRequest(
                    host="localhost:8188",
                    origin="http://localhost:8188",
                )
            )
        )

    def test_public_host_or_non_loopback_peer_is_rejected(self) -> None:
        public_request = FakeRequest(
            host="comfy.example",
            origin="https://comfy.example",
        )
        self.assertFalse(is_local_admin_request(public_request))
        self.assertFalse(is_local_admin_request(FakeRequest(peer="192.168.1.20")))

    def test_cross_origin_browser_request_is_rejected(self) -> None:
        self.assertFalse(
            is_local_admin_request(FakeRequest(origin="https://other.example"))
        )
        self.assertFalse(is_local_admin_request(FakeRequest(fetch_site="cross-site")))


if __name__ == "__main__":
    unittest.main()

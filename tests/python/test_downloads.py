from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cuicommander import downloads, jobs


class FakeContent:
    def __init__(self, chunks: list[bytes]) -> None:
        self.chunks = chunks

    async def iter_chunked(self, _size: int):
        for chunk in self.chunks:
            yield chunk


class FakeResponse:
    def __init__(self, chunks: list[bytes]) -> None:
        self.headers = {"Content-Length": str(sum(map(len, chunks)))}
        self.content = FakeContent(chunks)


class DownloadValidationTests(unittest.TestCase):
    def tearDown(self) -> None:
        jobs._reset_for_tests()

    def test_private_and_embedded_credential_urls_are_blocked(self) -> None:
        with self.assertRaises(PermissionError):
            downloads._validated_url("http://127.0.0.1/model.safetensors")
        with self.assertRaises(ValueError):
            downloads._validated_url("https://user:secret@example.com/model.safetensors")

    def test_public_url_and_header_policy(self) -> None:
        with patch("cuicommander.downloads._require_public_host"):
            self.assertEqual(
                downloads._validated_url("https://example.com/model.safetensors?token=secret"),
                "https://example.com/model.safetensors?token=secret",
            )
        headers = downloads._safe_headers({"Authorization": "Bearer abc", "Accept": "*/*"})
        self.assertEqual(headers, {"Authorization": "Bearer abc", "Accept": "*/*"})
        self.assertEqual(
            downloads._redirect_headers(
                "https://example.com/model", "https://example.com/next", headers
            ),
            headers,
        )
        self.assertNotIn(
            "Authorization",
            downloads._redirect_headers(
                "https://example.com/model", "http://example.com/next", headers
            ),
        )
        self.assertNotIn(
            "Authorization",
            downloads._redirect_headers(
                "https://example.com/model", "https://example.com:444/next", headers
            ),
        )
        with self.assertRaises(ValueError):
            downloads._safe_headers({"Authorization": "Bearer abc\r\nX-Test: bad"})
        with self.assertRaises(ValueError):
            downloads._safe_headers({"X-Forwarded-Host": "127.0.0.1"})


class DownloadStreamingTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        jobs._reset_for_tests()
        self.temp = tempfile.TemporaryDirectory()

    async def asyncTearDown(self) -> None:
        jobs._reset_for_tests()
        self.temp.cleanup()

    async def test_streaming_hashes_and_updates_progress(self) -> None:
        job = jobs.create_job("download", {"bytesReceived": 0, "totalBytes": None})
        path = Path(self.temp.name) / "model.bin"
        chunks = [b"abc", b"def"]
        digest, received = await downloads._write_response(
            job["id"], path, FakeResponse(chunks)
        )
        self.assertEqual(received, 6)
        self.assertEqual(digest, hashlib.sha256(b"abcdef").hexdigest())
        self.assertEqual(jobs.get_job(job["id"])["bytesReceived"], 6)
        self.assertEqual(path.read_bytes(), b"abcdef")


if __name__ == "__main__":
    unittest.main()

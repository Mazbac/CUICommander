from __future__ import annotations

import unittest
from unittest.mock import patch

from cuicommander import runtime


class RuntimeValidationTests(unittest.TestCase):
    def tearDown(self) -> None:
        runtime._clear_responses_for_tests()

    def test_dynamic_route_matching(self) -> None:
        self.assertTrue(runtime._canonical_matches("/api/jobs/{job_id}", "/api/jobs/abc"))
        self.assertFalse(runtime._canonical_matches("/api/jobs/{job_id}", "/api/jobs/a/b"))

    def test_execute_is_comfyui_scoped_and_confirms_mutations(self) -> None:
        with patch("cuicommander.runtime._route_exists", return_value=True):
            method, path, query, body = runtime._validate_request(
                {"method": "GET", "route": "/models", "query": {"kind": "all"}}
            )
            self.assertEqual((method, path), ("GET", "/models"))
            self.assertEqual(query, {"kind": "all"})
            self.assertIsNone(body)

            with self.assertRaises(PermissionError):
                runtime._validate_request({"method": "POST", "route": "/prompt", "body": {}})

            accepted = runtime._validate_request(
                {"method": "POST", "route": "/prompt", "body": {}, "confirmed": True}
            )
            self.assertEqual(accepted[0:2], ("POST", "/prompt"))

    def test_external_and_recursive_routes_are_rejected(self) -> None:
        with patch("cuicommander.runtime._route_exists", return_value=True):
            for route in ["https://example.com/prompt", "/prompt?x=1", "/cuicommander/v1/manifest"]:
                with self.subTest(route=route):
                    with self.assertRaises(ValueError):
                        runtime._validate_request({"method": "GET", "route": route})

    def test_retained_native_response_is_completely_readable(self) -> None:
        text = ("a" * 1023) + "€" + ("tail" * 500)
        response_id = runtime._store_response_bytes(text.encode("utf-8"), "text/plain")

        offset = 0
        parts: list[str] = []
        while True:
            chunk = runtime.read_runtime_response(
                {
                    "responseId": response_id,
                    "offset": offset,
                    "maxBytes": 1024,
                    "encoding": "utf-8",
                }
            )
            parts.append(chunk["content"])
            if chunk["eof"]:
                self.assertIsNone(chunk["nextOffset"])
                break
            self.assertGreater(chunk["nextOffset"], offset)
            offset = chunk["nextOffset"]

        self.assertEqual("".join(parts), text)

    def test_unknown_retained_response_is_rejected(self) -> None:
        with self.assertRaisesRegex(KeyError, "Unknown or expired"):
            runtime.read_runtime_response({"responseId": "missing"})

    def test_unknown_live_route_is_rejected(self) -> None:
        with patch("cuicommander.runtime._route_exists", return_value=False):
            with self.assertRaises(ValueError):
                runtime._validate_request({"method": "GET", "route": "/does-not-exist"})


if __name__ == "__main__":
    unittest.main()

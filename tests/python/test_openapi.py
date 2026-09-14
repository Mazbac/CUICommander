from __future__ import annotations

import unittest

from cuicommander.openapi import build_schema


class OpenApiTests(unittest.TestCase):
    def test_schema_advertises_only_implemented_generic_operations(self) -> None:
        schema = build_schema("https://comfy.example", "test")
        paths = schema["paths"]
        self.assertIn("/cuicommander/v1/downloads", paths)
        self.assertIn("/cuicommander/v1/jobs/{job_id}", paths)
        self.assertIn("/cuicommander/v1/execute", paths)
        execute = paths["/cuicommander/v1/execute"]["post"]
        self.assertEqual(execute["operationId"], "executeComfyUI")
        self.assertEqual(schema["servers"], [{"url": "https://comfy.example"}])

    def test_local_admin_routes_are_never_exposed_to_actions(self) -> None:
        paths = build_schema("https://comfy.example", "test")["paths"]
        self.assertFalse(any("/local/" in path for path in paths))
        self.assertNotIn("/cuicommander/v1/local/setup", paths)


if __name__ == "__main__":
    unittest.main()

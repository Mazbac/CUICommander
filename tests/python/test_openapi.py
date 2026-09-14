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


if __name__ == "__main__":
    unittest.main()

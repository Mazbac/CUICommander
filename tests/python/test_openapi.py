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
        self.assertIn("/cuicommander/v1/resources/read", paths)
        self.assertIn("/cuicommander/v1/resources/patch", paths)
        self.assertIn("/cuicommander/v1/runtime/responses/read", paths)
        self.assertEqual(
            paths["/cuicommander/v1/resources/read"]["post"]["operationId"],
            "readComfyUIResource",
        )
        self.assertEqual(
            paths["/cuicommander/v1/resources/patch"]["post"]["operationId"],
            "patchComfyUIResource",
        )
        self.assertEqual(
            paths["/cuicommander/v1/runtime/responses/read"]["post"]["operationId"],
            "readComfyUIResponse",
        )
        discover_properties = paths["/cuicommander/v1/discover"]["post"]["requestBody"][
            "content"
        ]["application/json"]["schema"]["properties"]
        self.assertIn("offset", discover_properties)
        for mutation_path in (
            "/cuicommander/v1/resources/update",
            "/cuicommander/v1/resources/patch",
            "/cuicommander/v1/resources/move",
            "/cuicommander/v1/resources/delete",
        ):
            body_schema = paths[mutation_path]["post"]["requestBody"]["content"][
                "application/json"
            ]["schema"]
            self.assertIn("expectedFingerprint", body_schema["required"])
        execute = paths["/cuicommander/v1/execute"]["post"]
        self.assertEqual(execute["operationId"], "executeComfyUI")
        self.assertEqual(schema["servers"], [{"url": "https://comfy.example"}])
        self.assertEqual(schema["components"]["schemas"], {})

    def test_local_admin_routes_are_never_exposed_to_actions(self) -> None:
        paths = build_schema("https://comfy.example", "test")["paths"]
        self.assertFalse(any("/local/" in path for path in paths))
        self.assertNotIn("/cuicommander/v1/local/setup", paths)


if __name__ == "__main__":
    unittest.main()

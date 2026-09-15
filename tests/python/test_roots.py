from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cuicommander import roots


class RootResolutionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name).resolve()
        self.internal = self.base / "user" / "__cuicommander"
        self.internal.mkdir(parents=True)
        self.root_patch = patch(
            "cuicommander.roots.roots_by_id",
            return_value={"root": {"path": str(self.base)}},
        )
        self.internal_patch = patch(
            "cuicommander.roots.internal_state_directory",
            return_value=self.internal,
        )
        self.root_patch.start()
        self.internal_patch.start()

    def tearDown(self) -> None:
        self.internal_patch.stop()
        self.root_patch.stop()
        self.temp.cleanup()

    def test_relative_paths_resolve_inside_root(self) -> None:
        target = self.base / "models" / "example.safetensors"
        target.parent.mkdir()
        target.write_bytes(b"model")

        base, resolved = roots.resolve_path("root", "models/example.safetensors")
        self.assertEqual(base, self.base)
        self.assertEqual(resolved, target)

    def test_traversal_and_absolute_paths_are_blocked(self) -> None:
        with self.assertRaises(ValueError):
            roots.resolve_path("root", "../escape", allow_missing=True)
        with self.assertRaises(ValueError):
            roots.resolve_path("root", "/absolute/path", allow_missing=True)
        if os.name == "nt":
            with self.assertRaises(ValueError):
                roots.resolve_path("root", "C:/absolute/path", allow_missing=True)

    def test_internal_credential_state_is_blocked(self) -> None:
        secret = self.internal / "connection.json"
        secret.write_text("{}", encoding="utf-8")
        with self.assertRaises(PermissionError):
            roots.resolve_path("root", "user/__cuicommander/connection.json")

    def test_internal_state_parent_detection(self) -> None:
        self.assertTrue(roots.contains_internal_state(self.base / "user"))
        self.assertTrue(roots.contains_internal_state(self.internal))
        models = self.base / "models"
        models.mkdir()
        self.assertFalse(roots.contains_internal_state(models))

    def test_discovery_disambiguates_normalized_registered_root_ids(self) -> None:
        import sys
        from types import SimpleNamespace

        fake = SimpleNamespace(
            base_path=str(self.base),
            get_input_directory=lambda: str(self.base / "input"),
            get_output_directory=lambda: str(self.base / "output"),
            get_temp_directory=lambda: str(self.base / "temp"),
            get_user_directory=lambda: str(self.base / "user"),
            models_dir=str(self.base / "models"),
            folder_names_and_paths={
                "LLM": ([str(self.base / "models" / "llm-a")], set()),
                "llm": ([str(self.base / "models" / "llm-b")], set()),
            },
        )
        with patch.dict(sys.modules, {"folder_paths": fake}):
            discovered = roots.discover_roots()
        ids = [item["id"] for item in discovered]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertIn("registered.llm.0", ids)
        self.assertIn("registered.llm.0.2", ids)


if __name__ == "__main__":
    unittest.main()

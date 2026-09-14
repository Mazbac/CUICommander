from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cuicommander import resources


class ResourceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.patcher = patch(
            "cuicommander.resources.resolve_path",
            side_effect=self._resolve,
        )
        self.patcher.start()
        self.internal_patcher = patch(
            "cuicommander.resources.contains_internal_state", return_value=False
        )
        self.internal_patcher.start()

    def tearDown(self) -> None:
        self.internal_patcher.stop()
        self.patcher.stop()
        self.temp.cleanup()

    def _resolve(self, root: str, relative: str, allow_missing: bool = False):
        self.assertEqual(root, "root")
        target = self.base / relative
        if not allow_missing and not target.exists() and not target.is_symlink():
            raise FileNotFoundError("missing")
        return self.base, target

    def test_file_crud_requires_fresh_fingerprint(self) -> None:
        created = resources.create_resource(
            {"root": "root", "path": "models/example.txt", "type": "file", "content": "v1"}
        )
        self.assertEqual(created["preview"], "v1")

        with self.assertRaises(RuntimeError):
            resources.update_resource(
                {
                    "root": "root",
                    "path": "models/example.txt",
                    "expectedFingerprint": "0" * 64,
                    "content": "v2",
                }
            )

        updated = resources.update_resource(
            {
                "root": "root",
                "path": "models/example.txt",
                "expectedFingerprint": created["fingerprint"],
                "content": "v2",
            }
        )
        self.assertEqual(updated["preview"], "v2")

    def test_move_uses_fingerprint_and_keeps_content(self) -> None:
        created = resources.create_resource(
            {"root": "root", "path": "a.bin", "type": "file", "contentBase64": "AQID"}
        )
        moved = resources.move_resource(
            {
                "root": "root",
                "path": "a.bin",
                "targetRoot": "root",
                "targetPath": "nested/b.bin",
                "expectedFingerprint": created["fingerprint"],
            }
        )
        self.assertFalse((self.base / "a.bin").exists())
        self.assertEqual(moved["previewEncoding"], "utf-8")
        self.assertEqual((self.base / "nested/b.bin").read_bytes(), b"\x01\x02\x03")

    def test_recursive_directory_delete_requires_fingerprint(self) -> None:
        directory = self.base / "custom_nodes" / "pack"
        directory.mkdir(parents=True)
        (directory / "node.py").write_text("pass\n", encoding="utf-8")
        inspected = resources.inspect_resource("root", "custom_nodes/pack")

        with self.assertRaises(ValueError):
            resources.delete_resource(
                {"root": "root", "path": "custom_nodes/pack", "expectedFingerprint": inspected["fingerprint"]}
            )

        deleted = resources.delete_resource(
            {
                "root": "root",
                "path": "custom_nodes/pack",
                "expectedFingerprint": inspected["fingerprint"],
                "recursive": True,
            }
        )
        self.assertTrue(deleted["deleted"])
        self.assertFalse(directory.exists())

    def test_internal_state_parent_directory_is_not_mutable(self) -> None:
        directory = self.base / "user"
        directory.mkdir()
        (directory / "connection.json").write_text("secret", encoding="utf-8")
        inspected = resources.inspect_resource("root", "user")

        with patch("cuicommander.resources.contains_internal_state", return_value=True):
            with self.assertRaises(PermissionError):
                resources.delete_resource(
                    {
                        "root": "root",
                        "path": "user",
                        "expectedFingerprint": inspected["fingerprint"],
                        "recursive": True,
                    }
                )
            with self.assertRaises(PermissionError):
                resources.move_resource(
                    {
                        "root": "root",
                        "path": "user",
                        "targetRoot": "root",
                        "targetPath": "user-moved",
                        "expectedFingerprint": inspected["fingerprint"],
                    }
                )
    def test_root_move_and_delete_are_blocked(self) -> None:
        with self.assertRaisesRegex(ValueError, "root is not allowed"):
            resources.move_resource(
                {
                    "root": "root",
                    "path": "",
                    "targetRoot": "root",
                    "targetPath": "elsewhere",
                    "expectedFingerprint": "0" * 64,
                }
            )
        with self.assertRaisesRegex(ValueError, "root is not allowed"):
            resources.delete_resource(
                {"root": "root", "path": "", "expectedFingerprint": "0" * 64}
            )


if __name__ == "__main__":
    unittest.main()


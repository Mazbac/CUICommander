from __future__ import annotations

import base64
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
    def test_large_utf8_file_is_completely_readable_in_chunks(self) -> None:
        text = ("node-data-" * 9000) + "â‚¬ tail"
        target = self.base / "workflow.json"
        target.write_text(text, encoding="utf-8")

        inspected = resources.inspect_resource("root", "workflow.json")
        self.assertTrue(inspected["previewTruncated"])
        self.assertIsNone(inspected["preview"])

        offset = 0
        chunks: list[str] = []
        while True:
            chunk = resources.read_resource(
                {
                    "root": "root",
                    "path": "workflow.json",
                    "offset": offset,
                    "maxBytes": 4096,
                    "encoding": "utf-8",
                    "expectedFingerprint": inspected["fingerprint"],
                }
            )
            self.assertEqual(chunk["fingerprint"], inspected["fingerprint"])
            chunks.append(chunk["content"])
            if chunk["eof"]:
                self.assertIsNone(chunk["nextOffset"])
                break
            self.assertGreater(chunk["nextOffset"], offset)
            offset = chunk["nextOffset"]

        self.assertEqual("".join(chunks), text)

    def test_utf8_chunk_boundary_never_splits_a_character(self) -> None:
        text = ("a" * 1023) + "â‚¬tail"
        (self.base / "utf8.txt").write_text(text, encoding="utf-8")
        inspected = resources.inspect_resource("root", "utf8.txt")

        first = resources.read_resource(
            {
                "root": "root",
                "path": "utf8.txt",
                "maxBytes": 1024,
                "encoding": "utf-8",
                "expectedFingerprint": inspected["fingerprint"],
            }
        )
        self.assertEqual(first["bytesRead"], 1023)
        second = resources.read_resource(
            {
                "root": "root",
                "path": "utf8.txt",
                "offset": first["nextOffset"],
                "maxBytes": 1024,
                "encoding": "utf-8",
                "expectedFingerprint": inspected["fingerprint"],
            }
        )
        self.assertEqual(first["content"] + second["content"], text)
        self.assertTrue(second["eof"])

    def test_binary_chunks_reconstruct_exact_bytes(self) -> None:
        data = bytes(range(256)) * 80
        (self.base / "binary.bin").write_bytes(data)
        inspected = resources.inspect_resource("root", "binary.bin")

        offset = 0
        reconstructed = bytearray()
        while True:
            chunk = resources.read_resource(
                {
                    "root": "root",
                    "path": "binary.bin",
                    "offset": offset,
                    "maxBytes": 2048,
                    "encoding": "base64",
                    "expectedFingerprint": inspected["fingerprint"],
                }
            )
            reconstructed.extend(base64.b64decode(chunk["contentBase64"]))
            if chunk["eof"]:
                break
            offset = chunk["nextOffset"]
        self.assertEqual(bytes(reconstructed), data)

    def test_chunk_read_rejects_stale_fingerprint(self) -> None:
        target = self.base / "stale.txt"
        target.write_text("before", encoding="utf-8")
        inspected = resources.inspect_resource("root", "stale.txt")
        target.write_text("after", encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "changed during chunked read"):
            resources.read_resource(
                {
                    "root": "root",
                    "path": "stale.txt",
                    "expectedFingerprint": inspected["fingerprint"],
                }
            )

    def test_patch_replaces_and_appends_with_fresh_fingerprints(self) -> None:
        target = self.base / "patch.txt"
        target.write_text("prefix-middle-suffix", encoding="utf-8")
        inspected = resources.inspect_resource("root", "patch.txt")
        patched = resources.patch_resource(
            {
                "root": "root",
                "path": "patch.txt",
                "expectedFingerprint": inspected["fingerprint"],
                "offset": len("prefix-"),
                "deleteBytes": len("middle"),
                "content": "NEW",
            }
        )
        self.assertEqual(target.read_text(encoding="utf-8"), "prefix-NEW-suffix")
        self.assertNotEqual(patched["fingerprint"], inspected["fingerprint"])

        appended = resources.patch_resource(
            {
                "root": "root",
                "path": "patch.txt",
                "expectedFingerprint": patched["fingerprint"],
                "offset": target.stat().st_size,
                "deleteBytes": 0,
                "content": "+tail",
            }
        )
        self.assertEqual(target.read_text(encoding="utf-8"), "prefix-NEW-suffix+tail")
        with self.assertRaises(RuntimeError):
            resources.patch_resource(
                {
                    "root": "root",
                    "path": "patch.txt",
                    "expectedFingerprint": patched["fingerprint"],
                    "offset": 0,
                    "deleteBytes": 0,
                    "content": "stale",
                }
            )
        self.assertEqual(appended["fingerprint"], resources.fingerprint(target)[0])

    def test_directory_pagination_has_no_hidden_items(self) -> None:
        directory = self.base / "many"
        directory.mkdir()
        for index in range(275):
            (directory / f"file-{index:03d}.txt").write_text(str(index), encoding="utf-8")

        first = resources.inspect_resource("root", "many", offset=0, limit=250)
        second = resources.inspect_resource(
            "root",
            "many",
            offset=first["nextOffset"],
            limit=250,
            expected_fingerprint=first["fingerprint"],
        )
        names = [item["name"] for item in first["items"] + second["items"]]
        self.assertEqual(len(names), 275)
        self.assertEqual(len(set(names)), 275)
        self.assertEqual(first["totalItems"], 275)
        self.assertTrue(first["truncated"])
        self.assertFalse(second["truncated"])
        self.assertIsNone(second["nextOffset"])

        (directory / "new-after-first-page.txt").write_text("new", encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "changed while it was being paged"):
            resources.inspect_resource(
                "root",
                "many",
                offset=first["nextOffset"],
                limit=250,
                expected_fingerprint=first["fingerprint"],
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


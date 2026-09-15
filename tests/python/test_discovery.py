from __future__ import annotations

import sys
import types
import unittest
from unittest.mock import patch

from cuicommander import discovery


class DiscoveryTests(unittest.TestCase):
    def test_root_discovery_is_pageable_without_hiding_items(self) -> None:
        roots = [
            {
                "id": f"root-{index:03d}",
                "label": f"Root {index}",
                "path": f"C:/root/{index}",
                "source": "folder_paths",
                "exists": True,
            }
            for index in range(503)
        ]
        with patch("cuicommander.discovery.discover_roots", return_value=roots):
            first = discovery.discover("roots", limit=500, offset=0)
            second = discovery.discover(
                "roots", limit=500, offset=first["nextOffset"]
            )

        self.assertEqual(len(first["items"]), 500)
        self.assertEqual(len(second["items"]), 3)
        self.assertEqual(first["totalItems"], 503)
        self.assertFalse(first["complete"])
        self.assertTrue(second["complete"])
        self.assertIsNone(second["nextOffset"])

    def test_node_discovery_paginates_in_stable_name_order(self) -> None:
        def node(name: str):
            return type(
                name,
                (),
                {
                    "CATEGORY": "test",
                    "DESCRIPTION": "test node",
                    "RETURN_TYPES": ("X",),
                    "FUNCTION": "run",
                    "INPUT_TYPES": staticmethod(lambda: {"required": {}}),
                },
            )

        fake_nodes = types.SimpleNamespace(
            NODE_CLASS_MAPPINGS={
                "Zulu": node("Zulu"),
                "Alpha": node("Alpha"),
                "Echo": node("Echo"),
                "Bravo": node("Bravo"),
            }
        )
        with patch.dict(sys.modules, {"nodes": fake_nodes}):
            first = discovery.discover_nodes(limit=2, offset=0)
            second = discovery.discover_nodes(limit=2, offset=first["nextOffset"])

        names = [item["name"] for item in first["items"] + second["items"]]
        self.assertEqual(names, ["Alpha", "Bravo", "Echo", "Zulu"])
        self.assertFalse(first["complete"])
        self.assertTrue(second["complete"])

    def test_negative_discovery_offset_is_rejected(self) -> None:
        with patch("cuicommander.discovery.discover_roots", return_value=[]):
            with self.assertRaisesRegex(ValueError, "offset"):
                discovery.discover("roots", offset=-1)


if __name__ == "__main__":
    unittest.main()

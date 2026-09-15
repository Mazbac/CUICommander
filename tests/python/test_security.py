from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cuicommander import security


class SecuritySettingsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.settings = Path(self.temp.name) / "connection.json"
        self.path_patch = patch(
            "cuicommander.security.settings_path",
            return_value=self.settings,
        )
        self.env_patch = patch.dict(
            os.environ,
            {security.TOKEN_ENV: "", security.ACCESS_ENV: ""},
            clear=False,
        )
        self.path_patch.start()
        self.env_patch.start()

    def tearDown(self) -> None:
        self.env_patch.stop()
        self.path_patch.stop()
        self.temp.cleanup()
    def test_local_settings_can_enable_full_and_store_https_origin(self) -> None:
        self.assertEqual(security.access_level(), "inspect")
        self.assertEqual(security.set_access_level("full"), "full")
        self.assertEqual(security.access_level(), "full")
        self.assertEqual(
            security.set_public_base_url("https://comfy.example/"),
            "https://comfy.example",
        )
        self.assertEqual(security.public_base_url(), "https://comfy.example")
        self.assertEqual(
            security.set_public_base_url("https://comfy.example:443"),
            "https://comfy.example",
        )
        self.assertTrue(security.custom_gpt_compatible_origin("https://comfy.example"))
        self.assertFalse(
            security.custom_gpt_compatible_origin("https://comfy.example:10000")
        )

    def test_public_endpoint_rejects_non_https_or_path(self) -> None:
        with self.assertRaises(ValueError):
            security.set_public_base_url("http://comfy.example")
        with self.assertRaises(ValueError):
            security.set_public_base_url("https://comfy.example/prefix")
        with self.assertRaises(ValueError):
            security.set_public_base_url("https://user:pass@comfy.example")

    def test_public_connection_info_does_not_expose_local_credential_path(self) -> None:
        info = security.public_connection_info()
        self.assertNotIn("credentialFile", info)
        self.assertNotIn(str(self.settings), info.values())

    def test_access_key_rotation_changes_file_managed_key(self) -> None:
        first = security.token()
        second = security.rotate_token()
        self.assertNotEqual(first, second)
        self.assertEqual(security.token(), second)
    def test_environment_overrides_cannot_be_mutated_through_file_settings(self) -> None:
        with patch.dict(
            os.environ,
            {
                security.ACCESS_ENV: "full",
                security.TOKEN_ENV: "environment-owned-key-that-is-long-enough",
            },
            clear=False,
        ):
            with self.assertRaises(RuntimeError):
                security.set_access_level("edit")
            with self.assertRaises(RuntimeError):
                security.rotate_token()
            overrides = security.environment_overrides()
            self.assertTrue(overrides["accessLevel"])
            self.assertTrue(overrides["accessKey"])


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import unittest

from cuicommander.gpt_setup import GPT_INSTRUCTIONS, action_schema_url, setup_profile


class GptSetupTests(unittest.TestCase):
    def test_public_https_origin_drives_action_schema_url(self) -> None:
        self.assertEqual(
            action_schema_url("https://comfy.example", "http://127.0.0.1:8188"),
            "https://comfy.example/cuicommander/v1/openapi",
        )
        profile = setup_profile(
            "https://comfy.example",
            "http://127.0.0.1:8188",
        )
        self.assertEqual(profile["authentication"]["scheme"], "bearer")
        self.assertEqual(profile["name"], "CUICommander")

    def test_instructions_encode_universal_control_invariant(self) -> None:
        self.assertIn("Discover / Inspect -> Create / Read / Update / Delete -> Execute", GPT_INSTRUCTIONS)
        self.assertIn("untrusted data", GPT_INSTRUCTIONS)
        self.assertIn("Never bypass confirmation requirements", GPT_INSTRUCTIONS)
        self.assertIn("local setup/admin routes", GPT_INSTRUCTIONS)


if __name__ == "__main__":
    unittest.main()

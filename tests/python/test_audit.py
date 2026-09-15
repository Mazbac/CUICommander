from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cuicommander import audit


class AuditTests(unittest.TestCase):
    def test_activity_is_bounded_and_filters_sensitive_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "activity.json"
            with patch("cuicommander.audit._path", return_value=path):
                item = audit.record_activity(
                    "resource.update",
                    {
                        "root": "user",
                        "path": "workflow.json",
                        "content": "secret body",
                        "headers": {"Authorization": "secret"},
                    },
                )
                self.assertEqual(item["detail"]["root"], "user")
                self.assertNotIn("content", item["detail"])
                self.assertNotIn("headers", item["detail"])
                listed = audit.list_activity(10)
                self.assertEqual(listed[0]["action"], "resource.update")


if __name__ == "__main__":
    unittest.main()

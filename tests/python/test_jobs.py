from __future__ import annotations

import asyncio
import unittest

from cuicommander import jobs


class JobTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        jobs._reset_for_tests()

    async def asyncTearDown(self) -> None:
        jobs._reset_for_tests()
        await asyncio.sleep(0)

    async def test_cancel_before_worker_runs_reaches_cancelled(self) -> None:
        gate = asyncio.Event()

        async def worker(_job_id: str) -> None:
            await gate.wait()

        job = jobs.create_job("test", {})
        jobs.start_job(job, worker)
        cancelling = jobs.cancel_job(job["id"])
        self.assertEqual(cancelling["status"], "cancelling")
        for _ in range(3):
            await asyncio.sleep(0)
        self.assertEqual(jobs.get_job(job["id"])["status"], "cancelled")


class JobPersistenceTests(unittest.TestCase):
    def test_restore_marks_nonterminal_jobs_interrupted(self) -> None:
        import json
        import tempfile
        from pathlib import Path
        from unittest.mock import patch

        jobs._reset_for_tests()
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "jobs.json"
            path.write_text(
                json.dumps([
                    {"id": "job-1", "kind": "download", "status": "running", "createdAt": 1, "updatedAt": 2},
                    {"id": "job-2", "kind": "download", "status": "succeeded", "createdAt": 1, "updatedAt": 2},
                ]),
                encoding="utf-8",
            )
            with patch("cuicommander.jobs._jobs_path", return_value=path):
                jobs.restore_jobs()
                self.assertEqual(jobs.get_job("job-1")["status"], "interrupted")
                self.assertEqual(jobs.get_job("job-2")["status"], "succeeded")
        jobs._reset_for_tests()

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

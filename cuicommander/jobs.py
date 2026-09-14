from __future__ import annotations

import asyncio
import time
import uuid
from collections import OrderedDict
from typing import Any, Awaitable, Callable

MAX_JOBS = 100
_JOBS: OrderedDict[str, dict[str, Any]] = OrderedDict()
_TASKS: dict[str, asyncio.Task[Any]] = {}


def _now_ms() -> int:
    return int(time.time() * 1000)


def create_job(kind: str, detail: dict[str, Any]) -> dict[str, Any]:
    job_id = str(uuid.uuid4())
    job = {
        "id": job_id,
        "kind": kind,
        "status": "queued",
        "createdAt": _now_ms(),
        "updatedAt": _now_ms(),
        **detail,
    }
    _JOBS[job_id] = job
    _trim()
    return job.copy()


def update_job(job_id: str, **changes: Any) -> dict[str, Any]:
    job = _JOBS.get(job_id)
    if job is None:
        raise KeyError("Unknown CUICommander job.")
    job.update(changes)
    job["updatedAt"] = _now_ms()
    _JOBS.move_to_end(job_id)
    return job.copy()


def get_job(job_id: str) -> dict[str, Any]:
    job = _JOBS.get(job_id)
    if job is None:
        raise KeyError("Unknown CUICommander job.")
    return job.copy()


def list_jobs(limit: int = 50) -> list[dict[str, Any]]:
    bounded = max(1, min(int(limit), MAX_JOBS))
    return [item.copy() for item in list(_JOBS.values())[-bounded:]][::-1]


def start_job(job: dict[str, Any], worker: Callable[[str], Awaitable[None]]) -> dict[str, Any]:
    job_id = str(job["id"])
    task = asyncio.create_task(worker(job_id), name=f"cuicommander:{job_id}")
    _TASKS[job_id] = task
    task.add_done_callback(lambda finished: _finish_task(job_id, finished))
    return job.copy()


def _finish_task(job_id: str, task: asyncio.Task[Any]) -> None:
    _TASKS.pop(job_id, None)
    job = _JOBS.get(job_id)
    if task.cancelled() and job is not None and job.get("status") not in {"succeeded", "failed", "cancelled"}:
        update_job(job_id, status="cancelled", finishedAt=_now_ms())


def cancel_job(job_id: str) -> dict[str, Any]:
    job = get_job(job_id)
    if job["status"] in {"succeeded", "failed", "cancelled"}:
        return job
    task = _TASKS.get(job_id)
    if task is None:
        return update_job(job_id, status="cancelled", finishedAt=_now_ms())
    task.cancel()
    return update_job(job_id, status="cancelling")


def _trim() -> None:
    while len(_JOBS) > MAX_JOBS:
        job_id, job = next(iter(_JOBS.items()))
        if job_id in _TASKS:
            _JOBS.move_to_end(job_id)
            if all(key in _TASKS for key in _JOBS):
                break
            continue
        _JOBS.pop(job_id, None)


def _reset_for_tests() -> None:
    for task in list(_TASKS.values()):
        task.cancel()
    _TASKS.clear()
    _JOBS.clear()


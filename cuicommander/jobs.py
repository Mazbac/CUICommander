from __future__ import annotations

import asyncio
import json
import os
import time
import uuid
from collections import OrderedDict
from pathlib import Path
from typing import Any, Awaitable, Callable

from .security import internal_state_directory

MAX_JOBS = 100
PERSIST_INTERVAL_MS = 2000
_TERMINAL = {"succeeded", "failed", "cancelled", "interrupted"}
_JOBS: OrderedDict[str, dict[str, Any]] = OrderedDict()
_TASKS: dict[str, asyncio.Task[Any]] = {}
_LAST_PERSIST_MS = 0


def _now_ms() -> int:
    return int(time.time() * 1000)


def _jobs_path() -> Path:
    return internal_state_directory() / "jobs.json"


def _write_jobs(items: list[dict[str, Any]]) -> None:
    path = _jobs_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(items[-MAX_JOBS:], indent=2) + "\n", encoding="utf-8")
    try:
        os.chmod(temp, 0o600)
    except OSError:
        pass
    os.replace(temp, path)


def _persist(force: bool = False) -> None:
    global _LAST_PERSIST_MS
    now = _now_ms()
    if not force and now - _LAST_PERSIST_MS < PERSIST_INTERVAL_MS:
        return
    try:
        _write_jobs([item.copy() for item in _JOBS.values()])
        _LAST_PERSIST_MS = now
    except (OSError, ImportError, TypeError, ValueError):
        pass


def restore_jobs() -> None:
    global _LAST_PERSIST_MS
    try:
        path = _jobs_path()
        if not path.exists():
            return
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ImportError, ValueError):
        return
    if not isinstance(value, list):
        return
    _JOBS.clear()
    now = _now_ms()
    for raw in value[-MAX_JOBS:]:
        if not isinstance(raw, dict) or not raw.get("id"):
            continue
        job = dict(raw)
        if job.get("status") not in _TERMINAL:
            job.update(
                status="interrupted",
                updatedAt=now,
                finishedAt=now,
                error={
                    "type": "RestartInterrupted",
                    "message": "ComfyUI restarted before this job reached a terminal state.",
                },
            )
        _JOBS[str(job["id"])] = job
    _LAST_PERSIST_MS = 0
    _trim()
    _persist(force=True)


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
    _persist(force=True)
    return job.copy()


def update_job(job_id: str, **changes: Any) -> dict[str, Any]:
    job = _JOBS.get(job_id)
    if job is None:
        raise KeyError("Unknown CUICommander job.")
    job.update(changes)
    job["updatedAt"] = _now_ms()
    _JOBS.move_to_end(job_id)
    _persist(force=job.get("status") in _TERMINAL)
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
    if task.cancelled() and job is not None and job.get("status") not in _TERMINAL:
        update_job(job_id, status="cancelled", finishedAt=_now_ms())
    _persist(force=True)


def cancel_job(job_id: str) -> dict[str, Any]:
    job = get_job(job_id)
    if job["status"] in _TERMINAL:
        return job
    task = _TASKS.get(job_id)
    if task is None:
        return update_job(job_id, status="cancelled", finishedAt=_now_ms())
    task.cancel()
    return update_job(job_id, status="cancelling")


def _trim() -> None:
    while len(_JOBS) > MAX_JOBS:
        job_id, _job = next(iter(_JOBS.items()))
        if job_id in _TASKS:
            _JOBS.move_to_end(job_id)
            if all(key in _TASKS for key in _JOBS):
                break
            continue
        _JOBS.pop(job_id, None)


def _reset_for_tests() -> None:
    global _LAST_PERSIST_MS
    for task in list(_TASKS.values()):
        task.cancel()
    _TASKS.clear()
    _JOBS.clear()
    _LAST_PERSIST_MS = 0

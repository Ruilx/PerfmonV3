"""Explicit task dispatch between Sources and Worker processes."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from src.core.protocol import JobRequest
from src.core.worker_handle import WorkerHandle


class WorkerState(StrEnum):
    STARTING = "starting"
    IDLE = "idle"
    BUSY = "busy"
    STOPPING = "stopping"
    DEAD = "dead"


@dataclass(slots=True)
class WorkerSlot:
    handle: WorkerHandle
    state: WorkerState = WorkerState.STARTING
    job_id: str | None = None


class Broker:
    """Keep pending/running jobs and assign them to idle Workers."""

    def __init__(self) -> None:
        self.workers: dict[str, WorkerSlot] = {}
        self.pending: deque[JobRequest] = deque()
        self.running: dict[str, JobRequest] = {}

    def register_worker(self, worker: WorkerHandle) -> None:
        if worker.worker_id in self.workers:
            raise ValueError(f"Worker '{worker.worker_id}' is already registered.")
        slot = WorkerSlot(worker)
        self.workers[worker.worker_id] = slot
        try:
            worker.start()
        except Exception:
            del self.workers[worker.worker_id]
            raise

    def unregister_worker(self, worker_id: str) -> None:
        slot = self.workers.pop(worker_id)
        if slot.job_id is not None:
            job = self.running.pop(slot.job_id, None)
            if job is not None:
                self.pending.appendleft(job)
        slot.handle.stop()
        slot.handle.join(5)
        slot.handle.close()

    def submit(self, job: JobRequest) -> None:
        if job.job_id in self.running or any(
            item.job_id == job.job_id for item in self.pending
        ):
            raise ValueError(f"Job '{job.job_id}' is already known to the Broker.")
        self.pending.append(job)
        self.dispatch()

    def dispatch(self) -> None:
        for slot in self.workers.values():
            if not self.pending:
                break
            if slot.state is not WorkerState.IDLE:
                continue

            job = self.pending.popleft()
            try:
                slot.handle.send_job(job)
            except RuntimeError:
                slot.state = WorkerState.DEAD
                self.pending.appendleft(job)
                continue
            slot.state = WorkerState.BUSY
            slot.job_id = job.job_id
            self.running[job.job_id] = job

    def poll(self, timeout: float = 0.0) -> tuple[dict[str, Any], ...]:
        """Collect Worker events and dispatch newly available jobs."""

        events: list[dict[str, Any]] = []
        first_worker = True
        for slot in tuple(self.workers.values()):
            wait = timeout if first_worker else 0.0
            first_worker = False
            event = slot.handle.poll_event(wait)
            while event is not None:
                events.append(event)
                self._apply_event(event)
                event = slot.handle.poll_event(0.0)

        self.dispatch()
        return tuple(events)

    def stop_all(self) -> None:
        for slot in self.workers.values():
            if slot.state not in {WorkerState.DEAD, WorkerState.STOPPING}:
                slot.state = WorkerState.STOPPING
                slot.handle.stop()

    def close(self) -> None:
        self.stop_all()
        for slot in tuple(self.workers.values()):
            slot.handle.join(5)
            slot.handle.close()
        self.workers.clear()

    def _apply_event(self, event: dict[str, Any]) -> None:
        worker_id = event.get("worker_id")
        slot = self.workers.get(worker_id)
        if slot is None:
            return

        event_type = event.get("type")
        if event_type == "worker_ready":
            slot.state = WorkerState.IDLE
            return
        if event_type == "job_started":
            slot.state = WorkerState.BUSY
            slot.job_id = event.get("job_id")
            return
        if event_type in {"job_finished", "job_failed"}:
            job_id = event.get("job_id")
            if job_id is not None:
                self.running.pop(job_id, None)
            slot.state = WorkerState.IDLE
            slot.job_id = None
            return
        if event_type == "worker_stopped":
            if slot.job_id is not None:
                job = self.running.pop(slot.job_id, None)
                if job is not None:
                    self.pending.appendleft(job)
            slot.state = WorkerState.DEAD
            slot.job_id = None

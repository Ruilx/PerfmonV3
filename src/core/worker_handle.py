"""Parent-side handle for a single spawned Worker process."""

from __future__ import annotations

from collections.abc import Callable
from multiprocessing import get_context
from multiprocessing.connection import Connection
from multiprocessing.process import BaseProcess
from typing import Any

from src.core.protocol import ErrorInfo, JobRequest, WorkerEvent
from src.core.worker_runtime import WorkerRuntime
from src.core.workflow_executor import WorkflowExecutor


ExecutorFactory = Callable[[], WorkflowExecutor]


class WorkerHandle:
    """Own a Worker process and its dedicated command/result Pipe."""

    def __init__(
        self,
        worker_id: str,
        executor_factory: ExecutorFactory,
        *,
        start_method: str = "spawn",
    ) -> None:
        if not worker_id:
            raise ValueError("worker_id is required.")
        self.worker_id = worker_id
        self._context = get_context(start_method)
        self._parent_connection, child_connection = self._context.Pipe(duplex=True)
        self._process: BaseProcess = self._context.Process(
            target=_worker_process_entry,
            args=(child_connection, worker_id, executor_factory),
            name=f"PerfmonWorker-{worker_id}",
        )
        self._child_connection = child_connection

    @property
    def process(self) -> BaseProcess:
        return self._process

    def start(self) -> None:
        self._process.start()
        self._child_connection.close()

    def send_job(self, job: JobRequest) -> None:
        if not self._process.is_alive():
            raise RuntimeError(f"Worker '{self.worker_id}' is not alive.")
        self._parent_connection.send(job.to_message())

    def poll_event(self, timeout: float | None = 0.0) -> dict[str, Any] | None:
        if timeout is None or self._parent_connection.poll(timeout):
            try:
                message = self._parent_connection.recv()
            except EOFError:
                return None
            if not isinstance(message, dict):
                raise TypeError("Worker event must be a dictionary.")
            return message
        return None

    def stop(self) -> None:
        if self._process.is_alive():
            self._parent_connection.send({"type": "stop"})

    def join(self, timeout: float | None = None) -> None:
        self._process.join(timeout)

    def close(self) -> None:
        self._parent_connection.close()
        if self._process.is_alive():
            self._process.terminate()
            self._process.join(5)


def _worker_process_entry(
    connection: Connection,
    worker_id: str,
    executor_factory: ExecutorFactory,
) -> None:
    try:
        executor = executor_factory()
        WorkerRuntime(worker_id, connection, executor).run()
    except Exception as error:
        try:
            connection.send(
                WorkerEvent(
                    "worker_stopped",
                    worker_id,
                    error=ErrorInfo.from_exception(error),
                ).to_message()
            )
        finally:
            connection.close()

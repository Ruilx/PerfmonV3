"""Child-process runtime for one Perfmon Worker."""

from __future__ import annotations

from multiprocessing.connection import Connection

from src.core.protocol import ErrorInfo, JobRequest, JobResult, WorkerEvent
from src.core.workflow_executor import WorkflowExecutor


class WorkerRuntime:
    """Receive commands from one Pipe and execute jobs serially."""

    def __init__(
        self,
        worker_id: str,
        connection: Connection,
        executor: WorkflowExecutor,
    ) -> None:
        self.worker_id = worker_id
        self.connection = connection
        self.executor = executor

    def run(self) -> None:
        self._send(WorkerEvent("worker_ready", self.worker_id))
        try:
            while True:
                try:
                    if not self.connection.poll(0.5):
                        continue
                    message = self.connection.recv()
                except EOFError:
                    break

                if not isinstance(message, dict):
                    raise ValueError("Worker command must be a dictionary.")

                message_type = message.get("type")
                if message_type == "stop":
                    self._send(WorkerEvent("worker_stopped", self.worker_id))
                    break
                if message_type != "job_request":
                    raise ValueError(f"Unknown worker command: {message_type!r}.")

                self._execute_job(JobRequest.from_message(message))
        finally:
            self.connection.close()

    def _execute_job(self, job: JobRequest) -> None:
        self._send(
            WorkerEvent(
                "job_started",
                self.worker_id,
                job_id=job.job_id,
                attempt=job.attempt,
            )
        )
        try:
            result = self.executor.execute(job)
        except Exception as error:
            result = JobResult(
                job_id=job.job_id,
                workflow=job.workflow,
                source=job.source,
                status="failed",
                error=ErrorInfo.from_exception(error),
                attempt=job.attempt,
                metadata=job.metadata,
            )

        event_name = "job_finished" if result.status == "succeeded" else "job_failed"
        self._send(
            WorkerEvent(
                event_name,
                self.worker_id,
                job_id=job.job_id,
                attempt=job.attempt,
                result=result,
                error=result.error,
            )
        )

    def _send(self, event: WorkerEvent) -> None:
        self.connection.send(event.to_message())

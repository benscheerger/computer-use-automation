import math
import time
from queue import Empty, Full, Queue
from threading import Lock
from types import TracebackType
from typing import Any, Literal


TakeoverCommand = Literal["resume", "cancel"]

TakeoverStatus = Literal[
    "human",
    "validating",
    "resumed",
    "cancelled",
    "timed_out",
    "failed",
]

FINISHED_STATUSES = {
    "resumed",
    "cancelled",
    "timed_out",
    "failed",
}


class ConsoleTakeover:
    def __init__(
        self,
        *,
        run_id: str,
        member_id: str,
        step: int,
        timeout_seconds: float,
        url: str,
    ):
        if timeout_seconds <= 0:
            raise ValueError("Takeover timeout must be positive.")

        self.run_id = run_id
        self.member_id = member_id
        self.step = step
        self.url = url
        self.deadline = time.monotonic() + timeout_seconds

        self._lock = Lock()
        self._commands: Queue[TakeoverCommand] = Queue(maxsize=1)
        self._status: TakeoverStatus = "human"
        self._message = (
            "Automation is paused. Repair the banking browser, "
            "then Resume or Cancel."
        )

    def __enter__(self) -> "ConsoleTakeover":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> Literal[False]:
        with self._lock:
            if self._status not in FINISHED_STATUSES:
                self._status = "failed"
                self._message = (
                    "Takeover ended. Review the replay result."
                )

        return False

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            remaining = max(
                0,
                math.ceil(self.deadline - time.monotonic()),
            )

            return {
                "run_id": self.run_id,
                "member_id": self.member_id,
                "step": self.step,
                "status": self._status,
                "message": self._message,
                "remaining_seconds": remaining,
                "can_command": (
                    self._status == "human"
                    and remaining > 0
                ),
            }

    def submit(
        self,
        command: TakeoverCommand,
        *,
        run_id: str,
        step: int,
    ) -> bool:
        with self._lock:
            if (
                command not in {"resume", "cancel"}
                or run_id != self.run_id
                or step != self.step
                or self._status != "human"
                or time.monotonic() >= self.deadline
            ):
                return False

            try:
                self._commands.put_nowait(command)
            except Full:
                return False

            self._status = "validating"
            self._message = (
                "Checking the resume checkpoint."
                if command == "resume"
                else "Cancellation requested."
            )

        return True

    def poll_command(self) -> TakeoverCommand | None:
        try:
            return self._commands.get_nowait()
        except Empty:
            return None

    def set_status(
        self,
        status: TakeoverStatus,
        message: str,
    ) -> None:
        with self._lock:
            self._status = status
            self._message = message
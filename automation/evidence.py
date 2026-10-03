import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from typing import Literal, TextIO

from automation.actions import StrictModel


EventName = Literal[
    "run_started",
    "model_requested",
    "action_proposed",
    "step_started",
    "step_completed",
    "checkpoint_passed",
    "verification_started",
    "verification_passed",
    "capability_saved",
    "run_completed",
    "run_failed",
    "member_not_found",
    "failure_evidence_saved",
    "failure_evidence_unavailable",
    "recovery_started",
    "recovery_completed",
    "recovery_exhausted",
    "handoff_started",
    "manual_action",
    "manual_recording_limit",
    "handoff_resume_rejected",
    "handoff_resumed",
    "handoff_cancelled",
    "handoff_timed_out",
    "handoff_ended",
]

ActionKind = Literal[
    "fill",
    "click",
    "click_button",
    "click_link",
    "finish",
]

class HumanAction(StrictModel):
    kind: Literal["click", "input", "change"]
    target: Literal[
        "member_id_field",
        "search_button",
        "savings_link",
        "dismiss_notice_button",
        "manual_resolution_button",
        "other",
    ]

class EvidenceEvent(StrictModel):
    schema_version: Literal["1.0"]
    timestamp: str
    elapsed_ms: int
    run_id: str
    mode: Literal["discovery", "replay"]
    source_run_id: str | None
    event: EventName
    step: int | None
    action: ActionKind | None
    error_type: str | None
    human_action: HumanAction | None = None


class RunLog:
    def __init__(
        self,
        directory: Path,
        mode: Literal["discovery", "replay"],
        source_run_id: str | None = None,
    ):
        self.run_id = str(uuid4())
        self.path = directory / f"{self.run_id}.jsonl"
        self.mode: Literal["discovery", "replay"] = mode
        self.source_run_id = source_run_id

        self._file: TextIO | None = None
        self._started_at = 0.0
        self._step: int | None = None
        self._action: ActionKind | None = None
        self._failure_error_type: str | None = None

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._file = self.path.open("x", encoding="utf-8")
        self._started_at = time.monotonic()

        try:
            self.emit("run_started")
        except BaseException:
            self._file.close()
            raise

        return self

    def emit(
        self,
        event: EventName,
        *,
        step: int | None = None,
        action: ActionKind | None = None,
        error_type: str | None = None,
        human_action: HumanAction | None = None,
    ) -> None:
        if self._file is None or self._file.closed:
            raise RuntimeError("The evidence log is not open.")

        entry = EvidenceEvent(
            schema_version="1.0",
            timestamp=datetime.now(timezone.utc).isoformat(),
            elapsed_ms=int(
                (time.monotonic() - self._started_at) * 1000
            ),
            run_id=self.run_id,
            mode=self.mode,
            source_run_id=self.source_run_id,
            event=event,
            step=step,
            action=action,
            error_type=error_type,
            human_action=human_action,
        )

        self._file.write(entry.model_dump_json() + "\n")
        self._file.flush()

        self._step = step
        self._action = action

    def __exit__(self, exc_type, exc_value, traceback):
        file = self._file

        if file is None:
            raise RuntimeError("The evidence log is not open.")

        error_type = (
            exc_type.__name__
            if exc_type is not None
            else self._failure_error_type
        )

        try:
            if error_type is None:
                self.emit("run_completed")
            else:
                self.emit(
                    "run_failed",
                    step=self._step,
                    action=self._action,
                    error_type=error_type,
                )
        finally:
            file.close()

        return False
    
    def mark_failed(
        self,
        *,
        error_type: str,
        step: int | None,
        action: ActionKind | None,
    ) -> None:
        self._failure_error_type = error_type
        self._step = step
        self._action = action
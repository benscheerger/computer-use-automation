from __future__ import annotations

import math
import secrets
import time
from pathlib import Path
from queue import Empty, Full, Queue
from threading import Event, Lock, Thread
from typing import Any, Literal, cast

from flask import (
    Flask,
    Response,
    abort,
    jsonify,
    render_template,
    request,
)
from werkzeug.serving import WSGIRequestHandler, make_server


OperatorCommand = Literal["resume", "cancel"]

PanelStatus = Literal[
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


class QuietRequestHandler(WSGIRequestHandler):
    def log(
        self,
        type: str,
        message: str,
        *args: Any,
    ) -> None:
        pass


class OperatorPanel:
    def __init__(
        self,
        *,
        run_id: str,
        member_id: str,
        step: int,
        timeout_seconds: float,
    ):
        self.run_id = run_id
        self.member_id = member_id
        self.step = step
        self.deadline = time.monotonic() + timeout_seconds

        self._token = secrets.token_hex(32)
        self._lock = Lock()
        self._commands: Queue[OperatorCommand] = Queue(maxsize=1)
        self._finished_seen = Event()

        self._status: PanelStatus = "human"
        self._message = (
            "Automation is paused. Resolve the notice in the "
            "banking browser, then request resume."
        )

        template_directory = (
            Path(__file__).resolve().parent / "templates"
        )

        app = Flask(
            __name__,
            template_folder=str(template_directory),
            static_folder=None,
        )
        app.config["MAX_CONTENT_LENGTH"] = 1024

        @app.before_request
        def check_host() -> None:
            if request.host != self._host:
                abort(403)

        @app.after_request
        def response_headers(response: Response) -> Response:
            response.headers["Cache-Control"] = "no-store"
            response.headers["X-Frame-Options"] = "DENY"
            return response

        def require_token() -> None:
            supplied = request.headers.get("X-Operator-Token", "")

            if not secrets.compare_digest(supplied, self._token):
                abort(403)

        @app.get("/")
        def index() -> str:
            return render_template(
                "operator_panel.html",
                token=self._token,
            )

        @app.get("/api/state")
        def state() -> Response:
            require_token()
            snapshot = self.snapshot()

            if snapshot["finished"]:
                self._finished_seen.set()

            return jsonify(snapshot)

        @app.post("/api/command")
        def command() -> tuple[Response, int]:
            require_token()

            if request.headers.get("Origin") != self.url:
                abort(403)

            body = request.get_json(silent=True)

            if (
                not isinstance(body, dict)
                or set(body) != {"command"}
                or body["command"] not in {"resume", "cancel"}
            ):
                abort(400)

            requested = cast(OperatorCommand, body["command"])

            if not self._submit(requested):
                return jsonify(
                    {"error": "A command cannot be accepted now."}
                ), 409

            return jsonify(self.snapshot()), 202

        # Port 0 selects an available local port.
        self._server = make_server(
            "127.0.0.1",
            0,
            app,
            threaded=True,
            request_handler=QuietRequestHandler,
        )

        self._host = f"127.0.0.1:{self._server.server_port}"
        self.url = f"http://{self._host}"

        self._thread = Thread(
            target=self._server.serve_forever,
            daemon=True,
            name="operator-panel",
        )

    def __enter__(self) -> OperatorPanel:
        self._thread.start()
        return self

    def snapshot(self) -> dict[str, object]:
        with self._lock:
            status = self._status
            message = self._message

        if status in {"human", "validating"}:
            owner = "human"
        elif status == "resumed":
            owner = "automation"
        else:
            owner = "none"

        return {
            "run_id": self.run_id,
            "member_id": self.member_id,
            "step": self.step,
            "status": status,
            "owner": owner,
            "message": message,
            "remaining_seconds": max(
                0,
                math.ceil(self.deadline - time.monotonic()),
            ),
            "can_command": status == "human",
            "finished": status in FINISHED_STATUSES,
        }

    def _submit(self, command: OperatorCommand) -> bool:
        with self._lock:
            if self._status != "human":
                return False

            try:
                self._commands.put_nowait(command)
            except Full:
                return False

            self._status = "validating"
            self._message = (
                "Checking the browser checkpoint."
                if command == "resume"
                else "Cancelling takeover."
            )

        return True

    def poll_command(self) -> OperatorCommand | None:
        try:
            return self._commands.get_nowait()
        except Empty:
            return None

    def set_status(
        self,
        status: PanelStatus,
        message: str,
    ) -> None:
        with self._lock:
            self._status = status
            self._message = message

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        with self._lock:
            if self._status not in FINISHED_STATUSES:
                self._status = "failed"
                self._message = (
                    "Takeover ended before a validated resume. "
                    "Check the terminal result."
                )

        # Give the page a brief opportunity to display the final
        # takeover status before shutting down the local server.
        self._finished_seen.wait(timeout=1)

        try:
            self._server.shutdown()
        finally:
            self._server.server_close()
            self._thread.join(timeout=1)

        return False
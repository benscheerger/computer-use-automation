import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

from automation.actions import StrictModel
from automation.handoff import TakeoverPanelFactory
from automation.capability import Capability, MemberLookupInputs
from automation.evidence import RunLog
from automation.network import install_request_guard
from automation.replay import run_replay
from automation.results import ReplayResult
from demo_app.server import DemoServer


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CAPABILITY_DIRECTORY = (
    PROJECT_ROOT / "evidence" / "capabilities"
)


def capability_paths() -> dict[str, Path]:
    directory = CAPABILITY_DIRECTORY.resolve()
    paths: dict[str, Path] = {}

    for path in directory.glob("*.json"):
        resolved = path.resolve()

        if resolved.is_file() and resolved.parent == directory:
            paths[path.stem] = resolved

    return paths


def list_capabilities() -> list[dict[str, str]]:
    paths = capability_paths()

    ordered_ids = sorted(
        paths,
        key=lambda name: (
            name != "get_savings_balance",
            -paths[name].stat().st_mtime,
        ),
    )

    return [
        {
            "id": capability_id,
            "label": (
                "Latest saved capability"
                if capability_id == "get_savings_balance"
                else capability_id
            ),
        }
        for capability_id in ordered_ids
    ]


def load_saved_capability(capability_id: str) -> Capability:
    path = capability_paths().get(capability_id)

    if path is None:
        raise ValueError("Unknown saved capability.")

    artifact_data: Any = json.loads(
        path.read_text(encoding="utf-8")
    )

    required_metadata = {"schema_version", "output_type"}

    if (
        not isinstance(artifact_data, dict)
        or not required_metadata.issubset(artifact_data)
    ):
        raise ValueError(
            "Artifact is missing required contract metadata."
        )

    return Capability.model_validate(artifact_data)


class ReplayJobResult(StrictModel):
    run_id: str
    dataset_id: str
    capability_id: str
    replay_result: ReplayResult


def replay_capability(
    inputs: MemberLookupInputs,
    *,
    dataset_id: str,
    capability_id: str,
    on_run_started: Callable[[str], None] | None = None,
    notice_mode: str = "off",
    allow_human_takeover: bool = False,
    panel_factory: TakeoverPanelFactory | None = None,
) -> ReplayJobResult:
    capability = load_saved_capability(capability_id)

    with RunLog(
        directory=PROJECT_ROOT / "evidence" / "runs",
        mode="replay",
        source_run_id=capability.source_run_id,
        dataset_id=dataset_id,
    ) as log:
        if on_run_started is not None:
            on_run_started(log.run_id)

        print(f"Evidence log: {log.path}")
        print(f"Replaying: {capability.name}")
        print(f"Dataset: {dataset_id}")
        print(f"Member: {inputs.member_id}")

        with DemoServer(
            dataset_id=dataset_id,
            notice_mode=notice_mode,
        ) as demo:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(
                    headless=False,
                    slow_mo=300,
                )

                try:
                    context = browser.new_context(
                        service_workers="block"
                    )
                    blocked_requests = install_request_guard(
                        context
                    )

                    page = context.new_page()
                    page.set_default_timeout(5000)

                    result = run_replay(
                        page=page,
                        capability=capability,
                        inputs=inputs,
                        blocked_requests=blocked_requests,
                        base_url=demo.url,
                        log=log,
                        allow_human_takeover=allow_human_takeover,
                        panel_factory=panel_factory,
                    )

                    return ReplayJobResult(
                        run_id=log.run_id,
                        dataset_id=dataset_id,
                        capability_id=capability_id,
                        replay_result=result,
                    )

                finally:
                    browser.close()
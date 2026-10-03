from pathlib import Path
from typing import Literal
from collections.abc import Callable

from dotenv import load_dotenv
from openai import OpenAI
from playwright.sync_api import sync_playwright

from automation.actions import StrictModel
from automation.capability import Capability
from automation.discovery import run_discovery
from automation.evidence import RunLog
from automation.network import install_request_guard
from automation.planner import MODEL
from automation.policy import PolicyViolation, check_url
from automation.task import DiscoveryTask
from automation.verification import BalanceResult, verify_balance
from demo_app.server import DemoServer


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class DiscoveryJobResult(StrictModel):
    status: Literal["success"] = "success"
    run_id: str
    dataset_id: str
    capability_id: str
    model_summary: str
    outputs: BalanceResult


def discover_capability(
    task: DiscoveryTask,
    *,
    dataset_id: str,
    on_run_started: Callable[[str], None] | None = None,
) -> DiscoveryJobResult:
    key_file = (
        Path.home()
        / ".config"
        / "computer-use-automation"
        / ".env"
    )
    load_dotenv(key_file, override=True)

    inputs = task.inputs
    account_type = "savings"

    goal = (
        f"Task: {task.goal}\n"
        f"Target member ID: {inputs.member_id}\n"
        f"Account type: {account_type}."
    )

    with RunLog(
        directory=PROJECT_ROOT / "evidence" / "runs",
        mode="discovery",
        dataset_id=dataset_id,
    ) as log:
        
        if on_run_started is not None:
            on_run_started(log.run_id)

        print(f"Evidence log: {log.path}")
        print(f"Dataset: {dataset_id}")
        print(f"Model: {MODEL}")

        with DemoServer(
            dataset_id=dataset_id,
            notice_mode="off",
        ) as demo:
            with OpenAI(
                timeout=30.0,
                max_retries=0,
            ) as client:
                with sync_playwright() as playwright:
                    browser = playwright.chromium.launch(
                        headless=False
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

                        check_url(demo.url)
                        page.goto(demo.url)

                        discovery = run_discovery(
                            client=client,
                            page=page,
                            goal=goal,
                            inputs=inputs,
                            blocked_requests=blocked_requests,
                            log=log,
                            max_steps=8,
                        )

                        log.emit("verification_started")

                        result = verify_balance(
                            page=page,
                            expected_member_id=inputs.member_id,
                            expected_account_type=account_type,
                        )

                        if blocked_requests:
                            raise PolicyViolation(
                                blocked_requests[-1]
                            )

                        log.emit("verification_passed")

                        capability = Capability(
                            source_run_id=discovery.run_id,
                            steps=discovery.steps,
                        )

                        capability_directory = (
                            PROJECT_ROOT
                            / "evidence"
                            / "capabilities"
                        )
                        capability_directory.mkdir(
                            parents=True,
                            exist_ok=True,
                        )

                        capability_id = (
                            f"get_savings_balance_{log.run_id}"
                        )

                        serialized = (
                            capability.model_dump_json(indent=2)
                            + "\n"
                        )

                        # Preserve the artifact belonging to this run.
                        artifact_path = (
                            capability_directory
                            / f"{capability_id}.json"
                        )

                        with artifact_path.open(
                            "x",
                            encoding="utf-8",
                        ) as file:
                            file.write(serialized)

                        # Preserve the existing replay default.
                        latest_path = (
                            capability_directory
                            / "get_savings_balance.json"
                        )
                        latest_path.write_text(
                            serialized,
                            encoding="utf-8",
                        )

                        log.emit("capability_saved")

                        print("\nModel summary:")
                        print(discovery.finish.summary)
                        print(f"\nSaved capability: {artifact_path}")

                        return DiscoveryJobResult(
                            run_id=log.run_id,
                            dataset_id=dataset_id,
                            capability_id=capability_id,
                            model_summary=discovery.finish.summary,
                            outputs=result,
                        )
                    finally:
                        browser.close()
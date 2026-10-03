from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from playwright.sync_api import sync_playwright

from automation.capability import Capability, MemberLookupInputs
from automation.discovery import run_discovery
from automation.evidence import RunLog
from automation.network import install_request_guard
from automation.planner import MODEL
from automation.policy import PolicyViolation, check_url
from automation.verification import verify_balance


def main():
    key_file = (
        Path.home()
        / ".config"
        / "computer-use-automation"
        / ".env"
    )
    load_dotenv(key_file, override=True)

    inputs = MemberLookupInputs(member_id="DEMO-101")
    account_type = "savings"

    goal = (
        f"Find member {inputs.member_id} and return their {account_type} "
        "account's available balance and currency."
    )
    start_url = "http://127.0.0.1:8000/"

    project_root = Path(__file__).resolve().parents[1]

    with RunLog(
        directory=project_root / "evidence" / "runs",
        mode="discovery",
    ) as log:
        print(f"Evidence log: {log.path}")
        print(f"Model: {MODEL}")

        with OpenAI(timeout=30.0, max_retries=0) as client:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=False)

                try:
                    context = browser.new_context(
                        service_workers="block"
                    )
                    blocked_requests = install_request_guard(context)

                    page = context.new_page()
                    page.set_default_timeout(5000)

                    check_url(start_url)
                    page.goto(start_url)

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
                        raise PolicyViolation(blocked_requests[-1])

                    log.emit("verification_passed")

                    capability = Capability(
                        source_run_id=discovery.run_id,
                        steps=discovery.steps,
                    )

                    artifact_path = (
                        project_root
                        / "evidence"
                        / "capabilities"
                        / "get_savings_balance.json"
                    )
                    artifact_path.parent.mkdir(
                        parents=True,
                        exist_ok=True,
                    )
                    artifact_path.write_text(
                        capability.model_dump_json(indent=2) + "\n",
                        encoding="utf-8",
                    )

                    log.emit("capability_saved")

                    print("\nModel summary:")
                    print(discovery.finish.summary)

                    print("\nVerified result:")
                    print(result.model_dump_json(indent=2))

                    print(f"\nSaved capability: {artifact_path}")

                finally:
                    browser.close()


if __name__ == "__main__":
    main()
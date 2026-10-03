import argparse
from pathlib import Path

from playwright.sync_api import sync_playwright

from automation.capability import Capability, MemberLookupInputs
from automation.network import install_request_guard
from automation.replay import run_replay


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--member-id", required=True)
    args = parser.parse_args()

    inputs = MemberLookupInputs(member_id=args.member_id)

    project_root = Path(__file__).resolve().parents[1]
    artifact_path = (
        project_root
        / "evidence"
        / "capabilities"
        / "get_savings_balance.json"
    )

    capability = Capability.model_validate_json(
        artifact_path.read_text(encoding="utf-8")
    )

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=False,
            slow_mo=300,
        )

        try:
            context = browser.new_context(service_workers="block")
            blocked_requests = install_request_guard(context)

            page = context.new_page()
            page.set_default_timeout(5000)

            print(f"Replaying: {capability.name}")
            print(f"Member: {inputs.member_id}")

            result = run_replay(
                page=page,
                capability=capability,
                inputs=inputs,
                blocked_requests=blocked_requests,
                base_url="http://127.0.0.1:8000/",
            )

            print("\nVerified replay result:")
            print(result.model_dump_json(indent=2))

        finally:
            browser.close()


if __name__ == "__main__":
    main()
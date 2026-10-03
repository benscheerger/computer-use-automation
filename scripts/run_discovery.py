from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from playwright.sync_api import sync_playwright

from automation.network import install_request_guard
from automation.discovery import run_discovery
from automation.planner import MODEL
from automation.policy import check_url

from automation.policy import PolicyViolation
from automation.verification import verify_balance


def main():
    key_file = (
        Path.home()
        / ".config"
        / "computer-use-automation"
        / ".env"
    )
    load_dotenv(key_file, override=True)

    member_id = "DEMO-101"
    account_type = "savings"

    goal = (
        f"Find member {member_id} and return their {account_type} "
        "account's available balance and currency."
    )
    
    start_url = "http://127.0.0.1:8000/"

    with OpenAI(timeout=30.0, max_retries=0) as client:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=False)

            try:
                context = browser.new_context(service_workers="block")
                blocked_requests = install_request_guard(context)

                page = context.new_page()
                page.set_default_timeout(5000)

                check_url(start_url)
                page.goto(start_url)
                print(f"Model: {MODEL}")

                finish = run_discovery(
                    client=client,
                    page=page,
                    goal=goal,
                    blocked_requests=blocked_requests,
                    max_steps=8,
                )

                result = verify_balance(
                    page=page,
                    expected_member_id=member_id,
                    expected_account_type=account_type,
                )

                if blocked_requests:
                    raise PolicyViolation(blocked_requests[-1])

                print("\nModel summary:")
                print(finish.summary)

                print("\nVerified result:")
                print(result.model_dump_json(indent=2))

            finally:
                browser.close()


if __name__ == "__main__":
    main()
from playwright.sync_api import sync_playwright

from automation.actions import ClickAction, FillAction
from automation.business_outcomes import detect_member_not_found
from automation.executor import execute_action
from automation.network import install_request_guard


def search_member(page, member_id):
    execute_action(
        page,
        FillAction(
            kind="fill",
            label="Member ID",
            value=member_id,
        ),
    )
    execute_action(
        page,
        ClickAction(
            kind="click",
            role="button",
            name="Search",
        ),
    )


def main():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)

        try:
            context = browser.new_context(service_workers="block")
            blocked_requests = install_request_guard(context)

            page = context.new_page()
            page.set_default_timeout(5000)
            page.goto("http://127.0.0.1:8000/")

            search_member(page, "DEMO-202")

            assert detect_member_not_found(page, "DEMO-202") is None
            print("Existing member correctly has no missing-member outcome.")

            search_member(page, "DEMO-999")

            outcome = detect_member_not_found(page, "DEMO-999")

            assert outcome is not None
            assert outcome.status == "member_not_found"
            assert outcome.member_id == "DEMO-999"
            assert not blocked_requests

            print("Missing member correctly detected:")
            print(outcome.model_dump_json(indent=2))

        finally:
            browser.close()


if __name__ == "__main__":
    main()
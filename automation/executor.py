from urllib.parse import urljoin

from playwright.sync_api import Page

from automation.actions import ClickAction, FillAction
from automation.policy import PolicyViolation, check_action, check_url


def execute_action(
    page: Page,
    action: FillAction | ClickAction,
) -> None:
    check_url(page.url)
    check_action(action)

    if isinstance(action, FillAction):
        page.get_by_label(
            action.label,
            exact=True,
        ).fill(action.value)

    elif isinstance(action, ClickAction):
        target = page.get_by_role(
            action.role,
            name=action.name,
            exact=True,
        )

        if action.role == "link":
            href = target.get_attribute("href")

            if href is None:
                raise PolicyViolation("Link has no inspectable destination.")

            destination = urljoin(page.url, href)
            check_url(destination)

        target.click()
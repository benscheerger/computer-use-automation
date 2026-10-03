from urllib.parse import urljoin, urlsplit

from playwright.sync_api import Page

from automation.actions import (
    BrowserAction,
    ClickAction,
    FillAction,
    LinkClickAction,
)
from automation.capability import (
    Capability,
    MemberLookupInputs,
    RecordedButtonClick,
    RecordedFill,
    RecordedLinkClick,
)
from automation.executor import execute_action
from automation.observation import observe_page
from automation.policy import PolicyViolation, check_url
from automation.verification import BalanceResult, verify_balance


class ReplayError(Exception):
    """Replay did not reach an expected state."""


def resolve_action(
    action: RecordedFill | RecordedButtonClick | RecordedLinkClick,
    inputs: MemberLookupInputs,
) -> BrowserAction:
    if isinstance(action, RecordedFill):
        return FillAction(
            kind="fill",
            label=action.label,
            value=action.value.resolve(inputs),
        )

    if isinstance(action, RecordedButtonClick):
        return ClickAction(
            kind="click",
            role="button",
            name=action.name,
        )

    if isinstance(action, RecordedLinkClick):
        return LinkClickAction(
            kind="click_link",
            href=action.href.resolve(inputs),
        )

    raise ReplayError("Unsupported recorded action.")


def run_replay(
    page: Page,
    capability: Capability,
    inputs: MemberLookupInputs,
    blocked_requests: list[str],
    base_url: str,
) -> BalanceResult:
    start_url = urljoin(base_url, capability.start_path)
    check_url(start_url)
    page.goto(start_url)

    if blocked_requests:
        raise PolicyViolation(blocked_requests[-1])

    for index, step in enumerate(capability.steps, start=1):
        action = resolve_action(step.action, inputs)
        execute_action(page, action)

        observation = observe_page(page)

        if blocked_requests:
            raise PolicyViolation(blocked_requests[-1])

        check_url(observation["url"])

        actual_path = urlsplit(observation["url"]).path
        expected_path = step.checkpoint.expected_path.resolve(inputs)

        if actual_path != expected_path:
            raise ReplayError(
                f"Checkpoint failed after step {index}: "
                "the page path did not match the recorded expectation."
            )

        print(
            f"Step {index}/{len(capability.steps)}: "
            f"{action.kind} — checkpoint passed"
        )

    # Capability v1 supports only the savings-balance verifier.
    result = verify_balance(
        page=page,
        expected_member_id=inputs.member_id,
        expected_account_type="savings",
    )

    if blocked_requests:
        raise PolicyViolation(blocked_requests[-1])

    return result
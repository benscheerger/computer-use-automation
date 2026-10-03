from openai import OpenAI
from playwright.sync_api import Page

from automation.actions import FinishAction
from automation.executor import execute_action
from automation.observation import observe_page
from automation.planner import propose_action
from automation.policy import PolicyViolation


def run_discovery(
    client: OpenAI,
    page: Page,
    goal: str,
    blocked_requests: list[str],
    max_steps: int = 8,
) -> FinishAction:
    if max_steps < 1:
        raise ValueError("max_steps must be at least 1.")

    for step in range(1, max_steps + 1):
        observation = observe_page(page)

        if blocked_requests:
            raise PolicyViolation(blocked_requests[-1])

        request = propose_action(
            client=client,
            goal=goal,
            observation=observation,
        )
        action = request.action

        print(f"\nStep {step}/{max_steps}")
        print(action.model_dump_json(indent=2))

        if isinstance(action, FinishAction):
            return action

        execute_action(page, action)

        if blocked_requests:
            raise PolicyViolation(blocked_requests[-1])

    raise RuntimeError(
        f"Discovery reached its limit of {max_steps} steps "
        "without a finish proposal."
    )
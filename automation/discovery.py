from dataclasses import dataclass
from urllib.parse import urlsplit
from uuid import uuid4

from openai import OpenAI
from playwright.sync_api import Page

from automation.actions import FinishAction
from automation.capability import (
    CapabilityStep,
    MemberLookupInputs,
    PageCheckpoint,
)
from automation.executor import execute_action
from automation.observation import observe_page
from automation.planner import propose_action
from automation.policy import PolicyViolation, check_url
from automation.recording import parameterize_path, record_action


@dataclass
class DiscoveryRun:
    run_id: str
    finish: FinishAction
    steps: list[CapabilityStep]


def run_discovery(
    client: OpenAI,
    page: Page,
    goal: str,
    inputs: MemberLookupInputs,
    blocked_requests: list[str],
    max_steps: int = 8,
) -> DiscoveryRun:
    if max_steps < 1:
        raise ValueError("max_steps must be at least 1.")

    run_id = str(uuid4())
    recorded_steps: list[CapabilityStep] = []

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
            return DiscoveryRun(
                run_id=run_id,
                finish=action,
                steps=recorded_steps,
            )

        # Capture the target while we are still on the original page.
        recorded_action = record_action(page, action, inputs)

        execute_action(page, action)

        # Observe the actual state reached after execution.
        after = observe_page(page)

        if blocked_requests:
            raise PolicyViolation(blocked_requests[-1])

        check_url(after["url"])

        checkpoint = PageCheckpoint(
            expected_path=parameterize_path(
                urlsplit(after["url"]).path,
                inputs,
            )
        )

        recorded_steps.append(
            CapabilityStep(
                action=recorded_action,
                checkpoint=checkpoint,
            )
        )

    raise RuntimeError(
        f"Discovery reached its limit of {max_steps} steps "
        "without a finish proposal."
    )
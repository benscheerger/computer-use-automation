import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field

from automation.actions import (
    BrowserAction,
    ClickAction,
    FillAction,
    LinkClickAction,
    StrictModel,
)


class PolicyViolation(Exception):
    """The requested operation is outside the permitted workflow."""


class AllowedOrigin(StrictModel):
    scheme: Literal["http", "https"]
    host: str = Field(min_length=1)
    port: int = Field(ge=1, le=65535)


class PolicyConfig(StrictModel):
    allowed_origins: list[AllowedOrigin]
    allowed_path_patterns: list[str]
    allowed_methods: list[
        Literal["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    ]
    allowed_action_kinds: list[
        Literal["fill", "click", "click_link"]
    ]
    allowed_fill_labels: list[str]
    allowed_button_names: list[str]
    blocked_risky_button_names: list[str]


@dataclass(frozen=True)
class LoadedPolicy:
    config: PolicyConfig
    path_patterns: tuple[re.Pattern[str], ...]


def load_policy(path: Path) -> LoadedPolicy:
    config = PolicyConfig.model_validate_json(
        path.read_text(encoding="utf-8")
    )

    try:
        patterns = tuple(
            re.compile(pattern)
            for pattern in config.allowed_path_patterns
        )
    except re.error as error:
        raise ValueError("Invalid policy path pattern.") from error

    return LoadedPolicy(
        config=config,
        path_patterns=patterns,
    )


DEFAULT_POLICY_PATH = (
    Path(__file__).resolve().parents[1]
    / "config"
    / "policy.json"
)

POLICY_PATH = Path(
    os.getenv("AUTOMATION_POLICY_FILE", str(DEFAULT_POLICY_PATH))
).expanduser()

DEFAULT_POLICY = load_policy(POLICY_PATH)


def check_url(
    url: str,
    policy: LoadedPolicy = DEFAULT_POLICY,
) -> None:
    try:
        parsed = urlsplit(url)
        port = parsed.port
    except ValueError as error:
        raise PolicyViolation("Destination URL is invalid.") from error

    if parsed.username is not None or parsed.password is not None:
        raise PolicyViolation("URLs containing credentials are blocked.")

    if port is None:
        port = {"http": 80, "https": 443}.get(parsed.scheme)

    origin = (parsed.scheme, parsed.hostname, port)

    allowed = any(
        origin == (
            candidate.scheme,
            candidate.host.lower(),
            candidate.port,
        )
        for candidate in policy.config.allowed_origins
    )

    if not allowed:
        raise PolicyViolation("Destination is outside the allowed origins.")

    if not any(
        pattern.fullmatch(parsed.path)
        for pattern in policy.path_patterns
    ):
        raise PolicyViolation("Destination path is not allowed.")


def check_request(
    url: str,
    method: str,
    policy: LoadedPolicy = DEFAULT_POLICY,
) -> None:
    check_url(url, policy)

    if method.upper() not in policy.config.allowed_methods:
        raise PolicyViolation("HTTP method is not allowed.")


def check_action(
    action: BrowserAction,
    policy: LoadedPolicy = DEFAULT_POLICY,
) -> None:
    config = policy.config

    if action.kind not in config.allowed_action_kinds:
        raise PolicyViolation("Action type is not allowed.")

    if isinstance(action, FillAction):
        if action.label not in config.allowed_fill_labels:
            raise PolicyViolation("Filling this field is not allowed.")

    elif isinstance(action, ClickAction):
        if action.role == "button":
            if action.name in config.blocked_risky_button_names:
                raise PolicyViolation("Risky button actions are blocked.")

            if action.name not in config.allowed_button_names:
                raise PolicyViolation("Clicking this button is not allowed.")

    elif isinstance(action, LinkClickAction):
        if not action.href.startswith("/") or action.href.startswith("//"):
            raise PolicyViolation(
                "Recorded links must use a root-relative destination."
            )

    else:
        raise PolicyViolation("Unsupported browser action.")
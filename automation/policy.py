import re
from urllib.parse import urlsplit

from automation.actions import ClickAction, FillAction


class PolicyViolation(Exception):
    """The requested action is outside the permitted workflow."""


ALLOWED_ORIGIN = ("http", "127.0.0.1", 8000)

ALLOWED_PATHS = (
    re.compile(r"/"),
    re.compile(r"/members/DEMO-\d+"),
    re.compile(r"/members/DEMO-\d+/accounts/[a-z]+"),
)

ALLOWED_FILL_LABELS = frozenset({"Member ID"})
ALLOWED_BUTTONS = frozenset({"Search"})


def check_url(url: str) -> None:
    parsed = urlsplit(url)
    origin = (parsed.scheme, parsed.hostname, parsed.port)

    if parsed.username is not None or parsed.password is not None:
        raise PolicyViolation("URLs containing credentials are blocked.")

    if origin != ALLOWED_ORIGIN:
        raise PolicyViolation("Destination is outside the allowed origin.")

    if not any(pattern.fullmatch(parsed.path) for pattern in ALLOWED_PATHS):
        raise PolicyViolation("Destination path is not allowed.")


def check_action(action: FillAction | ClickAction) -> None:
    if isinstance(action, FillAction):
        if action.label not in ALLOWED_FILL_LABELS:
            raise PolicyViolation("Filling this field is not allowed.")

    elif isinstance(action, ClickAction):
        if action.role == "button" and action.name not in ALLOWED_BUTTONS:
            raise PolicyViolation("Clicking this button is not allowed.")

    else:
        raise PolicyViolation("Unsupported browser action.")
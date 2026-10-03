import json
from pathlib import Path
from tempfile import TemporaryDirectory

from automation.actions import ClickAction
from automation.policy import (
    DEFAULT_POLICY_PATH,
    PolicyViolation,
    check_action,
    check_request,
    check_url,
    load_policy,
)


def assert_blocked(operation):
    try:
        operation()
    except PolicyViolation:
        return

    raise AssertionError("Expected the operation to be blocked.")


def main():
    search = ClickAction(
        kind="click",
        role="button",
        name="Search",
    )
    transfer = ClickAction(
        kind="click",
        role="button",
        name="Transfer",
    )

    check_action(search)
    check_request("http://127.0.0.1:8000/", "GET")

    assert_blocked(
        lambda: check_url("https://example.com/")
    )
    assert_blocked(
        lambda: check_request("http://127.0.0.1:8000/", "POST")
    )

    data = json.loads(
        DEFAULT_POLICY_PATH.read_text(encoding="utf-8")
    )
    data["allowed_button_names"] = ["Dismiss notice", "Transfer"]

    with TemporaryDirectory() as temporary_directory:
        path = Path(temporary_directory) / "policy.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        custom_policy = load_policy(path)

        # Search was removed from this configuration.
        assert_blocked(
            lambda: check_action(search, policy=custom_policy)
        )

        # Transfer is permitted by name but explicitly blocked as risky.
        assert_blocked(
            lambda: check_action(transfer, policy=custom_policy)
        )

    print("Configurable policy checks passed.")


if __name__ == "__main__":
    main()
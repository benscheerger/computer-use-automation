import json
import os
from pathlib import Path
from typing import Any

from flask import Flask, abort, render_template, request


DATA_DIRECTORY = Path(__file__).resolve().parent / "data"
NOTICE_MODES = {"off", "dismissible", "persistent"}


def dataset_paths() -> dict[str, Path]:
    directory = DATA_DIRECTORY.resolve()
    datasets: dict[str, Path] = {}

    for path in sorted(directory.glob("*.json")):
        resolved = path.resolve()

        if not resolved.is_file():
            continue

        # Dataset selections stay inside the demo data directory.
        if resolved.parent != directory:
            continue

        datasets[path.stem] = resolved

    return datasets


def list_datasets() -> list[dict[str, str]]:
    return [
        {
            "id": dataset_id,
            "label": dataset_id.replace("_", " ").title(),
        }
        for dataset_id in dataset_paths()
    ]


def get_dataset_path(dataset_id: str) -> Path:
    path = dataset_paths().get(dataset_id)

    if path is None:
        raise ValueError("Unknown demo dataset.")

    return path


def load_members(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as file:
        members = json.load(file)

    if not isinstance(members, dict):
        raise ValueError(
            "A demo dataset must contain a JSON object of member records."
        )

    return members


def create_app(
    dataset_id: str | None = None,
    notice_mode: str | None = None,
) -> Flask:
    selected_dataset = (
        dataset_id
        if dataset_id is not None
        else os.getenv("DEMO_DATASET", "members")
    )

    selected_notice_mode = (
        notice_mode
        if notice_mode is not None
        else os.getenv("DEMO_NOTICE", "off")
    )

    if selected_notice_mode not in NOTICE_MODES:
        raise ValueError("Unknown DEMO_NOTICE setting.")

    # Load once. Routes use these records for this app instance.
    members = load_members(
        get_dataset_path(selected_dataset)
    )

    app = Flask(__name__)

    app.config["DEMO_DATASET_ID"] = selected_dataset
    app.config["DEMO_NOTICE_MODE"] = selected_notice_mode

    @app.get("/")
    def search():
        member_id = request.args.get("member_id", "").strip()
        member = members.get(member_id)

        return render_template(
            "search.html",
            member_id=member_id,
            member=member,
        )

    @app.get("/members/<member_id>")
    def member_details(member_id: str):
        member = members.get(member_id)

        if member is None:
            abort(404)

        return render_template(
            "member.html",
            member_id=member_id,
            member=member,
            notice_mode=selected_notice_mode,
        )

    @app.get("/members/<member_id>/accounts/<account_type>")
    def account_details(
        member_id: str,
        account_type: str,
    ):
        member = members.get(member_id)

        if member is None:
            abort(404)

        account = member["accounts"].get(account_type)

        if account is None:
            abort(404)

        return render_template(
            "account.html",
            member_id=member_id,
            member=member,
            account_type=account_type,
            account=account,
        )

    return app
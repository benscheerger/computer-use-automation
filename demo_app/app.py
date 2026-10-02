import json
from pathlib import Path

from flask import Flask, abort, render_template, request

app = Flask(__name__)

DATA_PATH = Path(__file__).resolve().parent / "data" / "members.json"


def load_members(path: Path) -> dict:
    with path.open(encoding="utf-8") as file:
        return json.load(file)

MEMBERS = load_members(DATA_PATH)

# Search Functionality
@app.get("/")
def search():
    member_id = request.args.get("member_id", "").strip()
    member = MEMBERS.get(member_id)

    return render_template(
        "search.html",
        member_id=member_id,
        member=member,
    )

# Makes Member Details Page which can be clicked on from the search page
@app.get("/members/<member_id>")
def member_details(member_id):
    member = MEMBERS.get(member_id)

    if member is None:
        abort(404)

    return render_template(
        "member.html",
        member_id=member_id,
        member=member,
    )

# Account Details Page which can be clicked on from the member details page
@app.get("/members/<member_id>/accounts/<account_type>")
def account_details(member_id, account_type):
    member = MEMBERS.get(member_id)

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
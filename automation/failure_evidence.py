from pathlib import Path
from typing import Literal, get_args

from playwright.sync_api import Error as PlaywrightError, Page
from pydantic import Field, ValidationError

from automation.actions import StrictModel
from automation.evidence import RunLog
from automation.results import ReplayFailure


MAX_DOM_NODES = 200

DomTag = Literal[
    "body", "main", "section", "div", "span",
    "form", "label", "input", "button", "a",
    "h1", "h2", "h3", "p",
    "dl", "dt", "dd", "ul", "ol", "li",
    "table", "tbody", "tr", "th", "td",
    "iframe", "other",
]


class DomNode(StrictModel):
    index: int
    parent_index: int | None
    tag: DomTag
    has_layout_box: bool
    disabled: bool


class DomSnapshot(StrictModel):
    nodes: list[DomNode] = Field(max_length=MAX_DOM_NODES)
    truncated: bool


class KnownControls(StrictModel):
    member_id_fields: int
    search_buttons: int
    savings_links: int


class FailureEvidence(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    run_id: str
    source_run_id: str | None
    failure: ReplayFailure
    dom: DomSnapshot | None
    known_controls: KnownControls | None
    frame_count: int | None
    capture_error: Literal["snapshot_unavailable"] | None


DOM_CAPTURE = """
(body, options) => {
    const allowedTags = new Set(options.allowed_tags);
    const nodes = [];
    let truncated = false;

    function visit(element, parentIndex) {
        if (nodes.length >= options.limit) {
            truncated = true;
            return;
        }

        const index = nodes.length;
        const tag = element.tagName.toLowerCase();

        nodes.push({
            index: index,
            parent_index: parentIndex,
            tag: allowedTags.has(tag) ? tag : "other",
            has_layout_box: element.getClientRects().length > 0,
            disabled: element.matches(":disabled")
        });

        for (const child of element.children) {
            if (nodes.length >= options.limit) {
                truncated = true;
                break;
            }
            visit(child, index);
        }
    }

    visit(body, null);
    return {nodes: nodes, truncated: truncated};
}
"""


def save_failure_evidence(
    page: Page,
    log: RunLog,
    failure: ReplayFailure,
) -> Path:
    dom = None
    controls = None
    frame_count = None
    capture_error = None

    try:
        raw_structure = page.locator("body").evaluate(
            DOM_CAPTURE,
            arg={
                "limit": MAX_DOM_NODES,
                "allowed_tags": list(get_args(DomTag)),
            },
            timeout=2000,
        )

        dom = DomSnapshot.model_validate(raw_structure)

        controls = KnownControls(
            member_id_fields=page.get_by_label(
                "Member ID", exact=True
            ).count(),
            search_buttons=page.get_by_role(
                "button", name="Search", exact=True
            ).count(),
            savings_links=page.get_by_role(
                "link", name="Savings", exact=True
            ).count(),
        )

        frame_count = len(page.frames)

    except (PlaywrightError, ValidationError):
        dom = None
        controls = None
        frame_count = None
        capture_error = "snapshot_unavailable"

    evidence = FailureEvidence(
        run_id=log.run_id,
        source_run_id=log.source_run_id,
        failure=failure,
        dom=dom,
        known_controls=controls,
        frame_count=frame_count,
        capture_error=capture_error,
    )

    path = log.path.with_suffix(".failure.json")
    path.write_text(
        evidence.model_dump_json(indent=2) + "\n",
        encoding="utf-8",
    )

    return path
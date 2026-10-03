from typing import Annotated, Literal

from pydantic import Field

from automation.actions import StrictModel


class MemberLookupInputs(StrictModel):
    member_id: str = Field(pattern=r"^DEMO-[0-9]+$")


class LiteralText(StrictModel):
    kind: Literal["literal"]
    value: str


class InputReference(StrictModel):
    kind: Literal["input"]
    name: Literal["member_id"]


TextPart = Annotated[
    LiteralText | InputReference,
    Field(discriminator="kind"),
]


class TextTemplate(StrictModel):
    parts: list[TextPart] = Field(min_length=1)

    def resolve(self, inputs: MemberLookupInputs) -> str:
        pieces = []

        for part in self.parts:
            if isinstance(part, LiteralText):
                pieces.append(part.value)
            else:
                pieces.append(inputs.member_id)

        return "".join(pieces)


class PageCheckpoint(StrictModel):
    expected_path: TextTemplate


class RecordedFill(StrictModel):
    kind: Literal["fill"]
    label: str = Field(min_length=1)
    value: TextTemplate


class RecordedButtonClick(StrictModel):
    kind: Literal["click_button"]
    name: str = Field(min_length=1)


class RecordedLinkClick(StrictModel):
    kind: Literal["click_link"]
    href: TextTemplate


RecordedAction = Annotated[
    RecordedFill | RecordedButtonClick | RecordedLinkClick,
    Field(discriminator="kind"),
]


class CapabilityStep(StrictModel):
    action: RecordedAction
    checkpoint: PageCheckpoint


class Capability(StrictModel):
    schema_version: Literal["1.1"] = "1.1"
    name: Literal["get_savings_balance"] = "get_savings_balance"

    source_run_id: str = Field(min_length=1)
    start_path: Literal["/"] = "/"

    input_type: Literal["MemberLookupInputs"] = "MemberLookupInputs"
    output_type: Literal["ReplayResult"] = "ReplayResult"
    verifier: Literal["savings_balance_v1"] = "savings_balance_v1"

    steps: list[CapabilityStep] = Field(min_length=1)
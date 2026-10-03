from typing import Annotated, Literal

from pydantic import Field

from automation.actions import StrictModel
from automation.verification import BalanceResult


class ReplaySuccess(StrictModel):
    status: Literal["success"] = "success"
    outputs: BalanceResult


class ReplayBusinessOutcome(StrictModel):
    status: Literal["business_outcome"] = "business_outcome"
    code: Literal["member_not_found"]
    member_id: str
    step: int = Field(ge=1)

FailureCode = Literal[
    "policy_violation",
    "target_timeout",
    "checkpoint_mismatch",
    "verification_failed",
    "browser_error",
    "unsupported_action",
]

class ReplayFailure(StrictModel):
    status: Literal["failure"] = "failure"
    code: FailureCode
    step: int | None
    expected: str
    observed: str
    error_type: str


ReplayResult = Annotated[
    ReplaySuccess | ReplayBusinessOutcome | ReplayFailure,
    Field(discriminator="status"),
]
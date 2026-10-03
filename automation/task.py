from pydantic import Field, field_validator

from automation.actions import StrictModel
from automation.capability import MemberLookupInputs


class DiscoveryTask(StrictModel):
    goal: str = Field(min_length=1, max_length=1000)
    inputs: MemberLookupInputs

    @field_validator("goal")
    @classmethod
    def validate_goal(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Goal must not be blank.")

        return value
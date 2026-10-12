from typing import Literal, Optional

from pydantic import BaseModel, Field


ActionType = Literal[
    "click",
    "fill",
    "read",
    "wait",
    "finish",
    "escalate",
]


class ActionDecision(BaseModel):
    action: ActionType

    target_id: Optional[str] = None

    value_ref: Optional[str] = None

    extract_as: Optional[str] = None

    reason: str = Field(
        min_length=1,
        max_length=500,
    )


class ActionResult(BaseModel):
    status: Literal[
        "SUCCESS",
        "FAILURE",
        "SAFETY_BLOCKED",
        "HUMAN_INTERVENTION_REQUIRED",
    ]

    action: str

    target_id: Optional[str] = None

    extracted_value: Optional[str] = None

    extract_as: Optional[str] = None

    error: Optional[str] = None
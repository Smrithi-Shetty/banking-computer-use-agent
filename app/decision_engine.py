import json

from pydantic import ValidationError

from app.config import (
    AZURE_OPENAI_DEPLOYMENT,
)

from app.foundry_client import (
    get_client,
)

from app.models import (
    ActionDecision,
)


SYSTEM_INSTRUCTIONS = """
You are a computer-use discovery agent.

Choose exactly ONE next action.

Use only:

1. The goal
2. Current Outputs
3. Current Observation
4. Visible element IDs

GENERAL RULES

- Return exactly one JSON object.
- Never return a list.
- Never use Markdown or code fences.
- Never invent an element ID.
- Never invent account data.
- Never invent credentials.
- Never include literal registration values.
- Never repeat an output already present
  in Current Outputs.

ALLOWED RUNTIME REFERENCES

runtime_first_name
runtime_last_name
runtime_address
runtime_city
runtime_state
runtime_zip
runtime_phone
runtime_ssn
runtime_username
runtime_password

REGISTRATION MAPPING

First Name -> runtime_first_name
Last Name -> runtime_last_name
Address -> runtime_address
City -> runtime_city
State -> runtime_state
Zip Code -> runtime_zip
Phone -> runtime_phone
SSN -> runtime_ssn
Username -> runtime_username
Password -> runtime_password
Confirm Password -> runtime_password

ALLOWED ACTIONS

click
fill
read
wait
finish
escalate

ACTION RULES

For click:
- target_id is required.
- value_ref must be null.
- extract_as must be null.

For fill:
- target_id is required.
- value_ref must be an allowed
  runtime reference.
- Never fill an element where
  is_filled is true.
- extract_as must be null.

For read:
- target_id is required.
- target_id must identify a table_value
  or readable text element.
- extract_as is required.
- Read the actual value, not a label
  or table header.

For wait, finish, and escalate:
- target_id must be null.
- value_ref must be null.
- extract_as must be null.

PAGE STATE RULES

- If the page title is already
  "ParaBank | Accounts Overview",
  do not click Accounts Overview again.
- On Accounts Overview, begin extracting
  the account table immediately.
- Do not repeat navigation actions when the
  current page title already confirms the
  destination was reached.

ACCOUNT OVERVIEW OUTPUT CONTRACT

Required outputs:

1. account_number
2. total_balance
3. available_balance

SELECTION RULES

- account_number:
  choose the table_value whose
  column_header is "Account".

- total_balance:
  choose the table_value whose
  column_header is "Balance".

- available_balance:
  choose the table_value whose
  column_header is "Available Amount".

- Select only kind="table_value".
- Never select a header or label.
- Never extract the literal text
  "Available Amount".
- Extract the corresponding currency value.
- Never extract an output that already exists
  in Current Outputs.
- Choose finish only when all three required
  outputs exist in Current Outputs.

DYNAMIC JSON RESPONSE FORMAT

{
  "action": "",
  "target_id": "<visible element_id or null>",
  "value_ref": "<runtime reference or null>",
  "extract_as": "<business output or null>",
  "reason": "<short explanation>"
}

The angle-bracketed values describe the schema.
Select actual values dynamically from the
current page observation.
"""


def _clean_response(
    response_text: str,
) -> str:
    return (
        response_text
        .replace("```json", "")
        .replace("```", "")
        .strip()
    )


def _validate_decision_semantics(
    decision: ActionDecision,
) -> None:
    if decision.action in {
        "click",
        "fill",
        "read",
    }:
        if not decision.target_id:
            raise ValueError(
                f"{decision.action} "
                "requires target_id."
            )

    if decision.action == "fill":
        if not decision.value_ref:
            raise ValueError(
                "fill requires value_ref."
            )

        if decision.extract_as is not None:
            raise ValueError(
                "fill cannot use extract_as."
            )

    elif decision.value_ref is not None:
        raise ValueError(
            "value_ref is only valid for fill."
        )

    if decision.action == "read":
        if not decision.extract_as:
            raise ValueError(
                "read requires extract_as."
            )

    elif decision.extract_as is not None:
        raise ValueError(
            "extract_as is only valid for read."
        )


def decide_next_action(
    goal: str,
    observation: dict,
    outputs: dict,
) -> ActionDecision:
    client = get_client()

    prompt = f"""
{SYSTEM_INSTRUCTIONS}

GOAL

{goal}

CURRENT OUTPUTS

{json.dumps(outputs, indent=2)}

CURRENT OBSERVATION

{json.dumps(observation, indent=2)}

Return exactly one next action.
"""

    last_error: Exception | None = None

    for _ in range(2):
        response = client.responses.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            input=prompt,
        )

        response_text = _clean_response(
            response.output_text
        )

        try:
            parsed = json.loads(
                response_text
            )

            if isinstance(parsed, list):
                raise ValueError(
                    "The model returned a list."
                )

            decision = (
                ActionDecision.model_validate(
                    parsed
                )
            )

            _validate_decision_semantics(
                decision
            )

            return decision

        except (
            json.JSONDecodeError,
            ValidationError,
            ValueError,
        ) as error:
            last_error = error

            prompt += f"""

The previous response was invalid.

Validation error:
{str(error)}

Return one corrected JSON object.
"""

    raise RuntimeError(
        "The model failed to return a valid "
        f"decision: {last_error}"
    )
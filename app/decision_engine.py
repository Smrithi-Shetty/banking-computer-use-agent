import json
from unittest import result

from app.foundry_client import get_client
from app.config import (
    AZURE_OPENAI_DEPLOYMENT
)


def decide_next_action(
    goal,
    observation
):

    client = get_client()

    prompt = f"""
You are a computer-use agent.

Goal:
{goal}

Observation:
{json.dumps(observation, indent=2)}

IMPORTANT RULES

1. Return ONLY the NEXT action.
2. Never return a list.
3. Never invent user data.
4. Use runtime values only.

Allowed runtime values:

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

Allowed actions:

click
fill
read
finish

Return ONLY JSON.

Schema:

{{
    "action":"click|fill|read|finish",
    "target_text":"string",
    "value":"string",
    "reason":"string"
}}
"""

    response = client.responses.create(
        model=AZURE_OPENAI_DEPLOYMENT,
        input=prompt
    )

    response_text = (
        response.output_text
        .replace("```json", "")
        .replace("```", "")
        .strip()
    )

    result = json.loads(response_text)

    if isinstance(result, list):
        return result[0]

    return result
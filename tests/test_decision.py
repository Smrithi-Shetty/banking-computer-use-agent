from app.decision_engine import (
    decide_next_action
)

observation = {
    "title": "ParaBank | Welcome | Online Banking",
    "elements": [
        {
            "id": "link_10",
            "type": "link",
            "text": "Register"
        }
    ]
}

result = decide_next_action(
    goal="Create a new account",
    observation=observation
)

import json

print(
    json.dumps(
        result,
        indent=4
    )
)
print(type(result))

import json

from app.decision_engine import (
    decide_next_action,
)


def main():
    observation = {
        "url": (
            "https://parabank.parasoft.com/"
            "parabank/index.htm"
        ),
        "title": (
            "ParaBank | Welcome | "
            "Online Banking"
        ),
        "elements": [
            {
                "element_id": "link_1",
                "kind": "link",
                "text": "Register",
                "visible": True,
                "enabled": True,
            }
        ],
    }

    result = decide_next_action(
        goal=(
            "Register a new ParaBank user."
        ),
        observation=observation,
        outputs={},
    )

    print(
        json.dumps(
            result.model_dump(),
            indent=4,
        )
    )


if __name__ == "__main__":
    main()
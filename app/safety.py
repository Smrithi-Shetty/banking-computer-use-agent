from urllib.parse import urlparse

from app.config import (
    PARABANK_HOST,
)

from app.models import (
    ActionDecision,
)


ALLOWED_ACTIONS = {
    "click",
    "fill",
    "read",
    "wait",
    "finish",
    "escalate",
}


ALLOWED_RUNTIME_REFERENCES = {
    "runtime_first_name",
    "runtime_last_name",
    "runtime_address",
    "runtime_city",
    "runtime_state",
    "runtime_zip",
    "runtime_phone",
    "runtime_ssn",
    "runtime_username",
    "runtime_password",
}


RISKY_TEXT = {
    "open new account",
    "transfer funds",
    "bill pay",
    "request loan",
    "send payment",
}


def validate_action(
    current_url: str,
    decision: ActionDecision,
    observation: dict,
) -> tuple[bool, str | None]:
    hostname = urlparse(
        current_url
    ).hostname

    if hostname != PARABANK_HOST:
        return (
            False,
            "The current host is outside the "
            "ParaBank allowlist.",
        )

    if decision.action not in ALLOWED_ACTIONS:
        return (
            False,
            "The action is not allowlisted.",
        )

    elements = observation.get(
        "elements",
        [],
    )

    valid_ids = {
        element["element_id"]
        for element in elements
    }

    if decision.action in {
        "click",
        "fill",
        "read",
    }:
        if not decision.target_id:
            return (
                False,
                "The action requires target_id.",
            )

        if decision.target_id not in valid_ids:
            return (
                False,
                "The target_id is not present "
                "in the current observation.",
            )

    if decision.action == "fill":
        if (
            decision.value_ref
            not in ALLOWED_RUNTIME_REFERENCES
        ):
            return (
                False,
                "The fill value reference is "
                "not allowlisted.",
            )

        target = next(
            (
                element
                for element in elements
                if (
                    element["element_id"]
                    == decision.target_id
                )
            ),
            None,
        )

        if target and target.get(
            "is_filled"
        ):
            return (
                False,
                "The selected field is already "
                "filled.",
            )

    target = next(
        (
            element
            for element in elements
            if (
                element["element_id"]
                == decision.target_id
            )
        ),
        None,
    )

    if target:
        target_description = " ".join(
            str(
                target.get(
                    key,
                    "",
                )
            )
            for key in (
                "text",
                "label",
                "name",
            )
        ).lower()

        if any(
            risky_text
            in target_description
            for risky_text in RISKY_TEXT
        ):
            return (
                False,
                "The target is classified as "
                "risky and requires human "
                "approval.",
            )

    return True, None
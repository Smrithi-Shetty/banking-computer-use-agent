import json
import time
from typing import Any

from app.action_executor import (
    execute_action,
)

from app.config import (
    AGENT_TIMEOUT_SECONDS,
    MAX_AGENT_STEPS,
)

from app.decision_engine import (
    decide_next_action,
)

from app.runtime_data import (
    RUNTIME_VALUES,
)

from app.safety import (
    validate_action,
)

from app.surface import (
    observe,
)


REQUIRED_OUTPUTS = {
    "account_number",
    "total_balance",
    "available_balance",
}


def _redacted_decision(
    decision,
) -> dict[str, Any]:
    data = decision.model_dump()

    if data.get("value_ref"):
        data["resolved_value"] = (
            "[REDACTED]"
        )

    return data


def run_agent_loop(
    page,
    goal: str,
) -> dict[str, Any]:
    history: list[dict] = []

    outputs: dict[str, str] = {}

    started_at = time.monotonic()

    previous_signature = None

    repeated_action_count = 0

    final_status = "MAX_STEPS_REACHED"

    for step_number in range(
        1,
        MAX_AGENT_STEPS + 1,
    ):
        elapsed = (
            time.monotonic()
            - started_at
        )

        if elapsed >= AGENT_TIMEOUT_SECONDS:
            final_status = "TIMEOUT"
            break

        observation, registry = observe(
            page
        )

        try:
            decision = decide_next_action(
                goal=goal,
                observation=observation,
                outputs=outputs,
            )

        except Exception as error:
            final_status = (
                "DECISION_FAILURE"
            )

            history.append(
                {
                    "step": step_number,
                    "url": page.url,
                    "page_title": page.title(),
                    "result": {
                        "status": "FAILURE",
                        "error": str(error),
                    },
                }
            )

            break

        signature = (
            decision.action,
            decision.target_id,
            decision.value_ref,
            decision.extract_as,
        )

        if signature == previous_signature:
            repeated_action_count += 1
        else:
            repeated_action_count = 0

        previous_signature = signature

        if repeated_action_count >= 2:
            final_status = (
                "REPEATED_ACTION"
            )

            history.append(
                {
                    "step": step_number,
                    "url": page.url,
                    "page_title": page.title(),
                    "decision": (
                        _redacted_decision(
                            decision
                        )
                    ),
                    "result": {
                        "status": "FAILURE",
                        "error": (
                            "The same action was "
                            "proposed repeatedly."
                        ),
                    },
                }
            )

            break

        allowed, safety_reason = (
            validate_action(
                current_url=page.url,
                decision=decision,
                observation=observation,
            )
        )

        if not allowed:
            final_status = "SAFETY_BLOCKED"

            history.append(
                {
                    "step": step_number,
                    "url": page.url,
                    "page_title": page.title(),
                    "decision": (
                        _redacted_decision(
                            decision
                        )
                    ),
                    "result": {
                        "status": (
                            "SAFETY_BLOCKED"
                        ),
                        "error": safety_reason,
                    },
                }
            )

            break

        result = execute_action(
            page=page,
            decision=decision,
            element_registry=registry,
            runtime_values=RUNTIME_VALUES,
        )

        history_entry = {
            "step": step_number,
            "url": page.url,
            "page_title": page.title(),
            "decision": (
                _redacted_decision(
                    decision
                )
            ),
            "result": result.model_dump(),
        }

        history.append(history_entry)

        print(
            json.dumps(
                history_entry,
                indent=4,
            )
        )

        if (
            result.status
            == "HUMAN_INTERVENTION_REQUIRED"
        ):
            final_status = (
                "HUMAN_INTERVENTION_REQUIRED"
            )
            break

        if result.status == "FAILURE":
            final_status = (
                "EXECUTION_FAILURE"
            )
            break

        if (
            result.extracted_value
            is not None
        ):
            output_name = (
                result.extract_as
                or "extracted_value"
            )

            outputs[output_name] = (
                result.extracted_value
            )

            print("\nCURRENT OUTPUTS\n")

            print(
                json.dumps(
                    outputs,
                    indent=4,
                )
            )

        if decision.action == "finish":
            if REQUIRED_OUTPUTS.issubset(
                outputs.keys()
            ):
                final_status = "SUCCESS"
                break

            history.append(
                {
                    "step": step_number,
                    "result": {
                        "status": "FAILURE",
                        "error": (
                            "Finish was requested "
                            "before all account "
                            "outputs were collected."
                        ),
                    },
                }
            )

            continue

    return {
        "status": final_status,
        "goal": goal,
        "outputs": outputs,
        "step_count": len(history),
        "history": history,
    }
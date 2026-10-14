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

from app.session_controller import (
    SessionController,
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


def _history_entry(
    step_number: int,
    page,
    decision,
    result: dict[str, Any],
) -> dict[str, Any]:

    return {
        "step": step_number,
        "url": page.url,
        "page_title": page.title(),
        "decision": (
            _redacted_decision(
                decision
            )
        ),
        "result": result,
    }


def run_agent_loop(
    page,
    goal: str,
) -> dict[str, Any]:

    history: list[dict[str, Any]] = []

    outputs: dict[str, str] = {}

    started_at = time.monotonic()

    previous_signature = None

    repeated_action_count = 0

    final_status = "MAX_STEPS_REACHED"

    session_controller = SessionController(
        page=page,
        goal=goal,
    )

    for step_number in range(
        1,
        MAX_AGENT_STEPS + 1,
    ):

        session_controller.update_step(
            step_number
        )

        elapsed = (
            time.monotonic()
            - started_at
        )

        if elapsed >= AGENT_TIMEOUT_SECONDS:

            final_status = "TIMEOUT"

            failure_result = (
                session_controller.mark_failed(
                    error=(
                        "Agent execution exceeded "
                        "the configured timeout."
                    )
                )
            )

            history.append(
                {
                    "step": step_number,
                    "url": page.url,
                    "page_title": page.title(),
                    "result": failure_result,
                }
            )

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

            failure_result = (
                session_controller.mark_failed(
                    error=str(error)
                )
            )

            history.append(
                {
                    "step": step_number,
                    "url": page.url,
                    "page_title": page.title(),
                    "result": failure_result,
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

        #
        # Repeated actions require human review
        #

        if repeated_action_count >= 2:

            handoff_reason = (
                "The automation proposed the "
                "same action repeatedly and "
                "cannot safely determine the "
                "next step."
            )

            repeated_entry = {
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
                        "HUMAN_INTERVENTION_REQUIRED"
                    ),
                    "error": handoff_reason,
                },
            }

            history.append(
                repeated_entry
            )

            print(
                json.dumps(
                    repeated_entry,
                    indent=4,
                )
            )

            session_controller.handoff_to_human(
                reason=handoff_reason
            )

            # The human may have changed the page,
            # so clear action repetition state.
            previous_signature = None
            repeated_action_count = 0

            # Re-observe the same live browser
            # on the next iteration.
            continue

        #
        # Validate action against safety policy
        #

        allowed, safety_reason = (
            validate_action(
                current_url=page.url,
                decision=decision,
                observation=observation,
            )
        )

        if not allowed:

            handoff_reason = (
                safety_reason
                or (
                    "The requested action requires "
                    "human review."
                )
            )

            safety_entry = {
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
                        "HUMAN_INTERVENTION_REQUIRED"
                    ),
                    "error": handoff_reason,
                },
            }

            history.append(
                safety_entry
            )

            print(
                json.dumps(
                    safety_entry,
                    indent=4,
                )
            )

            session_controller.handoff_to_human(
                reason=handoff_reason
            )

            previous_signature = None
            repeated_action_count = 0

            continue

        #
        # The model may explicitly escalate
        #

        if decision.action == "escalate":

            handoff_reason = (
                decision.reason
                or (
                    "The model requested human "
                    "intervention."
                )
            )

            escalation_entry = {
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
                        "HUMAN_INTERVENTION_REQUIRED"
                    ),
                    "error": handoff_reason,
                },
            }

            history.append(
                escalation_entry
            )

            print(
                json.dumps(
                    escalation_entry,
                    indent=4,
                )
            )

            session_controller.handoff_to_human(
                reason=handoff_reason
            )

            previous_signature = None
            repeated_action_count = 0

            continue

        #
        # Execute allowed automation action
        #

        result = execute_action(
            page=page,
            decision=decision,
            element_registry=registry,
            runtime_values=RUNTIME_VALUES,
        )

        history_entry = _history_entry(
            step_number=step_number,
            page=page,
            decision=decision,
            result=result.model_dump(),
        )

        history.append(
            history_entry
        )

        print(
            json.dumps(
                history_entry,
                indent=4,
            )
        )

        #
        # Executor can also request handoff
        #

        if (
            result.status
            == "HUMAN_INTERVENTION_REQUIRED"
        ):

            handoff_reason = (
                result.error
                or decision.reason
                or (
                    "The action executor requested "
                    "human intervention."
                )
            )

            session_controller.handoff_to_human(
                reason=handoff_reason
            )

            previous_signature = None
            repeated_action_count = 0

            continue

        #
        # Execution failure
        #

        if result.status == "FAILURE":

            final_status = (
                "EXECUTION_FAILURE"
            )

            session_controller.mark_failed(
                error=(
                    result.error
                    or (
                        "The action executor "
                        "reported a failure."
                    )
                )
            )

            break

        #
        # Capture extracted outputs
        #

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

            print(
                "\nCURRENT OUTPUTS\n"
            )

            print(
                json.dumps(
                    outputs,
                    indent=4,
                )
            )

        #
        # Finish only after all required
        # business outputs were extracted
        #

        if decision.action == "finish":

            if REQUIRED_OUTPUTS.issubset(
                outputs.keys()
            ):

                final_status = "SUCCESS"

                session_controller.mark_completed()

                break

            missing_outputs = sorted(
                REQUIRED_OUTPUTS
                - outputs.keys()
            )

            finish_entry = {
                "step": step_number,
                "url": page.url,
                "page_title": page.title(),
                "result": {
                    "status": "FAILURE",
                    "error": (
                        "Finish was requested "
                        "before all account outputs "
                        "were collected."
                    ),
                    "missing_outputs": (
                        missing_outputs
                    ),
                },
            }

            history.append(
                finish_entry
            )

            print(
                json.dumps(
                    finish_entry,
                    indent=4,
                )
            )

            # Continue because this is not a
            # terminal failure. The model gets
            # Current Outputs on the next step.
            previous_signature = None

            continue

    #
    # If the loop reaches its maximum without
    # success, record a failed session.
    #

    if (
        final_status
        == "MAX_STEPS_REACHED"
    ):

        session_controller.mark_failed(
            error=(
                "The agent reached the maximum "
                "configured number of steps."
            )
        )

    return {
        "status": final_status,
        "goal": goal,
        "outputs": outputs,
        "step_count": len(history),
        "session": {
            "session_id": (
                session_controller.session_id
            ),
            "owner": (
                session_controller.owner.value
            ),
            "status": (
                session_controller.status.value
            ),
        },
        "history": history,
    }
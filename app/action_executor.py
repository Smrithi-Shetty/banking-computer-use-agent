import time

from playwright.sync_api import (
    Locator,
    Page,
)

from app.models import (
    ActionDecision,
    ActionResult,
)


def execute_action(
    page: Page,
    decision: ActionDecision,
    element_registry: dict[
        str,
        Locator,
    ],
    runtime_values: dict[
        str,
        str,
    ],
) -> ActionResult:
    try:
        if decision.action == "wait":
            time.sleep(1)

            return ActionResult(
                status="SUCCESS",
                action="wait",
            )

        if decision.action == "finish":
            return ActionResult(
                status="SUCCESS",
                action="finish",
            )

        if decision.action == "escalate":
            return ActionResult(
                status=(
                    "HUMAN_INTERVENTION_REQUIRED"
                ),
                action="escalate",
            )

        if not decision.target_id:
            return ActionResult(
                status="FAILURE",
                action=decision.action,
                error=(
                    "This action requires target_id."
                ),
            )

        locator = element_registry.get(
            decision.target_id
        )

        if locator is None:
            return ActionResult(
                status="FAILURE",
                action=decision.action,
                target_id=decision.target_id,
                error=(
                    "The target was not available "
                    "in the current observation."
                ),
            )

        if decision.action == "click":
            locator.click()

            page.wait_for_timeout(750)

            return ActionResult(
                status="SUCCESS",
                action="click",
                target_id=decision.target_id,
            )

        if decision.action == "fill":
            if not decision.value_ref:
                return ActionResult(
                    status="FAILURE",
                    action="fill",
                    target_id=decision.target_id,
                    error=(
                        "Fill requires value_ref."
                    ),
                )

            if (
                decision.value_ref
                not in runtime_values
            ):
                return ActionResult(
                    status="FAILURE",
                    action="fill",
                    target_id=decision.target_id,
                    error=(
                        "Unknown runtime reference: "
                        f"{decision.value_ref}"
                    ),
                )

            value = runtime_values[
                decision.value_ref
            ]

            locator.fill(value)

            return ActionResult(
                status="SUCCESS",
                action="fill",
                target_id=decision.target_id,
            )

        if decision.action == "read":
            try:
                extracted_value = (
                    locator.input_value()
                )

            except Exception:
                try:
                    extracted_value = (
                        locator.inner_text()
                        .strip()
                    )

                except Exception:
                    extracted_value = (
                        locator.text_content()
                        or ""
                    ).strip()

            if not extracted_value:
                return ActionResult(
                    status="FAILURE",
                    action="read",
                    target_id=decision.target_id,
                    extract_as=decision.extract_as,
                    error=(
                        "The selected element did "
                        "not contain readable data."
                    ),
                )

            return ActionResult(
                status="SUCCESS",
                action="read",
                target_id=decision.target_id,
                extracted_value=(
                    extracted_value
                ),
                extract_as=decision.extract_as,
            )

        return ActionResult(
            status="FAILURE",
            action=decision.action,
            target_id=decision.target_id,
            error="Unsupported action.",
        )

    except Exception as error:
        return ActionResult(
            status="FAILURE",
            action=decision.action,
            target_id=decision.target_id,
            error=str(error),
        )
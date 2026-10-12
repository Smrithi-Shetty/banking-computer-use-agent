from playwright.sync_api import Page


def execute_action(
    page: Page,
    decision: dict
):

    action = decision.get("action")

    target_text = decision.get(
        "target_text",
        ""
    )

    value = decision.get(
        "value",
        ""
    )

    try:

        # CLICK

        if action == "click":

            page.get_by_text(
                target_text,
                exact=False
            ).first.click()

            return {
                "status": "SUCCESS",
                "action": action,
                "target_text": target_text
            }

        # FILL

        elif action == "fill":

            textboxes = page.locator(
                "input"
            )

            count = textboxes.count()

            if count > 0:

                textboxes.first.fill(
                    value
                )

                return {
                    "status": "SUCCESS",
                    "action": action,
                    "value": value
                }

            return {
                "status": "FAILURE",
                "error": "No input field found"
            }

        # READ

        elif action == "read":

            return {
                "status": "SUCCESS",
                "action": action
            }

        # FINISH

        elif action == "finish":

            return {
                "status": "SUCCESS",
                "action": action
            }

        return {
            "status": "UNSUPPORTED_ACTION",
            "action": action
        }

    except Exception as ex:

        return {
            "status": "FAILURE",
            "error": str(ex)
        }
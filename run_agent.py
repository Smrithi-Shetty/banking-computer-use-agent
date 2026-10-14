import json
from datetime import datetime
from pathlib import Path

from playwright.sync_api import (
    sync_playwright,
)

from app.agent_loop import (
    run_agent_loop,
)

from app.config import (
    HEADLESS,
    PARABANK_BASE_URL,
)

from app.artifact_generator import (
    save_artifact,
)


def main():

    goal = (
        "Register a new ParaBank user. "
        "After successful registration, open "
        "Accounts Overview. Extract the first "
        "available account number, total balance, "
        "and available balance. Do not finish until "
        "account_number, total_balance, and "
        "available_balance are all extracted."
    )

    with sync_playwright() as playwright:

        browser = playwright.chromium.launch(
            headless=HEADLESS
        )

        context = browser.new_context()

        page = context.new_page()

        page.goto(
            PARABANK_BASE_URL,
            wait_until="domcontentloaded",
        )

        result = run_agent_loop(
            page=page,
            goal=goal,
        )

        artifact_file = save_artifact(
            goal=goal,
            history=result["history"],
            outputs=result["outputs"],
        )

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        Path(
            "evidence/discovery"
        ).mkdir(
            parents=True,
            exist_ok=True
        )

        page.screenshot(
            path=(
                f"evidence/discovery/"
                f"account_overview_{timestamp}.png"
            ),
            full_page=True
        )

        #
        # FINAL SUMMARY ONLY
        #

        final_summary = {
            "status": result["status"],
            "outputs": result["outputs"]
        }

        print("\n" + "=" * 60)
        print("DISCOVERY RUN SUMMARY")
        print("=" * 60)

        print(
            json.dumps(
                final_summary,
                indent=4
            )
        )

        print("=" * 60)

        print(
            f"\nArtifact Saved: "
            f"{artifact_file}"
        )

        screenshot_file = (
            f"evidence/discovery/"
            f"account_overview_{timestamp}.png"
        )

        page.screenshot(
            path=screenshot_file,
            full_page=True
        )

        print(
            f"\nDiscovery Screenshot Saved: "
            f"{screenshot_file}"
        )

        if not HEADLESS:

            input(
                "\nPress Enter to close..."
            )

        context.close()
        browser.close()


if __name__ == "__main__":
    main()
from playwright.sync_api import (
    sync_playwright
)

from app.config import (
    PARABANK_BASE_URL
)

from app.agent_loop import (
    run_agent_loop
)


with sync_playwright() as p:

    browser = p.chromium.launch(
        headless=False
    )

    page = browser.new_page()

    page.goto(
        PARABANK_BASE_URL
    )

    page.wait_for_timeout(
        3000
    )

    history = run_agent_loop(
        page,
        goal="Create a new account"
    )

    input(
        "\nPress Enter to close..."
    )

    browser.close()
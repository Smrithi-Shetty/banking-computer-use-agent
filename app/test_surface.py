from playwright.sync_api import sync_playwright

from app.config import (
    PARABANK_BASE_URL
)

from app.surface import observe


with sync_playwright() as p:

    browser = p.chromium.launch(
        headless=False
    )

    page = browser.new_page()

    page.goto(
        PARABANK_BASE_URL
    )

    page.wait_for_timeout(5000)

    observation = observe(page)

    print(observation)

    input(
        "Press Enter to close..."
    )

    browser.close()
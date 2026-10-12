from playwright.sync_api import Page


def observe(page: Page):

    elements = []

    buttons = page.locator("button").all()

    for idx, button in enumerate(buttons):

        try:

            elements.append(
                {
                    "id": f"btn_{idx}",
                    "type": "button",
                    "text": button.inner_text()
                }
            )

        except Exception:
            pass

    return {
        "url": page.url,
        "title": page.title(),
        "elements": elements
    }
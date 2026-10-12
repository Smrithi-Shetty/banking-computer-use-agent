from playwright.sync_api import Page


def observe(page: Page):

    elements = []

    # Links
    for idx, link in enumerate(page.locator("a").all()):
        try:
            text = link.inner_text().strip()

            if text:
                elements.append(
                    {
                        "id": f"link_{idx}",
                        "type": "link",
                        "text": text
                    }
                )
        except:
            pass

    # Inputs
    for idx, inp in enumerate(page.locator("input").all()):
        try:

            elements.append(
                {
                    "id": f"input_{idx}",
                    "type": "input",
                    "name": inp.get_attribute("name"),
                    "placeholder":
                        inp.get_attribute("placeholder")
                }
            )

        except:
            pass

    return {
        "url": page.url,
        "title": page.title(),
        "elements": elements
    }
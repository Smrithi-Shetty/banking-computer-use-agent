from typing import Any

from playwright.sync_api import Locator, Page


def _safe_attribute(
    locator: Locator,
    attribute: str,
) -> str | None:
    try:
        return locator.get_attribute(attribute)
    except Exception:
        return None


def _safe_text(
    locator: Locator,
) -> str:
    try:
        return locator.inner_text().strip()
    except Exception:
        return ""


def _safe_visible(
    locator: Locator,
) -> bool:
    try:
        return locator.is_visible()
    except Exception:
        return False


def _safe_enabled(
    locator: Locator,
) -> bool:
    try:
        return locator.is_enabled()
    except Exception:
        return False


def _safe_input_value(
    locator: Locator,
) -> str:
    try:
        return locator.input_value()
    except Exception:
        return ""


def _derive_input_label(
    page: Page,
    locator: Locator,
) -> str:
    aria_label = _safe_attribute(
        locator,
        "aria-label",
    )

    if aria_label:
        return aria_label.strip()

    placeholder = _safe_attribute(
        locator,
        "placeholder",
    )

    if placeholder:
        return placeholder.strip()

    dom_id = _safe_attribute(
        locator,
        "id",
    )

    if dom_id:
        try:
            label = page.locator(
                f'label[for="{dom_id}"]'
            ).first

            if label.count() > 0:
                text = _safe_text(label)

                if text:
                    return text

        except Exception:
            pass

    try:
        row_label = locator.evaluate(
            """
            element => {
                const row = element.closest("tr");

                if (!row) {
                    return "";
                }

                const cells = row.querySelectorAll(
                    "td, th"
                );

                if (cells.length === 0) {
                    return "";
                }

                return cells[0].innerText.trim();
            }
            """
        )

        if row_label:
            return row_label.strip()

    except Exception:
        pass

    return (
        _safe_attribute(locator, "name")
        or "Unlabelled input"
    )


def observe(
    page: Page,
) -> tuple[
    dict[str, Any],
    dict[str, Locator],
]:
    elements: list[dict[str, Any]] = []

    registry: dict[str, Locator] = {}

    # Inputs and input-based buttons

    inputs = page.locator("input")

    for index in range(inputs.count()):
        locator = inputs.nth(index)

        if not _safe_visible(locator):
            continue

        element_id = f"input_{index}"

        input_type = (
            _safe_attribute(
                locator,
                "type",
            )
            or "text"
        ).lower()

        name = _safe_attribute(
            locator,
            "name",
        )

        label = _derive_input_label(
            page,
            locator,
        )

        if input_type in {
            "submit",
            "button",
            "reset",
        }:
            elements.append(
                {
                    "element_id": element_id,
                    "kind": "button",
                    "input_type": input_type,
                    "name": name,
                    "text": (
                        _safe_attribute(
                            locator,
                            "value",
                        )
                        or label
                    ),
                    "visible": True,
                    "enabled": _safe_enabled(
                        locator
                    ),
                }
            )

        else:
            elements.append(
                {
                    "element_id": element_id,
                    "kind": "input",
                    "input_type": input_type,
                    "name": name,
                    "label": label,
                    "is_filled": bool(
                        _safe_input_value(locator)
                    ),
                    "visible": True,
                    "enabled": _safe_enabled(
                        locator
                    ),
                    "sensitive": (
                        input_type == "password"
                    ),
                }
            )

        registry[element_id] = locator

    # Native buttons

    buttons = page.locator("button")

    for index in range(buttons.count()):
        locator = buttons.nth(index)

        if not _safe_visible(locator):
            continue

        element_id = f"button_{index}"

        elements.append(
            {
                "element_id": element_id,
                "kind": "button",
                "text": _safe_text(locator),
                "visible": True,
                "enabled": _safe_enabled(locator),
            }
        )

        registry[element_id] = locator

    # Links

    links = page.locator("a")

    for index in range(links.count()):
        locator = links.nth(index)

        if not _safe_visible(locator):
            continue

        text = _safe_text(locator)

        if not text:
            continue

        element_id = f"link_{index}"

        elements.append(
            {
                "element_id": element_id,
                "kind": "link",
                "text": text,
                "visible": True,
                "enabled": _safe_enabled(locator),
            }
        )

        registry[element_id] = locator

    # Semantic table values

    tables = page.locator("table")

    table_value_index = 0

    for table_index in range(
        tables.count()
    ):
        table = tables.nth(table_index)

        if not _safe_visible(table):
            continue

        header_cells = table.locator(
            "thead th"
        )

        headers: list[str] = []

        for header_index in range(
            header_cells.count()
        ):
            headers.append(
                _safe_text(
                    header_cells.nth(
                        header_index
                    )
                )
            )

        # Fallback for tables without <thead>
        if not headers:
            first_row_headers = table.locator(
                "tr"
            ).first.locator("th")

            for header_index in range(
                first_row_headers.count()
            ):
                headers.append(
                    _safe_text(
                        first_row_headers.nth(
                            header_index
                        )
                    )
                )

        rows = table.locator("tbody tr")

        if rows.count() == 0:
            rows = table.locator("tr")

        for row_index in range(
            rows.count()
        ):
            row = rows.nth(row_index)

            cells = row.locator("td")

            if cells.count() == 0:
                continue

            for column_index in range(
                cells.count()
            ):
                cell = cells.nth(column_index)

                if not _safe_visible(cell):
                    continue

                value_text = _safe_text(cell)

                if not value_text:
                    continue

                column_header = (
                    headers[column_index]
                    if column_index < len(headers)
                    else (
                        f"Column {column_index + 1}"
                    )
                )

                element_id = (
                    f"table_value_"
                    f"{table_value_index}"
                )

                table_value_index += 1

                elements.append(
                    {
                        "element_id": element_id,
                        "kind": "table_value",
                        "table_index": table_index,
                        "row_index": row_index,
                        "column_index": (
                            column_index
                        ),
                        "column_header": (
                            column_header
                        ),
                        "value_text": value_text,
                        "visible": True,
                        "enabled": False,
                    }
                )

                registry[element_id] = cell

    # Headings and error text only.
    # Do not duplicate table headers or cells.

    readable = page.locator(
        "h1, h2, h3, "
        "p.error, .error, "
        "#rightPanel > p"
    )

    text_index = 0

    seen_text: set[str] = set()

    for index in range(
        readable.count()
    ):
        locator = readable.nth(index)

        if not _safe_visible(locator):
            continue

        text = _safe_text(locator)

        if not text:
            continue

        if text in seen_text:
            continue

        seen_text.add(text)

        element_id = f"text_{text_index}"

        text_index += 1

        elements.append(
            {
                "element_id": element_id,
                "kind": "text",
                "text": text[:300],
                "visible": True,
                "enabled": False,
            }
        )

        registry[element_id] = locator

    observation = {
        "url": page.url,
        "title": page.title(),
        "elements": elements,
    }

    return observation, registry
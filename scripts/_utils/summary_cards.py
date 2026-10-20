from html import escape


def summary_cards(items: list[tuple[str, str]]) -> list[str]:
    """Markdown lines for a row of stat cards (label, value) on a list page.

    Raw HTML block with no blank lines inside, so kramdown passes it through.
    Styled by .lotto-stats-grid / .lotto-stats-card / .summary-cards.
    """
    lines = ['<div class="lotto-stats-grid summary-cards">']
    for label, value in items:
        lines.append(
            f'  <div class="lotto-stats-card"><span class="lotto-stats-label">{escape(label)}</span>'
            f"<strong>{escape(value)}</strong></div>"
        )
    lines.extend(["</div>", ""])
    return lines

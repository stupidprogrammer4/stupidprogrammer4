#!/usr/bin/env python3
"""Generate a self-hosted weekly GitHub activity line chart."""

from __future__ import annotations

import datetime as dt
import html
import pathlib
import re
import sys
import time
import urllib.request

USERNAME = "stupidprogrammer4"
ROOT = pathlib.Path(__file__).resolve().parents[1]
OUTPUT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "assets/activity-graph.svg"


def fetch_days() -> list[tuple[dt.date, int]]:
    url = f"https://github.com/users/{USERNAME}/contributions"
    request = urllib.request.Request(url, headers={"User-Agent": "pouya-profile-activity-graph/1.0"})
    for attempt in range(3):
        try:
            page = urllib.request.urlopen(request, timeout=30).read().decode()
            break
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2**attempt)
    pattern = re.compile(
        r'data-date="(\d{4}-\d{2}-\d{2})"[^>]*>.*?'
        r"<tool-tip[^>]*>(?:(No)|(\d+) contributions?) on ",
        re.S,
    )
    days = [
        (dt.date.fromisoformat(date), 0 if no_contributions else int(count))
        for date, no_contributions, count in pattern.findall(page)
    ]
    if not days:
        raise RuntimeError("GitHub returned no contribution data")
    return sorted(days)


def weekly_totals(days: list[tuple[dt.date, int]]) -> list[tuple[dt.date, int]]:
    totals: dict[dt.date, int] = {}
    for date, count in days:
        week = date - dt.timedelta(days=date.weekday())
        totals[week] = totals.get(week, 0) + count
    return sorted(totals.items())


def render(points: list[tuple[dt.date, int]]) -> str:
    width, height = 900, 280
    left, right, top, bottom = 62, 24, 42, 46
    chart_width = width - left - right
    chart_height = height - top - bottom
    maximum = max(value for _, value in points) or 1
    ceiling = max(10, ((maximum + 9) // 10) * 10)

    def x(index: int) -> float:
        return left + index * chart_width / max(1, len(points) - 1)

    def y(value: int) -> float:
        return top + chart_height * (1 - value / ceiling)

    line = " ".join(f"{x(index):.1f},{y(value):.1f}" for index, (_, value) in enumerate(points))
    area = f"{left},{top + chart_height} {line} {left + chart_width},{top + chart_height}"
    grid, labels = [], []
    for step in range(5):
        value = round(ceiling * step / 4)
        y_position = y(value)
        grid.append(f'<line x1="{left}" y1="{y_position:.1f}" x2="{width-right}" y2="{y_position:.1f}"/>')
        labels.append(f'<text x="{left-12}" y="{y_position+4:.1f}" text-anchor="end">{value}</text>')

    months, previous_month, last_label_x = [], None, -100.0
    for index, (date, _) in enumerate(points):
        if date.month != previous_month:
            label_x = x(index)
            if label_x - last_label_x >= 38:
                months.append(f'<text x="{label_x:.1f}" y="{height-18}">{html.escape(date.strftime("%b"))}</text>')
                last_label_x = label_x
            previous_month = date.month

    total = sum(value for _, value in points)
    latest = points[-1][0].isoformat()
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">GitHub contribution activity</title>
<desc id="desc">{total} public contributions grouped by week through {latest}.</desc>
<defs><linearGradient id="area" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#27ff73" stop-opacity=".34"/><stop offset="1" stop-color="#27ff73" stop-opacity="0"/></linearGradient><filter id="glow"><feGaussianBlur stdDeviation="2.4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>
<rect width="{width}" height="{height}" rx="8" fill="#06100a"/>
<g stroke="#174527" stroke-width="1" opacity=".72">{"".join(grid)}</g>
<g fill="#638b70" font-family="ui-monospace,monospace" font-size="11">{"".join(labels)}{"".join(months)}</g>
<text x="{left}" y="24" fill="#27ff73" font-family="ui-monospace,monospace" font-size="13">CONTRIBUTION ACTIVITY · WEEKLY</text>
<text x="{width-right}" y="24" text-anchor="end" fill="#638b70" font-family="ui-monospace,monospace" font-size="11">{total} CONTRIBUTIONS</text>
<polygon points="{area}" fill="url(#area)"/>
<polyline points="{line}" fill="none" stroke="#27ff73" stroke-width="2.4" stroke-linejoin="round" stroke-linecap="round" filter="url(#glow)"/>
</svg>
"""


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render(weekly_totals(fetch_days())), encoding="utf-8")
    print(f"Updated {OUTPUT}")


if __name__ == "__main__":
    main()

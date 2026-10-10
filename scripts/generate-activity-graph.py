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
OUTPUT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "assets/contribution-activity.svg"


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
    width, height = 900, 340
    left, right, top, bottom = 62, 36, 138, 46
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
        labels.append(f'<text x="{left-14}" y="{y_position+4:.1f}" text-anchor="end">{value}</text>')

    months, previous_month, last_label_x = [], None, -100.0
    for index, (date, _) in enumerate(points):
        if date.month != previous_month:
            label_x = x(index)
            if label_x - last_label_x >= 38:
                months.append(f'<text x="{label_x:.1f}" y="{height-18}" text-anchor="middle">{html.escape(date.strftime("%b"))}</text>')
                last_label_x = label_x
            previous_month = date.month

    total = sum(value for _, value in points)
    first = points[0][0].isoformat()
    latest = points[-1][0].isoformat()
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">GitHub contribution activity</title>
<desc id="desc">{total} public contributions grouped into weeks of {first} through {latest}. Edge weeks may be partial.</desc>
<defs>
  <linearGradient id="surface" x2="1" y2="1"><stop stop-color="#0e0c1b"/><stop offset="1" stop-color="#17132d"/></linearGradient>
  <linearGradient id="line" x1="0" y1="0" x2="1" y2="0"><stop stop-color="#c4a4ff"/><stop offset="1" stop-color="#7cbcff"/></linearGradient>
  <linearGradient id="area" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#818cf8" stop-opacity=".26"/><stop offset="1" stop-color="#818cf8" stop-opacity="0"/></linearGradient>
  <clipPath id="frame"><rect width="{width}" height="{height}" rx="20"/></clipPath>
</defs>
<g clip-path="url(#frame)">
<rect width="{width}" height="{height}" fill="url(#surface)"/>
<rect x=".5" y=".5" width="{width-1}" height="{height-1}" rx="19.5" fill="none" stroke="#393252" stroke-opacity=".65"/>
<circle cx="28" cy="25" r="4" fill="#a78bfa"/><circle cx="44" cy="25" r="4" fill="#818cf8"/><circle cx="60" cy="25" r="4" fill="#60a5fa"/>
<text x="80" y="29" fill="#b1a8cc" font-family="ui-monospace,monospace" font-size="12">~/github/activity</text>
<text x="{width-right}" y="29" text-anchor="end" fill="#c4a4ff" font-family="ui-monospace,monospace" font-size="11" letter-spacing="2">WEEKLY</text>
<path d="M24 48H{width-24}" stroke="#393252" stroke-opacity=".7"/>
<g font-family="Inter, 'DejaVu Sans', Arial, sans-serif">
  <text x="{left}" y="87" fill="#f3efff" font-size="23" font-weight="700">Contribution activity</text>
  <text x="{left}" y="111" fill="#b1a8cc" font-size="13">Weeks of {first} — {latest}</text>
  <text x="{width-right}" y="87" text-anchor="end" fill="url(#line)" font-size="30" font-weight="700">{total:,}</text>
  <text x="{width-right}" y="111" text-anchor="end" fill="#b1a8cc" font-size="12">contributions in this range</text>
</g>
<g stroke="#393252" stroke-width="1" stroke-dasharray="3 6" opacity=".55">{"".join(grid)}</g>
<g fill="#b1a8cc" font-family="Inter, 'DejaVu Sans', Arial, sans-serif" font-size="12">{"".join(labels)}{"".join(months)}</g>
<polygon points="{area}" fill="url(#area)"/>
<polyline points="{line}" fill="none" stroke="url(#line)" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/>
<circle cx="{x(len(points)-1):.1f}" cy="{y(points[-1][1]):.1f}" r="7" fill="#7cbcff" fill-opacity=".15"/>
<circle cx="{x(len(points)-1):.1f}" cy="{y(points[-1][1]):.1f}" r="3.5" fill="#7cbcff" stroke="#17132d" stroke-width="1.5"/>
</g>
</svg>
"""


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render(weekly_totals(fetch_days())), encoding="utf-8")
    print(f"Updated {OUTPUT}")


if __name__ == "__main__":
    main()

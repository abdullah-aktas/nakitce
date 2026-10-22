"""Inline SVG pie chart — avoids flet-charts Flutter package for Play AAB builds."""

import base64
import math


def pie_chart_data_uri(slices, *, size=210):
    """slices: list of (value, color_hex). Returns a data:image/svg+xml URI."""
    total = sum(max(0.0, float(value)) for value, _ in slices)
    cx = cy = size / 2
    radius = size * 0.42
    if total <= 0:
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">'
            f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="#DCE5E3"/>'
            f"</svg>"
        )
        return "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode("ascii")

    def polar(angle_deg, r):
        rad = math.radians(angle_deg - 90)
        return cx + r * math.cos(rad), cy + r * math.sin(rad)

    parts = []
    start = 0.0
    for value, color in slices:
        if value <= 0:
            continue
        sweep = 360.0 * value / total
        end = start + sweep
        large = 1 if sweep > 180 else 0
        x1, y1 = polar(start, radius)
        x2, y2 = polar(end, radius)
        if sweep >= 359.9:
            parts.append(f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="{color}"/>')
        else:
            parts.append(
                f'<path d="M {cx} {cy} L {x1:.2f} {y1:.2f} A {radius:.2f} {radius:.2f} 0 {large} 1 {x2:.2f} {y2:.2f} Z" fill="{color}"/>'
            )
        mid = start + sweep / 2
        if sweep >= 18:
            tx, ty = polar(mid, radius * 0.62)
            pct = round(100 * value / total)
            parts.append(
                f'<text x="{tx:.1f}" y="{ty:.1f}" text-anchor="middle" dominant-baseline="middle" '
                f'fill="#FFFFFF" font-size="14" font-weight="700" font-family="Segoe UI, Arial, sans-serif">{pct}%</text>'
            )
        start = end

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">'
        f'{"".join(parts)}'
        f"</svg>"
    )
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode("ascii")

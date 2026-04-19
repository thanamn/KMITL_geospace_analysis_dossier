from __future__ import annotations

import html
import math
import re
import subprocess
import textwrap
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent
VISUAL_DIR = ROOT / "visuals"
VISUAL_DIR.mkdir(exist_ok=True)

W = 1200
H = 760
HEADER_H = 82

PALETTE = {
    "navy": "#123f63",
    "navy_2": "#214f73",
    "sky": "#7fa5c3",
    "sky_2": "#d9e8f2",
    "ink": "#1f2f3d",
    "muted": "#5f7385",
    "line": "#d8e0e8",
    "paper": "#fbfdff",
    "panel": "#ffffff",
    "panel_2": "#f4f8fb",
    "green": "#2f7a57",
    "green_soft": "#eaf5ef",
    "orange": "#c77b33",
    "orange_soft": "#fff4e9",
    "red": "#b85b55",
    "red_soft": "#fbeceb",
    "gold": "#b9973f",
    "gold_soft": "#f8f1dd",
    "purple": "#6c63a7",
    "purple_soft": "#f0eefb",
}


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def wrap_text(text: str | list[str], width: int) -> list[str]:
    if isinstance(text, list):
        lines: list[str] = []
        for item in text:
            lines.extend(wrap_text(item, width))
        return lines

    parts = str(text).split("\n")
    lines = []
    for part in parts:
        part = part.strip()
        if not part:
            lines.append("")
            continue
        lines.extend(textwrap.wrap(part, width=width, break_long_words=False))
    return lines


def points_path(points: list[tuple[float, float]]) -> str:
    return " ".join(f"{x},{y}" for x, y in points)


def scale(value: float, lo: float, hi: float, px0: float, px1: float) -> float:
    if hi == lo:
        return px0
    return px0 + (value - lo) * (px1 - px0) / (hi - lo)


class SVG:
    def __init__(self, title: str, subtitle: str = "", width: int = W, height: int = H) -> None:
        self.width = width
        self.height = height
        self.parts: list[str] = []
        self.parts.append(
            f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">
<defs>
  <marker id="arrow" markerWidth="14" markerHeight="14" refX="9" refY="4.5" orient="auto" markerUnits="strokeWidth">
    <path d="M0,0 L9,4.5 L0,9 z" fill="{PALETTE["navy"]}"/>
  </marker>
  <filter id="shadow" x="-10%" y="-10%" width="120%" height="120%">
    <feDropShadow dx="0" dy="6" stdDeviation="8" flood-color="#173048" flood-opacity="0.08"/>
  </filter>
</defs>
<style>
  .frame {{ fill: {PALETTE["paper"]}; stroke: {PALETTE["line"]}; stroke-width: 2; }}
  .header {{ fill: {PALETTE["navy"]}; }}
  .headerTitle {{ font: 700 34px Arial, Helvetica, sans-serif; fill: #ffffff; letter-spacing: 0.2px; }}
  .headerSub {{ font: 18px Arial, Helvetica, sans-serif; fill: #d8e6f0; }}
  .panel {{ fill: {PALETTE["panel"]}; stroke: {PALETTE["line"]}; stroke-width: 2; }}
  .panelSoft {{ fill: {PALETTE["panel_2"]}; stroke: {PALETTE["line"]}; stroke-width: 2; }}
  .title {{ font: 700 24px Arial, Helvetica, sans-serif; fill: {PALETTE["navy"]}; }}
  .body {{ font: 18px Arial, Helvetica, sans-serif; fill: {PALETTE["muted"]}; }}
  .small {{ font: 15px Arial, Helvetica, sans-serif; fill: {PALETTE["muted"]}; }}
  .axis {{ font: 16px Arial, Helvetica, sans-serif; fill: {PALETTE["muted"]}; }}
  .chip {{ font: 700 16px Arial, Helvetica, sans-serif; fill: {PALETTE["navy"]}; }}
  .label {{ font: 700 18px Arial, Helvetica, sans-serif; fill: {PALETTE["navy"]}; }}
  .value {{ font: 700 18px Arial, Helvetica, sans-serif; fill: {PALETTE["ink"]}; }}
  .mutedStrong {{ font: 700 16px Arial, Helvetica, sans-serif; fill: {PALETTE["muted"]}; }}
</style>
<rect class="frame" x="1" y="1" rx="22" ry="22" width="{width-2}" height="{height-2}"/>
<rect class="header" x="0" y="0" width="{width}" height="{HEADER_H}"/>
<text class="headerTitle" x="34" y="48">{esc(title)}</text>
"""
        )
        if subtitle:
            self.parts.append(f'<text class="headerSub" x="34" y="69">{esc(subtitle)}</text>')

    def add(self, fragment: str) -> None:
        self.parts.append(fragment)

    def rect(self, x: float, y: float, w: float, h: float, fill: str | None = None, stroke: str | None = None, rx: int = 18, cls: str | None = None, filter_id: str | None = None, opacity: float | None = None) -> None:
        attrs = []
        if cls:
            attrs.append(f'class="{cls}"')
        if fill:
            attrs.append(f'fill="{fill}"')
        if stroke:
            attrs.append(f'stroke="{stroke}" stroke-width="2"')
        if filter_id:
            attrs.append(f'filter="url(#{filter_id})"')
        if opacity is not None:
            attrs.append(f'opacity="{opacity}"')
        attr_str = " ".join(attrs)
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" ry="{rx}" {attr_str}/>')

    def line(self, x1: float, y1: float, x2: float, y2: float, color: str | None = None, width: int = 4, arrow: bool = False, dashed: bool = False) -> None:
        attrs = [f'x1="{x1}"', f'y1="{y1}"', f'x2="{x2}"', f'y2="{y2}"', f'stroke="{color or PALETTE["navy"]}"', f'stroke-width="{width}"', 'stroke-linecap="round"']
        if arrow:
            attrs.append('marker-end="url(#arrow)"')
        if dashed:
            attrs.append('stroke-dasharray="8 8"')
        self.parts.append(f'<line {" ".join(attrs)}/>')

    def path(self, d: str, fill: str = "none", stroke: str | None = None, width: int = 4, arrow: bool = False, opacity: float | None = None) -> None:
        attrs = [f'd="{d}"', f'fill="{fill}"']
        if stroke:
            attrs.extend([f'stroke="{stroke}"', f'stroke-width="{width}"', 'stroke-linecap="round"', 'stroke-linejoin="round"'])
        if arrow:
            attrs.append('marker-end="url(#arrow)"')
        if opacity is not None:
            attrs.append(f'opacity="{opacity}"')
        self.parts.append(f'<path {" ".join(attrs)}/>')

    def circle(self, x: float, y: float, r: float, fill: str, stroke: str | None = None, width: int = 2, opacity: float | None = None) -> None:
        attrs = [f'cx="{x}"', f'cy="{y}"', f'r="{r}"', f'fill="{fill}"']
        if stroke:
            attrs.extend([f'stroke="{stroke}"', f'stroke-width="{width}"'])
        if opacity is not None:
            attrs.append(f'opacity="{opacity}"')
        self.parts.append(f'<circle {" ".join(attrs)}/>')

    def polygon(self, points: list[tuple[float, float]], fill: str, stroke: str | None = None, width: int = 2, opacity: float | None = None) -> None:
        attrs = [f'points="{points_path(points)}"', f'fill="{fill}"']
        if stroke:
            attrs.extend([f'stroke="{stroke}"', f'stroke-width="{width}"'])
        if opacity is not None:
            attrs.append(f'opacity="{opacity}"')
        self.parts.append(f'<polygon {" ".join(attrs)}/>')

    def text(self, x: float, y: float, text: str, size: int = 18, fill: str | None = None, weight: int = 400, anchor: str = "start") -> None:
        self.parts.append(
            f'<text x="{x}" y="{y}" font-family="Arial, Helvetica, sans-serif" font-size="{size}" font-weight="{weight}" fill="{fill or PALETTE["muted"]}" text-anchor="{anchor}">{esc(text)}</text>'
        )

    def text_block(self, x: float, y: float, text: str | list[str], width_chars: int = 26, size: int = 18, fill: str | None = None, weight: int = 400, line_gap: float = 1.35, anchor: str = "start") -> None:
        lines = wrap_text(text, width_chars)
        fill_value = fill or PALETTE["muted"]
        self.parts.append(
            f'<text x="{x}" y="{y}" font-family="Arial, Helvetica, sans-serif" font-size="{size}" font-weight="{weight}" fill="{fill_value}" text-anchor="{anchor}">'
        )
        first = True
        for line in lines:
            if first:
                self.parts.append(f'<tspan x="{x}" dy="0">{esc(line)}</tspan>')
                first = False
            else:
                self.parts.append(f'<tspan x="{x}" dy="{round(size * line_gap, 1)}">{esc(line)}</tspan>')
        self.parts.append("</text>")

    def card(self, x: float, y: float, w: float, h: float, title: str, body: str | list[str], fill: str = PALETTE["panel"], accent: str = PALETTE["sky"], body_width: int | None = None, title_size: int = 23, body_size: int = 18) -> None:
        self.rect(x, y, w, h, fill=fill, stroke=PALETTE["line"], rx=18, filter_id="shadow")
        self.rect(x, y, w, 10, fill=accent, rx=18)
        title_width = max(14, int((w - 36) / 12))
        title_lines = wrap_text(title, title_width)
        self.text_block(x + 18, y + 42, title_lines, width_chars=title_width, size=title_size, fill=PALETTE["navy"], weight=700, line_gap=1.15)
        body_lines = wrap_text(body, body_width or max(18, int((w - 36) / 11)))
        if any(line.strip() for line in body_lines):
            body_y = y + 74 + max(0, len(title_lines) - 1) * round(title_size * 1.15, 1)
            effective_body_size = body_size
            available_height = (y + h - 18) - body_y
            while effective_body_size > 14:
                line_step = round(effective_body_size * 1.35, 1)
                body_height = effective_body_size + max(0, len(body_lines) - 1) * line_step
                if body_height <= available_height:
                    break
                effective_body_size -= 1
            self.text_block(x + 18, body_y, body_lines, width_chars=body_width or max(18, int((w - 36) / 11)), size=effective_body_size, fill=PALETTE["muted"], weight=400)

    def pill(self, x: float, y: float, w: float, h: float, label: str, fill: str, text_fill: str = PALETTE["navy"]) -> None:
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h/2}" ry="{h/2}" fill="{fill}"/>')
        self.text(x + w / 2, y + h / 2 + 6, label, size=16, fill=text_fill, weight=700, anchor="middle")

    def footer_note(self, text_value: str) -> None:
        self.parts.append(f'<text x="{self.width - 34}" y="{self.height - 20}" font-family="Arial, Helvetica, sans-serif" font-size="14" fill="{PALETTE["muted"]}" text-anchor="end">{esc(text_value)}</text>')

    def render(self) -> str:
        return "".join(self.parts) + "</svg>\n"


@dataclass(frozen=True)
class VisualMeta:
    id: str
    chapter: int
    figure_no: str
    filename: str
    title: str
    subtitle: str
    caption: str
    alt: str
    register_type: str
    build_bucket: str
    needs_user: str


def chip_color(level: str) -> tuple[str, str]:
    if level in {"Very strong", "World-scale", "High", "Very high", "Strong"}:
        return PALETTE["green_soft"], PALETTE["green"]
    if level in {"Growing", "Medium", "Moderate", "Emerging"}:
        return PALETTE["gold_soft"], PALETTE["orange"]
    return PALETTE["red_soft"], PALETTE["red"]


def draw_comparison_table(svg: SVG, x: int, y: int, columns: list[str], rows: list[str], values: list[list[str]], col_widths: list[int] | None = None, row_height: int = 72, title_fill: str = PALETTE["navy"]) -> None:
    widths = col_widths or [180] + [190] * (len(columns) - 1)
    total_w = sum(widths)
    svg.rect(x, y, total_w, row_height, fill=PALETTE["navy"], stroke=PALETTE["navy"], rx=14)
    cx = x
    for index, col in enumerate(columns):
        svg.text_block(cx + widths[index] / 2, y + 28, col, width_chars=max(10, widths[index] // 13), size=18, fill="#ffffff", weight=700, anchor="middle", line_gap=1.15)
        cx += widths[index]
    for row_index, row_name in enumerate(rows):
        row_y = y + row_height * (row_index + 1)
        cx = x
        for col_index, width_value in enumerate(widths):
            fill = PALETTE["panel"] if row_index % 2 == 0 else PALETTE["panel_2"]
            svg.rect(cx, row_y, width_value, row_height, fill=fill, stroke=PALETTE["line"], rx=0)
            if col_index == 0:
                svg.text_block(cx + 14, row_y + 26, row_name, width_chars=max(12, width_value // 11), size=18, fill=title_fill, weight=700)
            else:
                value = values[row_index][col_index - 1]
                svg.text_block(cx + width_value / 2, row_y + 28, value, width_chars=max(10, width_value // 12), size=16, fill=PALETTE["ink"], weight=700, anchor="middle")
            cx += width_value


def build_v01(meta: VisualMeta) -> str:
    svg = SVG(meta.title, meta.subtitle)
    cards = [
        ("1. Aerospace engineering", "Moves the delivery vehicle through air and space.\nFocus: propulsion, aerodynamics, loads, flight dynamics.", 118, PALETTE["sky"]),
        ("2. Space systems engineering", "Runs the orbital mission machine after launch.\nFocus: power, thermal, attitude control, onboard computing, payloads.", 320, PALETTE["gold_soft"]),
        ("3. Geospatial engineering", "Turns measurements linked to place into usable action.\nFocus: imagery processing, GIS, positioning, modeling, decision support.", 522, PALETTE["green_soft"]),
    ]
    for title, body, y, fill in cards:
        svg.card(150, y, 900, 150, title, body, fill=fill, accent=PALETTE["navy"])
    svg.line(600, 268, 600, 304, arrow=True)
    svg.line(600, 470, 600, 506, arrow=True)
    svg.pill(174, 664, 190, 38, "Rocket / aircraft", PALETTE["sky_2"])
    svg.pill(505, 664, 250, 38, "Satellite / payload / ground link", PALETTE["gold_soft"])
    svg.pill(830, 664, 206, 38, "Flood map / telecom plan", PALETTE["green_soft"])
    svg.footer_note("Figure reinforces Chapter 1's core stack logic.")
    return svg.render()


def build_v02(meta: VisualMeta) -> str:
    svg = SVG(meta.title, meta.subtitle)
    steps = [
        ("Acquire", "Satellites, UAVs, and gauges collect the first signal.", PALETTE["sky_2"]),
        ("Preprocess", "Correct imagery, clean radar scenes, and normalize inputs.", PALETTE["panel_2"]),
        ("Overlay", "Join flood extent with roads, terrain, districts, hospitals, and assets.", PALETTE["gold_soft"]),
        ("Model", "Add rainfall-runoff or inundation models if forecasting is needed.", PALETTE["purple_soft"]),
        ("Act", "RID, BMA, GISTDA, and local operators shift from awareness to response.", PALETTE["green_soft"]),
    ]
    x = 38
    for i, (title, body, fill) in enumerate(steps):
        svg.card(x, 180, 212, 260, title, body, fill=fill, accent=PALETTE["navy"])
        if i < len(steps) - 1:
            svg.line(x + 212, 310, x + 232, 310, arrow=True)
        x += 232
    svg.rect(110, 492, 980, 110, fill=PALETTE["panel"], stroke=PALETTE["line"], rx=18)
    svg.text(134, 532, "Why this matters", size=23, fill=PALETTE["navy"], weight=700)
    svg.text_block(134, 562, "Flood work only creates value when observation becomes location-specific operational action. The visual shows why KMITL's space layer and geospatial layer are economically linked in Thailand.", width_chars=96, size=18)
    svg.footer_note("Chao Phraya flood-monitoring workflow.")
    return svg.render()


def build_v03(meta: VisualMeta) -> str:
    svg = SVG(meta.title, meta.subtitle)
    columns = ["Capability", "Thailand", "Japan", "India", "China"]
    rows = ["Launch", "Earth observation", "Navigation", "Ground systems", "Data services", "Industrial depth"]
    values = [
        ["Limited", "Strong", "Strong", "Very strong"],
        ["Emerging", "Strong", "Strong", "Very strong"],
        ["Dependent", "Strong", "Strong", "Very strong"],
        ["Operational", "Strong", "Strong", "Very strong"],
        ["Growing", "Strong", "Strong", "Very strong"],
        ["Thin", "Strong", "Strong", "Very strong"],
    ]
    draw_comparison_table(svg, 66, 130, columns, rows, values, col_widths=[220, 170, 170, 170, 170], row_height=76)
    legend = [("Limited / Thin", PALETTE["red_soft"], PALETTE["red"]), ("Growing / Operational", PALETTE["gold_soft"], PALETTE["orange"]), ("Strong / Very strong", PALETTE["green_soft"], PALETTE["green"])]
    lx = 110
    for label, fill, text_fill in legend:
        svg.pill(lx, 658, 210 if "Strong" not in label else 230, 34, label, fill, text_fill=text_fill)
        lx += 250
    svg.footer_note("Qualitative capability ladder, not a budget chart.")
    return svg.render()


def build_v04(meta: VisualMeta) -> str:
    svg = SVG(meta.title, meta.subtitle)
    bands = [
        ("Data / applications", 1020, "Thaicom data products, GIS teams, analytics, climate and disaster use cases", PALETTE["green_soft"], PALETTE["green"]),
        ("Telecom / ground systems", 860, "NT, satcom operations, RF, GNSS, ground-segment and network work", PALETTE["sky_2"], PALETTE["navy"]),
        ("Public mission support", 690, "GISTDA, state projects, mission operations, procurement-linked technical work", PALETTE["gold_soft"], PALETTE["orange"]),
        ("Hardware manufacturing", 420, "Narrowest Thai lane: testing, components, and selected high-friction hardware roles", PALETTE["red_soft"], PALETTE["red"]),
    ]
    y = 170
    for label, width_value, note, fill, accent in bands:
        svg.rect(96, y, width_value, 92, fill=fill, stroke=accent, rx=18, filter_id="shadow")
        svg.text(122, y + 38, label, size=24, fill=PALETTE["navy"], weight=700)
        svg.text_block(122, y + 68, note, width_chars=max(26, int((width_value - 40) / 13)), size=17)
        y += 112
    svg.text_block(96, 632, "Interpretation: the degree is safest where Thai demand already exists in services, systems, and data. The hardware band is real, but visibly thinner.", width_chars=104, size=18, fill=PALETTE["muted"], weight=700)
    svg.footer_note("Visual width indicates market thickness, not numeric headcount.")
    return svg.render()


def build_v05(meta: VisualMeta) -> str:
    svg = SVG(meta.title, meta.subtitle)
    svg.card(70, 152, 485, 420, "Pure hardware path", "", fill=PALETTE["red_soft"], accent=PALETTE["red"], body_width=30)
    svg.card(645, 152, 485, 420, "GIS / data path", "", fill=PALETTE["green_soft"], accent=PALETTE["green"], body_width=30)
    rows = ["Employer count", "Capex", "Time to value", "Fallback mobility"]
    left_y = 292
    right_y = 292
    chips_left = ["Low", "High", "Slow", "Narrow"]
    chips_right = ["High", "Lower", "Fast", "Wide"]
    chip_fill_left = [PALETTE["red_soft"], PALETTE["gold_soft"], PALETTE["gold_soft"], PALETTE["red_soft"]]
    chip_fill_right = [PALETTE["green_soft"], PALETTE["green_soft"], PALETTE["green_soft"], PALETTE["green_soft"]]
    for idx, row in enumerate(rows):
        svg.text(110, left_y + idx * 68, row, size=19, fill=PALETTE["navy"], weight=700)
        svg.pill(375, left_y - 18 + idx * 68, 122, 32, chips_left[idx], chip_fill_left[idx], text_fill=PALETTE["ink"])
        svg.text(685, right_y + idx * 68, row, size=19, fill=PALETTE["navy"], weight=700)
        svg.pill(948, right_y - 18 + idx * 68, 122, 32, chips_right[idx], chip_fill_right[idx], text_fill=PALETTE["ink"])
    svg.rect(70, 622, 1060, 68, fill=PALETTE["panel_2"], stroke=PALETTE["line"], rx=16)
    svg.text_block(94, 649, "Core message: the geospatial layer is the employability buffer. It creates more immediate Thai demand and better fallback mobility than a pure hardware-first read of the degree.", width_chars=110, size=18, fill=PALETTE["navy"], weight=700)
    return svg.render()


def build_v06(meta: VisualMeta) -> str:
    svg = SVG(meta.title, meta.subtitle)
    stages = [
        ("Boundary", "Define parcels, sites, or compliance scope.", PALETTE["sky_2"]),
        ("Collect", "Use satellite, drone, field, or registry data.", PALETTE["panel_2"]),
        ("Detect", "Run change detection and evidence checks.", PALETTE["gold_soft"]),
        ("Overlay", "Join imagery with parcels, permits, and ownership.", PALETTE["purple_soft"]),
        ("Dashboard", "Summarize carbon, land, or pollution signals.", PALETTE["green_soft"]),
        ("Decision", "Move to audit, compliance, or management action.", PALETTE["panel"]),
    ]
    x = 30
    y = 196
    widths = [170, 170, 170, 170, 170, 170]
    for idx, (title, body, fill) in enumerate(stages):
        svg.card(x, y, widths[idx], 250, title, body, fill=fill, accent=PALETTE["navy"], body_width=18)
        if idx < len(stages) - 1:
            svg.line(x + widths[idx], y + 125, x + widths[idx] + 20, y + 125, arrow=True)
        x += widths[idx] + 20
    svg.rect(140, 516, 920, 110, fill=PALETTE["panel"], stroke=PALETTE["line"], rx=18)
    svg.text_block(164, 548, "This is why ESG, carbon tracking, land verification, and environmental-spatial work can absorb graduates. The value sits in the traceable chain from evidence to action, not in map aesthetics alone.", width_chars=96, size=18)
    return svg.render()


def build_v07(meta: VisualMeta) -> str:
    svg = SVG(meta.title, meta.subtitle)
    # Stylized district blocks
    districts = [
        ([(104, 150), (360, 132), (404, 286), (160, 306)], "#eef2f5"),
        ([(370, 136), (640, 148), (620, 314), (404, 286)], "#f3f6f9"),
        ([(650, 148), (1044, 174), (1028, 326), (618, 314)], "#eef3f7"),
        ([(120, 316), (400, 300), (376, 520), (146, 560)], "#f5f8fa"),
        ([(400, 304), (650, 320), (612, 548), (378, 520)], "#eef2f6"),
        ([(650, 320), (1020, 334), (986, 560), (612, 548)], "#f5f8fb"),
    ]
    for points, fill in districts:
        svg.polygon(points, fill, stroke=PALETTE["line"])
    # River
    river_points = "M530 138 C500 210 470 256 500 330 C528 406 612 456 586 546 C568 608 524 650 514 700"
    svg.path(river_points, stroke="#67a6d4", width=34, opacity=0.9)
    svg.path(river_points, stroke="#d9eefc", width=18, opacity=1)
    # Roads
    roads = [
        "M120 252 C250 226 360 228 474 250",
        "M230 392 C360 370 504 384 650 418",
        "M706 220 C826 232 914 272 1046 306",
        "M734 514 C846 498 930 510 1024 536",
        "M318 154 C314 274 316 406 310 610",
        "M792 176 C786 290 780 416 774 592",
    ]
    for road in roads:
        svg.path(road, stroke="#cad5df", width=12)
        svg.path(road, stroke="#ffffff", width=6)
    # Telemetry points
    telemetry = [(470, 270), (532, 340), (584, 420), (540, 520)]
    for x, y in telemetry:
        svg.circle(x, y, 15, fill="#2c7fb8", stroke="#ffffff", width=4)
        svg.circle(x, y, 28, fill="#67a6d4", opacity=0.16)
    # PM2.5 hotspots
    for x, y, r in [(250, 214, 48), (870, 268, 56), (930, 474, 44)]:
        svg.circle(x, y, r, fill="#f1a44d", opacity=0.18)
        svg.circle(x, y, 16, fill="#d27c1d", stroke="#ffffff", width=3)
    # Coverage cells
    for x, y in [(250, 430), (720, 410), (920, 240)]:
        svg.circle(x, y, 86, fill="none", stroke="#4ba37d", width=3, opacity=0.45)
        svg.circle(x, y, 58, fill="none", stroke="#4ba37d", width=2, opacity=0.45)
        svg.circle(x, y, 12, fill="#4ba37d", stroke="#ffffff", width=4)
    svg.text(150, 182, "North corridor", size=18, fill=PALETTE["navy"], weight=700)
    svg.text(748, 190, "Inner Bangkok", size=18, fill=PALETTE["navy"], weight=700)
    svg.text(144, 598, "East logistics belt", size=18, fill=PALETTE["navy"], weight=700)
    # Legend
    svg.rect(838, 572, 292, 124, fill=PALETTE["panel"], stroke=PALETTE["line"], rx=16, filter_id="shadow")
    svg.text(860, 602, "Legend", size=22, fill=PALETTE["navy"], weight=700)
    svg.circle(878, 628, 10, fill="#2c7fb8", stroke="#ffffff", width=3)
    svg.text(904, 634, "Flood telemetry point", size=17, fill=PALETTE["muted"], weight=700)
    svg.circle(878, 656, 12, fill="#d27c1d", stroke="#ffffff", width=3)
    svg.text(904, 662, "PM2.5 hotspot", size=17, fill=PALETTE["muted"], weight=700)
    svg.circle(878, 684, 11, fill="#4ba37d", stroke="#ffffff", width=3)
    svg.text(904, 690, "Conceptual 5G / cell coverage", size=17, fill=PALETTE["muted"], weight=700)
    svg.footer_note("Schematic city map built for concept clarity, not cadastral fidelity.")
    return svg.render()


def build_v08(meta: VisualMeta) -> str:
    svg = SVG(meta.title, meta.subtitle)
    svg.card(420, 126, 360, 120, "What do you want most?", "Start with the honest motive, not the most glamorous label.", fill=PALETTE["panel"], accent=PALETTE["navy"], body_width=38)
    branches = [
        ("Prestige / easiest recognition", 90, "Chula or other prestige-heavy route\nStronger title recognition, less hybrid identity"),
        ("Pure aerospace identity", 320, "Choose only if vehicle-centric mechanics, propulsion, and aerospace prestige are the real goal"),
        ("Hybrid space + GIS", 550, "KMITL's best-fit lane\nTelecom, sensing, GNSS, GIS, and systems logic"),
        ("Pure geospatial depth", 780, "Choose a GIS-first or survey-first program if Earth-side analysis is the whole point"),
        ("Postgraduate specialization", 1010, "Generalist now, specialize harder later if master's study is already part of the plan"),
    ]
    for label, cx, body in branches:
        svg.line(600, 246, cx, 312, arrow=True)
        svg.card(cx - 100, 332, 200, 260, label, body, fill=PALETTE["panel_2"], accent=PALETTE["sky"], body_width=17, title_size=21)
    return svg.render()


def build_v09(meta: VisualMeta) -> str:
    svg = SVG(meta.title, meta.subtitle)
    steps = [
        ("Heavy coursework", "Math, labs, projects, and deadlines pile up."),
        ("Missed milestone", "One report, practical, or team checkpoint slips."),
        ("Weak grades / incomplete project", "The first miss spreads into multiple courses."),
        ("Registration / fee / status issue", "Administrative friction begins to matter."),
        ("Leave / paperwork", "Formal status management replaces ordinary studying."),
        ("Longer graduation timeline", "Delay compounds into cost, morale, and opportunity loss."),
    ]
    x = 110
    y = 156
    for idx, (title, body) in enumerate(steps):
        svg.card(x + idx * 130, y + idx * 74, 360, 106, title, body, fill=PALETTE["panel"], accent=PALETTE["red"], body_width=34)
        if idx < len(steps) - 1:
            svg.line(x + idx * 130 + 360, y + idx * 74 + 54, x + (idx + 1) * 130, y + (idx + 1) * 74 + 54, arrow=True)
    svg.rect(116, 646, 964, 60, fill=PALETTE["panel_2"], stroke=PALETTE["line"], rx=16)
    svg.text_block(140, 674, "Why this visual matters: Chapter 5's risk is usually cumulative drift, not one dramatic collapse. Early intervention changes the whole chain.", width_chars=110, size=18, fill=PALETTE["navy"], weight=700)
    return svg.render()


def build_v10(meta: VisualMeta) -> str:
    svg = SVG(meta.title, meta.subtitle)
    svg.card(66, 210, 240, 132, "Math foundations", "Calculus, linear algebra, differential equations, probability.", fill=PALETTE["sky_2"], accent=PALETTE["navy"], body_width=20)
    svg.card(66, 400, 240, 132, "Programming habits", "Computer programming, OOP, debugging, problem decomposition.", fill=PALETTE["panel_2"], accent=PALETTE["navy"], body_width=20)
    svg.card(392, 210, 260, 132, "Signals / circuits / electromagnetics", "The real engineering filter: abstraction plus physical systems.", fill=PALETTE["gold_soft"], accent=PALETTE["orange"], body_width=24)
    svg.line(306, 274, 392, 274, arrow=True)
    svg.line(306, 466, 392, 334, arrow=True)
    targets = [
        ("Orbital mechanics", 774, 126),
        ("Remote sensing", 938, 254),
        ("GIS", 774, 382),
        ("GNSS", 938, 510),
        ("Spacecraft systems", 774, 638),
    ]
    for label, x, y in targets:
        svg.card(x, y, 250, 92, label, "Upper-year application area", fill=PALETTE["panel"], accent=PALETTE["green"], body_width=20, title_size=21, body_size=16)
    for _, x, y in targets:
        svg.line(652, 276, x, y + 46, arrow=True)
    return svg.render()


def build_v11(meta: VisualMeta) -> str:
    svg = SVG(meta.title, meta.subtitle)
    sources = [
        ("Linear algebra + differential equations", 70, 170, PALETTE["sky_2"]),
        ("Object-oriented programming", 70, 370, PALETTE["panel_2"]),
        ("Electric circuit analysis", 70, 570, PALETTE["gold_soft"]),
    ]
    mids = [
        ("Signals and systems", 450, 140, PALETTE["panel"]),
        ("Orbital mechanics", 450, 300, PALETTE["panel"]),
        ("Embedded systems", 450, 460, PALETTE["panel"]),
        ("Remote sensing + GIS + Spatial AI", 450, 620, PALETTE["green_soft"]),
    ]
    for title, x, y, fill in sources:
        svg.card(x, y, 270, 108, title, "Year 2 dependency source", fill=fill, accent=PALETTE["navy"], body_width=24, title_size=21, body_size=16)
    for title, x, y, fill in mids:
        svg.card(x, y, 300, 100, title, "Courses or stacks that build on it", fill=fill, accent=PALETTE["navy"], body_width=26, title_size=20, body_size=16)
    arrows = [
        ((340, 224), (450, 190)),
        ((340, 224), (450, 350)),
        ((340, 624), (450, 510)),
        ((340, 424), (450, 510)),
        ((340, 424), (450, 670)),
        ((340, 624), (450, 670)),
        ((340, 224), (450, 670)),
    ]
    for (x1, y1), (x2, y2) in arrows:
        svg.line(x1, y1, x2, y2, arrow=True)
    svg.rect(820, 230, 300, 260, fill=PALETTE["panel_2"], stroke=PALETTE["line"], rx=18)
    svg.text(844, 268, "Read it this way", size=22, fill=PALETTE["navy"], weight=700)
    svg.text_block(844, 302, "Year 2 is not a flat list of subjects. It is where abstraction compounds. Students who miss the mathematical or coding base feel the strain later in GIS, GNSS, AI, and systems classes.", width_chars=28, size=18)
    return svg.render()


def build_v12(meta: VisualMeta) -> str:
    svg = SVG(meta.title, meta.subtitle)
    stages = [
        ("GNSS / GIS / Spatial AI / Satcom classes", 46),
        ("Lab output", 244),
        ("Team project", 442),
        ("Industrial training", 640),
        ("Capstone or co-op", 838),
        ("Job interview portfolio", 1036),
    ]
    for idx, (title, x) in enumerate(stages):
        svg.card(x, 220, 160, 190, title, "Must become proof, not only coursework.", fill=PALETTE["panel"], accent=PALETTE["navy"], body_width=16, title_size=19, body_size=16)
        if idx < len(stages) - 1:
            svg.line(x + 160, 315, x + 198, 315, arrow=True)
    svg.rect(126, 490, 948, 126, fill=PALETTE["green_soft"], stroke=PALETTE["green"], rx=18)
    svg.text(154, 530, "Conversion rule", size=24, fill=PALETTE["navy"], weight=700)
    svg.text_block(154, 562, "Upper-year value compounds only when every stage leaves an artifact: code, map product, model result, employer reference, operations note, or capstone proof that a recruiter can inspect.", width_chars=100, size=18)
    return svg.render()


def build_v13(meta: VisualMeta) -> str:
    svg = SVG(meta.title, meta.subtitle)
    svg.card(410, 116, 380, 106, "Do you already have a strong employer placement?", "The choice should follow quality and conversion probability, not status anxiety.", fill=PALETTE["panel"], accent=PALETTE["navy"], body_width=40)
    svg.line(600, 222, 360, 300, arrow=True)
    svg.line(600, 222, 840, 300, arrow=True)
    svg.card(210, 320, 300, 120, "Yes", "A good placement with real work and conversion upside usually favors co-op.", fill=PALETTE["green_soft"], accent=PALETTE["green"], body_width=26)
    svg.card(690, 320, 300, 120, "No", "Ask what kind of proof you still need before graduation.", fill=PALETTE["gold_soft"], accent=PALETTE["orange"], body_width=26)
    svg.line(840, 440, 690, 528, arrow=True)
    svg.line(840, 440, 990, 528, arrow=True)
    svg.card(540, 548, 260, 132, "Need stronger portfolio / job conversion", "Prefer co-op if the placement is real, supervised, and path-matched.", fill=PALETTE["panel"], accent=PALETTE["navy"], body_width=22)
    svg.card(860, 548, 260, 132, "Targeting master's / research / deeper technical project", "Prefer capstone if project quality and supervision are strong.", fill=PALETTE["panel"], accent=PALETTE["navy"], body_width=22)
    svg.card(94, 548, 320, 132, "Already in a strong employer lane", "Co-op is the cleaner signal when the placement itself is the asset.", fill=PALETTE["panel"], accent=PALETTE["green"], body_width=28)
    return svg.render()


def build_v14(meta: VisualMeta) -> str:
    svg = SVG(meta.title, meta.subtitle)
    svg.rect(100, 260, 980, 110, fill="#eff4f8", stroke=PALETTE["line"], rx=20)
    segments = [
        (100, 340, "RF lab / GNSS / ground systems / teleport", PALETTE["green_soft"], PALETTE["green"]),
        (460, 220, "AIT testing", PALETTE["gold_soft"], PALETTE["orange"]),
        (760, 140, "Satellite component manufacturing", PALETTE["red_soft"], PALETTE["red"]),
    ]
    for x, w, label, fill, accent in segments:
        svg.rect(x, 282, w, 66, fill=fill, stroke=accent, rx=14)
        svg.text_block(x + w / 2, 320, label, width_chars=max(18, w // 11), size=18, fill=PALETTE["navy"], weight=700, anchor="middle")
    svg.path("M210 420 L210 520 L520 520", stroke=PALETTE["green"], width=6)
    svg.text_block(110, 450, "Largest Thai opportunity zone", width_chars=20, size=18, fill=PALETTE["green"], weight=700)
    svg.rect(650, 428, 420, 170, fill=PALETTE["panel"], stroke=PALETTE["line"], rx=18)
    svg.text(674, 464, "Interpretation", size=23, fill=PALETTE["navy"], weight=700)
    svg.text_block(674, 500, "The hardware path is wider than clean-room assembly but narrower than the whole degree. Thailand pays most naturally for RF, GNSS, ground systems, testing, and operations-facing technical work.", width_chars=38, size=18)
    return svg.render()


def build_v15(meta: VisualMeta) -> str:
    svg = SVG(meta.title, meta.subtitle)
    # Grid
    x0, y0, size = 160, 170, 420
    svg.rect(x0, y0, size, size, fill=PALETTE["panel"], stroke=PALETTE["line"], rx=18)
    for step in range(1, 4):
        pos = x0 + step * size / 4
        svg.line(pos, y0, pos, y0 + size, color=PALETTE["line"], width=2)
        pos_y = y0 + step * size / 4
        svg.line(x0, pos_y, x0 + size, pos_y, color=PALETTE["line"], width=2)
    svg.text(x0 + size / 2, y0 + size + 44, "Physical strain", size=21, fill=PALETTE["navy"], weight=700, anchor="middle")
    svg.text(x0 - 90, y0 + size / 2, "Mental intensity", size=21, fill=PALETTE["navy"], weight=700, anchor="middle")
    items = [
        ("RF lab", 0.40, 0.76, PALETTE["sky"]),
        ("Teleport operations", 0.54, 0.68, PALETTE["green"]),
        ("Embedded bench work", 0.24, 0.80, PALETTE["purple"]),
        ("Clean-room AIT", 0.72, 0.74, PALETTE["orange"]),
    ]
    for label, px, py, color in items:
        cx = x0 + px * size
        cy = y0 + (1 - py) * size
        svg.circle(cx, cy, 24, fill=color, stroke="#ffffff", width=4)
        svg.text_block(cx + 38, cy + 8, label, width_chars=16, size=18, fill=PALETTE["navy"], weight=700)
    svg.rect(650, 182, 420, 364, fill=PALETTE["panel_2"], stroke=PALETTE["line"], rx=18)
    svg.text(674, 222, "How to read it", size=23, fill=PALETTE["navy"], weight=700)
    svg.text_block(674, 258, "The matrix fights a common misconception: technical prestige does not map neatly to one kind of workload. Clean-room AIT is physically stricter than embedded bench work, while embedded or RF work can be mentally more sustained. Choose the path that matches your real working style, not the aura around it.", width_chars=38, size=18)
    return svg.render()


def build_v16(meta: VisualMeta) -> str:
    svg = SVG(meta.title, meta.subtitle)
    stages = [
        ("Raw data", "Imagery, vectors, GPS, surveys, admin layers", PALETTE["sky_2"]),
        ("Cleaning + CRS checks", "Fix geometry, metadata, duplicates, coordinate systems", PALETTE["panel"]),
        ("Analysis + modeling", "Spatial joins, rules, statistics, ML, QA", PALETTE["gold_soft"]),
        ("Delivery outputs", "Maps, dashboards, APIs, reports, layers", PALETTE["purple_soft"]),
        ("Operational use", "Client decision, internal workflow, risk response", PALETTE["green_soft"]),
    ]
    x = 50
    for idx, (title, body, fill) in enumerate(stages):
        svg.card(x, 212, 208, 232, title, body, fill=fill, accent=PALETTE["navy"], body_width=19)
        if idx < len(stages) - 1:
            svg.line(x + 208, 328, x + 230, 328, arrow=True)
        x += 230
    svg.rect(126, 516, 948, 96, fill=PALETTE["panel"], stroke=PALETTE["line"], rx=18)
    svg.text_block(150, 548, "The point of the data/GIS lane is delivery discipline. The map is not the job. The usable chain from messy input to trusted operational output is the job.", width_chars=102, size=18, fill=PALETTE["navy"], weight=700)
    return svg.render()


def build_v17(meta: VisualMeta) -> str:
    svg = SVG(meta.title, meta.subtitle)
    source_boxes = [
        ("NSDC / satellite feeds", 70, 160),
        ("Drones + imagery", 70, 286),
        ("Internal GIS / asset data", 70, 412),
        ("Surveys + field reports", 70, 538),
    ]
    for label, x, y in source_boxes:
        svg.card(x, y, 240, 88, label, "Source layer", fill=PALETTE["panel"], accent=PALETTE["navy"], body_width=18, title_size=20, body_size=16)
        svg.line(310, y + 44, 420, 340, arrow=True)
    svg.card(420, 228, 300, 232, "Python / GEE / GIS processing", "Clean, align, clip, derive features, run rules or models, then prepare outputs for review.", fill=PALETTE["gold_soft"], accent=PALETTE["orange"], body_width=28)
    svg.card(810, 228, 260, 110, "Model or rule-based analysis", "Classification, scoring, anomaly detection, trend logic.", fill=PALETTE["purple_soft"], accent=PALETTE["purple"], body_width=22)
    svg.card(810, 366, 260, 110, "QA", "Validate assumptions, edge cases, and obvious errors before delivery.", fill=PALETTE["panel"], accent=PALETTE["navy"], body_width=22)
    svg.card(810, 504, 260, 110, "Dashboard / map service / report", "Operational surface that stakeholders can actually use.", fill=PALETTE["green_soft"], accent=PALETTE["green"], body_width=22)
    svg.line(720, 344, 810, 282, arrow=True)
    svg.line(720, 344, 810, 420, arrow=True)
    svg.line(940, 476, 940, 504, arrow=True)
    return svg.render()


def build_v18(meta: VisualMeta) -> str:
    svg = SVG(meta.title, meta.subtitle)
    svg.line(120, 380, 1080, 380, color=PALETTE["navy"], width=5)
    times = ["08:30", "10:30", "12:00", "14:00", "16:00", "18:00"]
    xs = [140, 320, 500, 680, 860, 1040]
    for x, label in zip(xs, times):
        svg.line(x, 360, x, 400, color=PALETTE["navy"], width=4)
        svg.text(x, 430, label, size=18, fill=PALETTE["navy"], weight=700, anchor="middle")
    blocks = [
        (140, 230, 180, 92, "Morning data pull + script work", PALETTE["sky_2"]),
        (320, 474, 180, 92, "Validation, QA, issue triage", PALETTE["panel"]),
        (500, 230, 180, 92, "Team sync / stakeholder check-in", PALETTE["gold_soft"]),
        (680, 474, 180, 92, "Model runs, dashboards, report drafting", PALETTE["purple_soft"]),
        (860, 230, 180, 92, "Ad hoc requests / revisions / follow-ups", PALETTE["green_soft"]),
        (1040, 474, 180, 92, "End-of-day pipeline and delivery checks", PALETTE["panel_2"]),
    ]
    for x, y, w, h, title, fill in blocks:
        svg.card(x - w / 2, y, w, h, title, "", fill=fill, accent=PALETTE["navy"], body_width=16, title_size=18, body_size=15)
        svg.line(x, 380, x, y + (h if y < 380 else 0), color=PALETTE["line"], width=3, dashed=True)
    svg.rect(130, 620, 940, 70, fill=PALETTE["panel"], stroke=PALETTE["line"], rx=16)
    svg.text_block(154, 648, "Daily reality: more pipeline ownership and stakeholder communication than most students imagine, but usually more flexibility than hardware lab or shift-heavy work.", width_chars=106, size=18)
    return svg.render()


def build_v19(meta: VisualMeta) -> str:
    svg = SVG(meta.title, meta.subtitle)
    stages = [
        ("Degree title", 120, 170, 260, 100, PALETTE["panel_2"]),
        ("Translated skills", 230, 308, 300, 110, PALETTE["sky_2"]),
        ("Employer category", 350, 466, 320, 118, PALETTE["gold_soft"]),
        ("Actual role title", 470, 630, 320, 118, PALETTE["purple_soft"]),
        ("Interview proof", 590, 790, 320, 118, PALETTE["green_soft"]),
    ]
    for idx, (x, y, w, h, fill) in enumerate([(120,170,260,100,PALETTE["panel_2"]), (230,308,300,110,PALETTE["sky_2"]), (350,466,320,118,PALETTE["gold_soft"]), (470,630,320,118,PALETTE["purple_soft"]), (590,790,320,118,PALETTE["green_soft"])]):
        pass
    labels = [
        ("Degree title", "Bachelor of Engineering in Space and Geospatial Engineering"),
        ("Translated skills", "Python, GIS, remote sensing, GNSS, networking, systems thinking"),
        ("Employer category", "Thaicom, CDG, ERM, GISTDA, enterprise planning, implementation firms"),
        ("Actual role title", "GIS Analyst, Geospatial Data Analyst, Satellite Control Engineer, GIS Consultant"),
        ("Interview proof", "Portfolio, code, map product, tooling depth, role-specific explanation"),
    ]
    x, y = 94, 176
    widths = [220, 250, 280, 290, 300]
    fills = [PALETTE["panel_2"], PALETTE["sky_2"], PALETTE["gold_soft"], PALETTE["purple_soft"], PALETTE["green_soft"]]
    for idx, ((title, body), width_value, fill) in enumerate(zip(labels, widths, fills)):
        svg.card(x, y, width_value, 164, title, body, fill=fill, accent=PALETTE["navy"], body_width=max(18, width_value // 12), title_size=21)
        if idx < len(labels) - 1:
            next_x = x + width_value + 28
            svg.line(x + width_value, y + 82, next_x, y + 82, arrow=True)
        x += width_value + 28
        y += 44
    return svg.render()


def build_v20(meta: VisualMeta) -> str:
    svg = SVG(meta.title, meta.subtitle)
    data = [
        ("GIS & implementation roles", 88, PALETTE["green"]),
        ("Consulting", 74, PALETTE["sky"]),
        ("Field / UAV roles", 62, PALETTE["orange"]),
        ("Satellite operations", 46, PALETTE["purple"]),
        ("Public-sector windows", 35, PALETTE["gold"]),
        ("Pure space-hardware roles", 20, PALETTE["red"]),
    ]
    x0, x1, y = 280, 1040, 182
    svg.text(x0, 146, "Lower entry friction", size=18, fill=PALETTE["muted"], weight=700)
    svg.text(x1, 146, "Higher entry friction", size=18, fill=PALETTE["muted"], weight=700, anchor="end")
    for label, value, color in data:
        svg.text(78, y + 18, label, size=19, fill=PALETTE["navy"], weight=700)
        svg.rect(x0, y - 12, x1 - x0, 30, fill="#edf2f6", stroke=PALETTE["line"], rx=12)
        svg.rect(x0, y - 12, (x1 - x0) * value / 100, 30, fill=color, stroke=color, rx=12)
        svg.text(x0 + (x1 - x0) * value / 100 + 16, y + 10, f"{value}", size=17, fill=PALETTE["ink"], weight=700)
        y += 86
    svg.rect(92, 646, 1016, 64, fill=PALETTE["panel"], stroke=PALETTE["line"], rx=16)
    svg.text_block(116, 672, "Interpretation: the market is thickest where employers already recognize implementation, GIS delivery, and adjacent digital work. Entry friction rises as the lane becomes narrower or more identity-rich.", width_chars=112, size=18)
    return svg.render()


def build_v21(meta: VisualMeta) -> str:
    svg = SVG(meta.title, meta.subtitle)
    # Left ladder
    left_steps = [
        ("Entry", "GIS analyst / assistant GIS engineer"),
        ("Mid", "Geospatial data analyst / consultant"),
        ("Senior", "Lead analyst / solution owner / project lead"),
        ("Top", "Platform, product, commercial, or domain authority"),
    ]
    right_steps = [
        ("Entry", "Satellite control / systems support"),
        ("Mid", "Satcom / RF / ground systems engineer"),
        ("Senior", "Systems lead / mission operations lead"),
        ("Top", "Specialist authority / infrastructure leadership"),
    ]
    x_positions = [150, 270, 390, 510]
    for (label, body), x in zip(left_steps, x_positions):
        svg.card(x, 280 - (x - 150) * 0.2, 180, 120, label, body, fill=PALETTE["green_soft"], accent=PALETTE["green"], body_width=18, title_size=20, body_size=16)
    for (label, body), x in zip(left_steps[:-1], x_positions[:-1]):
        pass
    svg.line(330, 340, 390, 320, arrow=True)
    svg.line(450, 320, 510, 300, arrow=True)
    svg.line(570, 300, 630, 280, arrow=True)
    right_x = [760, 860, 960, 1060]
    for (label, body), x in zip(right_steps, right_x):
        svg.card(x, 318 - (x - 760) * 0.35, 170, 116, label, body, fill=PALETTE["sky_2"], accent=PALETTE["navy"], body_width=17, title_size=19, body_size=16)
    svg.line(930, 352, 960, 332, arrow=True)
    svg.line(1030, 332, 1060, 312, arrow=True)
    svg.line(1130, 312, 1160, 292, arrow=True)
    svg.text(184, 192, "Broader GIS / data ladder", size=24, fill=PALETTE["green"], weight=700)
    svg.text(790, 192, "Narrower satcom / systems ladder", size=24, fill=PALETTE["navy"], weight=700)
    svg.rect(150, 600, 950, 74, fill=PALETTE["panel"], stroke=PALETTE["line"], rx=16)
    svg.text_block(174, 628, "Both ladders can reach authority and leadership, but the GIS/data side branches wider while the satcom/systems side stays more selective and path-dependent.", width_chars=106, size=18)
    return svg.render()


def build_v22(meta: VisualMeta) -> str:
    svg = SVG(meta.title, meta.subtitle)
    x0, x1 = 280, 1070
    axis_ticks = [0, 50000, 100000, 150000, 180000]
    for tick in axis_ticks:
        x = scale(tick, 0, 180000, x0, x1)
        svg.line(x, 154, x, 628, color=PALETTE["line"], width=2)
        label = "180k+" if tick == 180000 else f"{int(tick/1000)}k"
        svg.text(x, 138, label, size=16, fill=PALETTE["muted"], weight=700, anchor="middle")
    roles = [
        ("GIS analyst / assistant GIS", (25000, 40000), (40000, 70000), (70000, 110000)),
        ("Geospatial data / remote sensing", (35000, 60000), (60000, 110000), (100000, 150000)),
        ("GIS consulting", (30000, 50000), (50000, 90000), (90000, 140000)),
        ("Satcom / ground systems / RF", (28000, 45000), (45000, 80000), (70000, 130000)),
        ("Platform / data management lead", None, (60000, 120000), (100000, 180000)),
    ]
    y = 196
    colors = [("#d9e8f2", PALETTE["navy"]), ("#f8f1dd", PALETTE["orange"]), ("#eaf5ef", PALETTE["green"])]
    for label, entry, mid, senior in roles:
        svg.text_block(72, y + 12, label, width_chars=24, size=18, fill=PALETTE["navy"], weight=700)
        for idx, band in enumerate([entry, mid, senior]):
            if not band:
                continue
            start, end = band
            x_start = scale(start, 0, 180000, x0, x1)
            x_end = scale(end, 0, 180000, x0, x1)
            fill, stroke = colors[idx]
            bar_y = y - 10 + idx * 18
            svg.rect(x_start, bar_y, x_end - x_start, 14, fill=fill, stroke=stroke, rx=7)
        y += 88
    svg.pill(332, 654, 120, 32, "Entry", "#d9e8f2")
    svg.pill(470, 654, 120, 32, "Mid", "#f8f1dd")
    svg.pill(608, 654, 120, 32, "Senior", "#eaf5ef")
    svg.footer_note("Indicative THB per month ranges from Chapter 12.")
    return svg.render()


def build_v23(meta: VisualMeta) -> str:
    svg = SVG(meta.title, meta.subtitle)
    levels = [
        ("Thailand-first growth", 1040, PALETTE["green_soft"], "Best realism: build proof locally, then move with evidence."),
        ("Regional downstream move", 920, PALETTE["sky_2"], "Singapore and Southeast Asia downstream geospatial work."),
        ("Master's-first path", 780, PALETTE["gold_soft"], "Adds credibility, resets geography, and opens research-led entry."),
        ("Japan / Europe civil route", 620, PALETTE["purple_soft"], "Possible, but narrower and often language or institution filtered."),
        ("U.S. commercial", 430, PALETTE["orange_soft"], "Harder due to distance, competition, and path sequencing."),
        ("Direct U.S. defense entry", 260, PALETTE["red_soft"], "Highest friction because export-control and nationality realities matter."),
    ]
    top = 150
    height = 86
    for idx, (label, width_value, fill, note) in enumerate(levels):
        x = (W - width_value) / 2
        points = [(x + 24, top), (x + width_value - 24, top), (x + width_value, top + height), (x, top + height)]
        svg.polygon(points, fill=fill, stroke=PALETTE["line"])
        svg.text(x + width_value / 2, top + 34, label, size=22, fill=PALETTE["navy"], weight=700, anchor="middle")
        svg.text_block(x + width_value / 2, top + 58, note, width_chars=max(24, int(width_value / 14)), size=17, fill=PALETTE["muted"], anchor="middle")
        top += 92
    svg.footer_note("Wider bands = more realistic sequencing for most Thai students.")
    return svg.render()


def build_v24(meta: VisualMeta) -> str:
    svg = SVG(meta.title, meta.subtitle)
    data = [
        ("GIS-specialized roles", 14, PALETTE["red"]),
        ("Telecom roles", 78, PALETTE["orange"]),
        ("Network roles", 84, PALETTE["sky"]),
        ("Cloud roles", 88, PALETTE["purple"]),
        ("Data roles", 92, PALETTE["green"]),
    ]
    x0, x1, y = 300, 1060, 202
    svg.text(x0, 158, "Narrower visible opening volume", size=18, fill=PALETTE["muted"], weight=700)
    svg.text(x1, 158, "Broader visible opening volume", size=18, fill=PALETTE["muted"], weight=700, anchor="end")
    for label, value, color in data:
        svg.text(92, y + 18, label, size=20, fill=PALETTE["navy"], weight=700)
        svg.rect(x0, y - 10, x1 - x0, 34, fill="#edf2f6", stroke=PALETTE["line"], rx=14)
        svg.rect(x0, y - 10, (x1 - x0) * value / 100, 34, fill=color, stroke=color, rx=14)
        svg.text(x0 + (x1 - x0) * value / 100 + 16, y + 12, f"{value}", size=17, fill=PALETTE["ink"], weight=700)
        y += 96
    svg.rect(100, 660, 990, 60, fill=PALETTE["panel"], stroke=PALETTE["line"], rx=16)
    svg.text_block(124, 686, "Reading: the degree becomes safer when it can translate into adjacent, thicker markets rather than waiting for a pure space or narrow GIS opening.", width_chars=106, size=18, fill=PALETTE["navy"], weight=700)
    return svg.render()


def build_v25(meta: VisualMeta) -> str:
    svg = SVG(meta.title, meta.subtitle)
    svg.card(390, 114, 420, 110, "What kind of work do you actually enjoy?", "Choose the lane by work style, not by the fanciest label.", fill=PALETTE["panel"], accent=PALETTE["navy"], body_width=44)
    branches = [
        ("I like data", 140, PALETTE["green_soft"], "Build Python, SQL, one end-to-end pipeline, and a spatial-data project."),
        ("I like operations", 390, PALETTE["sky_2"], "Lean into satcom, GNSS, systems logs, reliability, and troubleshooting."),
        ("I like infrastructure", 640, PALETTE["purple_soft"], "Build Linux, networking, cloud basics, and one deployed system."),
        ("I like client-facing GIS", 890, PALETTE["gold_soft"], "Build ArcGIS or QGIS delivery, domain context, and explanation skills."),
    ]
    for label, x, fill, body in branches:
        svg.line(600, 224, x + 100, 310, arrow=True)
        svg.card(x, 332, 200, 240, label, body, fill=fill, accent=PALETTE["navy"], body_width=18, title_size=20)
    svg.rect(94, 620, 1010, 72, fill=PALETTE["panel"], stroke=PALETTE["line"], rx=16)
    svg.text_block(118, 648, "Action rule: pick one primary lane, then accumulate proof in the same language for at least 12 to 18 months before trying to market yourself broadly.", width_chars=108, size=18)
    return svg.render()


def build_v26(meta: VisualMeta) -> str:
    svg = SVG(meta.title, meta.subtitle)
    years = [
        ("Year 1", "Survival + habits", "Math, physics, coding basics, mini project.", PALETTE["sky_2"]),
        ("Year 2", "Lane choice + lab entry", "Decide whether your gravity is GIS/data, satcom, systems, or hardware-adjacent.", PALETTE["gold_soft"]),
        ("Year 3", "External proof", "Industrial training, one path-matched credential, and a serious project artifact.", PALETTE["purple_soft"]),
        ("Year 4", "Conversion", "Capstone or co-op becomes the bridge to a job, graduate study, or regional move.", PALETTE["green_soft"]),
    ]
    x = 54
    for idx, (label, headline, body, fill) in enumerate(years):
        svg.card(x, 220, 248, 260, label, headline + "\n" + body, fill=fill, accent=PALETTE["navy"], body_width=22, title_size=24)
        if idx < len(years) - 1:
            svg.line(x + 248, 350, x + 284, 350, arrow=True)
        x += 284
    svg.rect(112, 560, 976, 108, fill=PALETTE["panel"], stroke=PALETTE["line"], rx=18)
    svg.text(138, 598, "Core sequencing rule", size=23, fill=PALETTE["navy"], weight=700)
    svg.text_block(138, 628, "Do not optimize for activity count. Optimize for artifacts and references that make the next year easier. Every year should leave one proof asset that survives into the next one.", width_chars=108, size=18)
    return svg.render()


def build_v27(meta: VisualMeta) -> str:
    svg = SVG(meta.title, meta.subtitle)
    svg.card(64, 152, 500, 470, "Go", "", fill=PALETTE["green_soft"], accent=PALETTE["green"], body_width=30)
    svg.card(636, 152, 500, 470, "No-Go", "", fill=PALETTE["red_soft"], accent=PALETTE["red"], body_width=30)
    y_go = 252
    y_no = 252
    for idx, item in enumerate(["Technically serious", "Comfortable with math, coding, and abstraction", "Willing to build a portfolio", "Market-realistic about Thai demand", "Okay with KMITL and Lat Krabang trade-offs"]):
        svg.circle(100, y_go + idx * 66, 12, fill=PALETTE["green"], stroke="#ffffff", width=3)
        svg.text_block(126, y_go + 8 + idx * 66, item, width_chars=34, size=18, fill=PALETTE["navy"], weight=700)
    for idx, item in enumerate(["Main motive is prestige or vague space romance", "Wants automatic employer recognition", "Dislikes math, coding, and systems thinking", "Needs a guaranteed hardware boom", "Will stay passive and wait for the title to explain itself"]):
        svg.circle(672, y_no + idx * 66, 12, fill=PALETTE["red"], stroke="#ffffff", width=3)
        svg.text_block(698, y_no + 8 + idx * 66, item, width_chars=34, size=18, fill=PALETTE["navy"], weight=700)
    svg.rect(142, 648, 916, 58, fill=PALETTE["panel"], stroke=PALETTE["line"], rx=16)
    svg.text_block(166, 674, "Bottom line: this degree is a conditional go for a portfolio-driven student and a no-go for someone hoping the word space will do the work for them.", width_chars=98, size=18, fill=PALETTE["navy"], weight=700)
    return svg.render()


VISUALS: list[VisualMeta] = [
    VisualMeta("V-01", 1, "1.1", "visual-v01.svg", "From Rocket to Decision", "Three stacked layers inside the degree", "Aerospace moves the delivery vehicle, space systems run the orbital machine, and geospatial engineering converts measurements into decisions.", "Three-layer stack from aerospace delivery vehicle to space systems payload to geospatial decision layer.", "Diagram", "Built", "No"),
    VisualMeta("V-02", 1, "1.2", "visual-v02.svg", "Flood Intelligence Pipeline", "How a Thai flood workflow turns sensing into action", "Satellite and UAV acquisition only create value when preprocessing, GIS overlay, modeling, and response action are connected in one chain.", "Workflow diagram showing flood intelligence from sensing to operational response.", "Workflow", "Built", "No"),
    VisualMeta("V-03", 2, "2.1", "visual-v03.svg", "Global Capability Ladder", "Thailand compared with Japan, India, and China", "A qualitative capability matrix makes Thailand's position legible without pretending to know exact budget numbers or unit economics.", "Capability matrix comparing Thailand, Japan, India, and China across space-sector depth.", "Capability matrix", "Built", "No"),
    VisualMeta("V-04", 2, "2.2", "visual-v04.svg", "Thai Space Value Chain Thickness", "Where labor demand is thick versus thin", "The degree is safest where Thailand already has downstream services, telecom-ground work, and public mission support rather than narrow hardware manufacturing depth.", "Horizontal thickness bands across the Thai space value chain.", "Diagram", "Built", "No"),
    VisualMeta("V-05", 3, "3.1", "visual-v05.svg", "Why GIS Is the Safety Net", "Pure hardware versus GIS and data", "The geospatial layer is the employability buffer because it usually offers broader employer count, faster time-to-value, and better fallback mobility than a pure hardware-first path.", "Two-column comparison of pure hardware and GIS or data pathways.", "Comparison chart", "Built", "No"),
    VisualMeta("V-06", 3, "3.2", "visual-v06.svg", "From Imagery to ESG Decision", "Spatial evidence as a compliance-grade workflow", "GIS and remote sensing matter economically when they turn land or environmental evidence into a traceable business or compliance decision.", "Workflow from boundary definition to ESG or compliance decision.", "Workflow", "Built", "No"),
    VisualMeta("V-07", 3, "3.3", "visual-v07.svg", "Bangkok-Style Urban GIS Stack", "A schematic city map showing layered geospatial signals", "This dossier build uses a schematic map to show how flood telemetry, PM2.5 hotspots, road structure, and conceptual telecom coverage can live in one urban GIS workflow.", "Schematic Bangkok-style map with telemetry, pollution hotspots, roads, and coverage cells.", "Map", "Built", "No"),
    VisualMeta("V-08", 4, "4.1", "visual-v08.svg", "Who Should Choose KMITL?", "Decision tree across prestige, aerospace, hybrid, and GIS options", "The degree makes sense only for a specific student profile, and this tree forces that choice through motive instead of vague prestige impressions.", "Decision tree for choosing KMITL versus other program types.", "Decision tree", "Built", "No"),
    VisualMeta("V-09", 5, "5.1", "visual-v09.svg", "How Overload Becomes Delay", "Academic pressure as a cumulative system", "Chapter 5's main risk is accumulation: missed milestones and administrative friction often create a longer graduation timeline before students realize how much has slipped.", "Workflow from heavy coursework to delayed graduation timeline.", "Workflow", "Built", "No"),
    VisualMeta("V-10", 6, "6.1", "visual-v10.svg", "Years 1-2 Dependency Chain", "The first half of the degree is a prerequisite system", "The early curriculum is not a flat list of courses. It is a dependency chain that feeds the upper-year identity of the program.", "Dependency diagram from Year 1 foundations to upper-year subjects.", "Diagram", "Built", "No"),
    VisualMeta("V-11", 6, "6.2", "visual-v11.svg", "Year 2 Mathematical Coupling", "What feeds later systems, GIS, and spatial AI work", "Linear algebra, differential equations, circuits, and OOP do not stay isolated. They compound directly into later signals, embedded, remote-sensing, and GIS-heavy coursework.", "Dependency map linking Year 2 courses to later technical work.", "Dependency map", "Built", "No"),
    VisualMeta("V-12", 7, "7.1", "visual-v12.svg", "Convert Year 3 into Employability", "Upper-year coursework must become proof", "The highest-value upper-year sequence is classes to lab output to training to capstone or co-op to portfolio proof that employers can inspect.", "Workflow turning upper-year courses into employability proof.", "Workflow", "Built", "No"),
    VisualMeta("V-13", 7, "7.2", "visual-v13.svg", "Capstone or Co-op?", "Pick the branch that creates the stronger signal", "Capstone versus co-op should be a strategic decision tied to placement quality, conversion odds, and research ambition, not a status reflex.", "Decision tree for choosing capstone or co-op.", "Decision tree", "Built", "No"),
    VisualMeta("V-14", 8, "8.1", "visual-v14.svg", "What the Hardware Path Really Means", "A wider spectrum than students often imagine", "In Thailand, the hardware path naturally includes RF, GNSS, teleport, ground systems, and testing work long before it reaches narrow spacecraft manufacturing roles.", "Spectrum from RF and ground systems to hardware manufacturing.", "Diagram", "Built", "No"),
    VisualMeta("V-15", 8, "8.2", "visual-v15.svg", "Hardware Workload Matrix", "Physical strain versus mental intensity", "The demanding part of hardware work changes by sub-path: clean-room AIT, RF lab work, embedded benches, and teleport operations stress people differently.", "Matrix placing hardware sub-paths by physical and mental load.", "Qualitative matrix", "Built", "No"),
    VisualMeta("V-16", 9, "9.1", "visual-v16.svg", "GIS Delivery Chain", "The data/GIS job is a delivery system", "The daily GIS or data role is not map-making in isolation. It is a workflow from messy input to trusted operational output.", "Workflow from raw geospatial data to operational use.", "Workflow", "Built", "No"),
    VisualMeta("V-17", 9, "9.2", "visual-v17.svg", "What Spatial AI Work Actually Looks Like", "A concrete analytics pipeline", "The visual turns vague AI language into a real processing pipeline with sources, rules or models, QA, and delivery surfaces.", "Diagram showing spatial analytics inputs, processing, QA, and outputs.", "Diagram", "Built", "No"),
    VisualMeta("V-18", 9, "9.3", "visual-v18.svg", "A Realistic GIS Analyst Day", "Daily rhythm in the data/GIS lane", "A realistic GIS analyst day is structured around scripting, QA, syncs, reporting, and pipeline checks rather than romantic uninterrupted deep work.", "Timeline of a realistic GIS analyst workday.", "Timeline", "Built", "No"),
    VisualMeta("V-19", 10, "10.1", "visual-v19.svg", "Degree-to-Job Translation Funnel", "Why the first job hunt is a translation problem", "Thai employers hire for recognizable functions, so the degree has to be translated into skills, employer categories, role titles, and proof points.", "Funnel from degree title to translated role proof.", "Diagram", "Built", "No"),
    VisualMeta("V-20", 10, "10.2", "visual-v20.svg", "Entry-Level Accessibility by Path", "Where fresh graduates can actually enter", "The market is visibly thicker where implementation, consulting, and GIS-adjacent delivery are already normal employer needs, and thinner where pure space identity dominates.", "Ranked chart of entry-level accessibility across role families.", "Ranked accessibility chart", "Built", "No"),
    VisualMeta("V-21", 11, "11.1", "visual-v21.svg", "Two Career Ladders, Two Risk Profiles", "GIS/data versus satcom/systems progression", "Both ladders can pay off, but the GIS/data ladder tends to branch wider while the satcom/systems ladder stays narrower and more selective.", "Parallel career ladders for GIS/data and satcom/systems.", "Diagram", "Built", "No"),
    VisualMeta("V-22", 12, "12.1", "visual-v22.svg", "Indicative Salary Bands in Thailand", "Reasoned monthly THB ranges from Chapter 12", "The strongest salary engine in this degree is the hybrid technical-specialist path, especially when GIS, data, systems, and delivery skills compound over time.", "Salary band chart for major role families in THB per month.", "Salary bands chart", "Built", "No"),
    VisualMeta("V-23", 12, "12.2", "visual-v23.svg", "International Pathways Funnel", "Not every international route is equally realistic", "Regional downstream work and master's-first sequencing are much more realistic for most Thai students than a direct jump into the most controlled parts of U.S. aerospace.", "Funnel showing relative realism of international pathways.", "Diagram", "Built", "No"),
    VisualMeta("V-24", 13, "13.1", "visual-v24.svg", "Adjacent Labor-Market Depth", "Specialized GIS versus broader technical markets", "The degree becomes safer when it can translate into adjacent data, cloud, network, and telecom markets that visibly run deeper than the narrow specialized GIS pool.", "Bar chart comparing market depth across adjacent technical lanes.", "Market-depth chart", "Built", "No"),
    VisualMeta("V-25", 13, "13.2", "visual-v25.svg", "Choose a Pivot Lane", "Pick one lane and accumulate proof in the same language", "Pivot success comes from choosing a primary lane by work style, then building several months of coherent evidence inside it.", "Decision tree matching work preferences to pivot lanes.", "Workflow", "Built", "No"),
    VisualMeta("V-26", 14, "14.1", "visual-v26.svg", "Four-Year Playbook at a Glance", "What each year is supposed to produce", "The four-year plan compounds only when each year leaves a durable proof asset that makes the next year easier.", "Timeline across all four years of the degree.", "Timeline", "Built", "No"),
    VisualMeta("V-27", 15, "15.1", "visual-v27.svg", "Go / No-Go Decision Matrix", "The final blunt recommendation", "The final verdict is conditional: this is a go for a portfolio-driven technical student and a no-go for someone hoping prestige or space romance will carry the decision.", "Two-column decision matrix with go and no-go conditions.", "Decision matrix", "Built", "No"),
]


BUILDERS = {
    "V-01": build_v01,
    "V-02": build_v02,
    "V-03": build_v03,
    "V-04": build_v04,
    "V-05": build_v05,
    "V-06": build_v06,
    "V-07": build_v07,
    "V-08": build_v08,
    "V-09": build_v09,
    "V-10": build_v10,
    "V-11": build_v11,
    "V-12": build_v12,
    "V-13": build_v13,
    "V-14": build_v14,
    "V-15": build_v15,
    "V-16": build_v16,
    "V-17": build_v17,
    "V-18": build_v18,
    "V-19": build_v19,
    "V-20": build_v20,
    "V-21": build_v21,
    "V-22": build_v22,
    "V-23": build_v23,
    "V-24": build_v24,
    "V-25": build_v25,
    "V-26": build_v26,
    "V-27": build_v27,
}


def visual_html(meta: VisualMeta) -> str:
    return f"""
<figure class="report-figure" id="figure-{meta.figure_no.replace('.', '-')}">
  <img src="visuals/{meta.filename}" alt="{esc(meta.alt)}">
  <figcaption>
    <span class="report-figure__label">Figure {meta.figure_no}</span>
    <span class="report-figure__title">{esc(meta.title)}.</span>
    {esc(meta.caption)}
  </figcaption>
</figure>
""".strip()


def integrate_visuals_into_chapters() -> None:
    id_to_meta = {meta.id.lower(): meta for meta in VISUALS}
    pattern = re.compile(r'<aside class="planned-visual" id="visual-(v-\d{2})">.*?</aside>', re.DOTALL)

    for chapter_path in sorted(ROOT.glob("chapter-*.html")):
        raw = chapter_path.read_text(encoding="utf-8")

        def replace(match: re.Match[str]) -> str:
            key = match.group(1)
            meta = id_to_meta[key]
            return visual_html(meta)

        updated = pattern.sub(replace, raw)
        chapter_path.write_text(updated, encoding="utf-8")


def build_visual_register() -> None:
    rows = []
    for meta in VISUALS:
        rows.append(
            f"<tr><td>{esc(meta.id)}</td><td>Chapter {meta.chapter}</td><td>{esc(meta.register_type)}</td><td>{esc(meta.build_bucket)}</td><td>{esc(meta.needs_user)}</td><td>{esc(meta.title)}</td><td>{esc(meta.caption)}</td></tr>"
        )

    register = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Visual Asset Register</title>
  <style>
    @import url("https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=Source+Serif+4:opsz,wght@8..60,400;8..60,500;8..60,600&display=swap");
    :root {{
      --bg: #eef3f7;
      --paper: #ffffff;
      --ink: #1d2835;
      --muted: #5b6978;
      --line: #d7e0e8;
      --accent: #124a71;
      --soft: #f6f9fb;
      --good: #235f3b;
      --good-bg: #edf7f0;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: linear-gradient(180deg, #f2f5f8, #e7edf2);
      color: var(--ink);
      font: 15.5px/1.58 "Source Serif 4", "Iowan Old Style", serif;
    }}
    main {{
      max-width: 1320px;
      margin: 0 auto;
      padding: 28px 20px 42px;
    }}
    .kicker {{
      margin: 0 0 8px;
      color: var(--accent);
      font: 700 0.75rem/1.2 "IBM Plex Sans", sans-serif;
      letter-spacing: 0.09em;
      text-transform: uppercase;
    }}
    h1 {{
      margin: 0 0 10px;
      color: #12324d;
      font: 700 2.1rem/1.06 "IBM Plex Sans", sans-serif;
      letter-spacing: -0.02em;
    }}
    .lead {{
      margin: 0;
      max-width: 86ch;
      color: var(--muted);
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 14px;
      margin: 24px 0 22px;
    }}
    .card {{
      background: var(--paper);
      border: 1px solid var(--line);
      padding: 15px 16px;
      box-shadow: 0 10px 24px rgba(20, 31, 44, 0.06);
    }}
    .card h2 {{
      margin: 0 0 6px;
      color: #173854;
      font: 700 1rem/1.2 "IBM Plex Sans", sans-serif;
    }}
    .card p {{
      margin: 0;
      color: var(--muted);
      font-family: "IBM Plex Sans", sans-serif;
      font-size: 0.92rem;
      line-height: 1.52;
    }}
    .panel {{
      background: var(--paper);
      border: 1px solid var(--line);
      box-shadow: 0 12px 28px rgba(20, 31, 44, 0.06);
      overflow: hidden;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-family: "IBM Plex Sans", sans-serif;
      font-size: 0.88rem;
      line-height: 1.46;
    }}
    th, td {{
      border: 1px solid var(--line);
      padding: 9px 10px;
      text-align: left;
      vertical-align: top;
    }}
    thead th {{
      background: #f1f5f8;
    }}
    tbody tr:nth-child(even) td {{
      background: #fbfcfd;
    }}
    .note {{
      margin-top: 16px;
      color: var(--muted);
      max-width: 90ch;
    }}
    a {{ color: var(--accent); }}
    @media (max-width: 1040px) {{
      .grid {{
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }}
    }}
    @media (max-width: 720px) {{
      .grid {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <main>
    <p class="kicker">Visual Register</p>
    <h1>Built Visual Asset Register for the KMITL Space and Geospatial Engineering Dossier</h1>
    <p class="lead">All 27 dossier visuals are now built as native SVG assets and integrated into the report. No user-supplied source files were required. The Bangkok-style map was built as a schematic city-layer illustration rather than a factual cadastral basemap.</p>
    <section class="grid">
      <article class="card"><h2>Total visuals</h2><p>27 built and integrated</p></article>
      <article class="card"><h2>Need from you</h2><p>0 required to ship the current book</p></article>
      <article class="card"><h2>Asset format</h2><p>SVG figures tuned for crisp A4 display and print use</p></article>
      <article class="card"><h2>Current state</h2><p>Standalone chapters and master dossier now use finished figures instead of placeholder notes</p></article>
    </section>
    <section class="panel">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Chapter</th>
            <th>Type</th>
            <th>Status</th>
            <th>Need From You?</th>
            <th>Visual</th>
            <th>Caption Summary</th>
          </tr>
        </thead>
        <tbody>
          {"".join(rows)}
        </tbody>
      </table>
    </section>
    <p class="note"><a href="kmitl-space-geospatial-strategic-dossier.html">Open the master dossier</a></p>
  </main>
</body>
</html>
"""
    (ROOT / "visual-asset-register.html").write_text(register, encoding="utf-8")


def build_assets() -> None:
    for meta in VISUALS:
        svg = BUILDERS[meta.id](meta)
        (VISUAL_DIR / meta.filename).write_text(svg, encoding="utf-8")


def rebuild_master() -> None:
    subprocess.run(
        ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(ROOT / "build-master-book.ps1")],
        cwd=str(ROOT),
        check=True,
    )


def main() -> None:
    build_assets()
    integrate_visuals_into_chapters()
    build_visual_register()
    rebuild_master()
    print(f"Built {len(VISUALS)} visuals and rebuilt the master dossier.")


if __name__ == "__main__":
    main()

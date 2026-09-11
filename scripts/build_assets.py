#!/usr/bin/env python3
"""Author the hand-built SVG art for the kael-odin profile README.

Everything here is drawn from scratch (no capsule-render / no third-party
widget service) and emitted as self-contained SVG: no external fonts, no
scripts, no remote references. That is what lets the images be committed to
the repo and served straight off raw.githubusercontent.

Run:  python scripts/build_assets.py [--out assets]
"""

from __future__ import annotations

import argparse
import os

WIDE = 1280
FONT = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"

THEMES = {
    "dark": {
        "bg0": "#05070d", "bg1": "#0a1020",
        "panel": "#0b1220", "panel2": "#0e1830",
        "border": "#16223a", "ink": "#e6f1ff", "muted": "#7a8ba3", "dim": "#3c4a63",
        "grid": "#12233d", "rule": "#16223a",
        "c1": "#00ffe5", "c2": "#7b2ff7", "c3": "#ff2e97", "amber": "#ffb020",
        "glow": True,
    },
    "light": {
        "bg0": "#ffffff", "bg1": "#eef3fb",
        "panel": "#ffffff", "panel2": "#f4f7fc",
        "border": "#d9e2f0", "ink": "#0b1020", "muted": "#5a6b85", "dim": "#9aa8bf",
        "grid": "#dce6f5", "rule": "#d9e2f0",
        "c1": "#009e8e", "c2": "#6236c9", "c3": "#d4247a", "amber": "#b57300",
        "glow": False,
    },
}


def head(w: int, h: int, t: dict, extra_defs: str = "", css: str = "") -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img">
<style>
  text {{ font-family: {FONT}; }}
  .mono {{ font-family: {FONT}; }}
  .pulse {{ animation: pulse 4.5s linear infinite; }}
  .blink {{ animation: blink 1.15s steps(1,end) infinite; }}
  .breathe {{ animation: breathe 5s ease-in-out infinite; }}
  @keyframes pulse {{ from {{ transform: translateX(0); }} to {{ transform: translateX({w + 260}px); }} }}
  @keyframes blink {{ 0%, 49% {{ opacity: 1; }} 50%, 100% {{ opacity: 0; }} }}
  @keyframes breathe {{ 0%, 100% {{ opacity: .45; }} 50% {{ opacity: 1; }} }}
  {css}
</style>
<defs>{extra_defs}</defs>
"""


def glow_filter(t: dict, std: float = 3.0) -> str:
    # color-interpolation-filters="sRGB" is required or linearRGB flattens
    # the neon palette toward white.
    return (
        f'<filter id="glow" x="-50%" y="-50%" width="200%" height="200%" '
        f'color-interpolation-filters="sRGB">'
        f'<feGaussianBlur stdDeviation="{std}" result="b"/>'
        f'<feMerge><feMergeNode in="b"/><feMergeNode in="b"/>'
        f'<feMergeNode in="SourceGraphic"/></feMerge></filter>'
    )


def grid_rect(w: int, h: int, t: dict, cell: int = 64, opacity: float = 0.55, scroll: bool = True) -> str:
    anim = (
        f'<animateTransform attributeName="transform" type="translate" '
        f'from="0 0" to="0 {cell}" dur="7s" repeatCount="indefinite"/>'
        if scroll
        else ""
    )
    return (
        f'<pattern id="grid" width="{cell}" height="{cell}" patternUnits="userSpaceOnUse">'
        f'<path d="M {cell} 0 L 0 0 0 {cell}" fill="none" stroke="{t["grid"]}" stroke-width="1"/>'
        f"</pattern>"
        f'<rect x="-{cell}" y="-{cell}" width="{w + cell * 2}" height="{h + cell * 2}" '
        f'fill="url(#grid)" opacity="{opacity}">{anim}</rect>'
    )


def brackets(w: int, h: int, t: dict, pad: int = 26, size: int = 22) -> str:
    c = t["c1"]
    d = [
        f"M {pad} {pad + size} L {pad} {pad} L {pad + size} {pad}",
        f"M {w - pad - size} {pad} L {w - pad} {pad} L {w - pad} {pad + size}",
        f"M {pad} {h - pad - size} L {pad} {h - pad} L {pad + size} {h - pad}",
        f"M {w - pad - size} {h - pad} L {w - pad} {h - pad} L {w - pad} {h - pad - size}",
    ]
    return "".join(
        f'<path d="{p}" fill="none" stroke="{c}" stroke-width="2" stroke-opacity=".55"/>' for p in d
    )


def status(w: int, h: int, t: dict, label: str = "ONLINE", left: str = "// PROFILE") -> str:
    return (
        f'<text x="56" y="56" font-size="12" font-weight="600" fill="{t["muted"]}" '
        f'letter-spacing="3.4">{left}</text>'
        f'<circle cx="{w - 138}" cy="52" r="3.5" fill="{t["c1"]}" class="blink"/>'
        f'<text x="{w - 56}" y="56" font-size="12" font-weight="600" fill="{t["c1"]}" '
        f'letter-spacing="3" text-anchor="end">{label}</text>'
    )


# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------


def hero(t: dict) -> str:
    w, h = WIDE, 350
    name = "KAEL ODIN"
    defs = (
        f'<linearGradient id="nameGrad" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0%" stop-color="{t["c1"]}"/>'
        f'<stop offset="48%" stop-color="{t["c2"]}"/>'
        f'<stop offset="100%" stop-color="{t["c3"]}"/></linearGradient>'
        f'<linearGradient id="shimmer" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0%" stop-color="#ffffff" stop-opacity="0"/>'
        f'<stop offset="50%" stop-color="#ffffff" stop-opacity=".85"/>'
        f'<stop offset="100%" stop-color="#ffffff" stop-opacity="0"/></linearGradient>'
        f'<linearGradient id="scanGrad" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{t["c1"]}" stop-opacity="0"/>'
        f'<stop offset="50%" stop-color="{t["c1"]}" stop-opacity=".13"/>'
        f'<stop offset="100%" stop-color="{t["c1"]}" stop-opacity="0"/></linearGradient>'
        f'<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{t["bg0"]}"/>'
        f'<stop offset="100%" stop-color="{t["bg1"]}"/></linearGradient>'
        f'<linearGradient id="ruleGrad" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0%" stop-color="{t["c1"]}"/>'
        f'<stop offset="100%" stop-color="{t["c1"]}" stop-opacity="0"/></linearGradient>'
        f'<clipPath id="nameClip"><text x="56" y="196" font-size="104" font-weight="800" '
        f'letter-spacing="9">{name}</text></clipPath>'
        f'<radialGradient id="halo"><stop offset="0%" stop-color="{t["c2"]}" stop-opacity=".38"/>'
        f'<stop offset="100%" stop-color="{t["c2"]}" stop-opacity="0"/></radialGradient>'
    )
    if t["glow"]:
        defs += glow_filter(t, 5.0)

    out = [head(w, h, t, defs)]
    out.append(f'<rect width="{w}" height="{h}" fill="url(#bg)"/>')
    out.append(grid_rect(w, h, t, opacity=0.5 if t["glow"] else 0.7))
    out.append(f'<ellipse cx="360" cy="180" rx="420" ry="170" fill="url(#halo)"/>')

    if t["glow"]:  # vertical scan sweep, dark theme only
        out.append(
            f'<rect x="0" y="-140" width="{w}" height="140" fill="url(#scanGrad)">'
            f'<animate attributeName="y" from="-140" to="350" dur="8s" repeatCount="indefinite"/>'
            f"</rect>"
        )

    out.append(brackets(w, h, t))
    out.append(status(w, h, t))

    # Name: glow pass, gradient pass, then a light sweep clipped to the glyphs.
    name_attrs = f'x="56" y="196" font-size="104" font-weight="800" letter-spacing="9"'
    if t["glow"]:
        out.append(
            f'<text {name_attrs} fill="{t["c1"]}" filter="url(#glow)" opacity=".55">{name}</text>'
        )
    out.append(f'<text {name_attrs} fill="url(#nameGrad)">{name}</text>')
    out.append(
        f'<g clip-path="url(#nameClip)"><rect x="-300" y="60" width="300" height="180" '
        f'fill="url(#shimmer)">'
        f'<animate attributeName="x" from="-300" to="{w + 60}" dur="5.5s" '
        f'begin="1s" repeatCount="indefinite"/></rect></g>'
    )

    # Accent rule with a travelling pulse
    out.append(f'<rect x="56" y="228" width="600" height="2" fill="url(#ruleGrad)" opacity=".85"/>')
    out.append(
        f'<rect class="pulse" x="-260" y="226.5" width="260" height="5" rx="2.5" '
        f'fill="url(#shimmer)" opacity=".9"/>'
    )

    out.append(
        f'<text x="56" y="266" font-size="19" fill="{t["muted"]}" letter-spacing="3.4">'
        f"Full-stack &amp; systems engineering &#183; open source &#183; turning ideas into repositories"
        f"</text>"
    )

    # Tag pills
    tags = ["LOCAL LLM", "AGENT TOOLING", "DATA PIPELINE", "I18N", "OPEN SOURCE"]
    x, y, ph = 56, 292, 34
    for i, tag in enumerate(tags):
        accent = [t["c1"], t["c3"], t["c2"], t["c1"], t["c3"]][i % 5]
        pw = len(tag) * 9.2 + 30
        out.append(
            f'<rect x="{x:.0f}" y="{y}" width="{pw:.0f}" height="{ph}" rx="{ph / 2:.0f}" '
            f'fill="{accent}" fill-opacity=".08" stroke="{accent}" stroke-opacity=".55" stroke-width="1"/>'
        )
        out.append(
            f'<text x="{x + pw / 2:.0f}" y="{y + 22}" font-size="12.5" font-weight="600" '
            f'fill="{accent}" letter-spacing="1.5" text-anchor="middle">{tag}</text>'
        )
        x += pw + 12

    out.append("</svg>\n")
    return "".join(out)


# ---------------------------------------------------------------------------
# Terminal
# ---------------------------------------------------------------------------


def terminal(t: dict) -> str:
    w, h = 940, 314
    top = 42
    defs = (
        f'<linearGradient id="termBg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{t["panel"]}"/>'
        f'<stop offset="100%" stop-color="{t["bg0"]}"/></linearGradient>'
    )

    # (text, colour, indent, is_command)
    lines = [
        ("$ whoami", t["c1"], 0, True),
        ("Kael Odin  ·  full-stack / systems  ·  @Thordata", t["ink"], 0, False),
        ("", t["muted"], 0, False),
        ("$ ls ~/projects --sort=stars", t["c1"], 0, True),
        ("awesome-academic-research-skills", t["ink"], 2, False),
        ("openworker", t["ink"], 2, False),
        ("kv-streaming-2080ti-22G", t["ink"], 2, False),
    ]
    stars = ["76", "27", "3"]

    out = [head(w, h, t, defs, css="@keyframes type { from { transform: scaleX(0); } to { transform: scaleX(1); } }")]
    out.append(
        f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="13" fill="url(#termBg)" '
        f'stroke="{t["border"]}" stroke-width="1"/>'
    )
    out.append(
        f'<path d="M 0.5 43 L 0.5 13 A 13 13 0 0 1 13.5 0.5 L {w - 13.5} 0.5 '
        f'A 13 13 0 0 1 {w - 0.5} 13 L {w - 0.5} 43 Z" fill="{t["panel2"]}"/>'
    )
    out.append(f'<line x1="0.5" y1="43" x2="{w - 0.5}" y2="43" stroke="{t["border"]}" stroke-width="1"/>')

    for i, colour in enumerate(["#ff5f57", "#febc2e", "#28c840"]):
        out.append(f'<circle cx="{26 + i * 21}" cy="22" r="6.5" fill="{colour}"/>')
    out.append(
        f'<text x="{w / 2}" y="27" font-size="12.5" fill="{t["muted"]}" letter-spacing="1.6" '
        f'text-anchor="middle">kael@github — zsh</text>'
    )

    # Lines wipe in left-to-right via a scaleX'd clip rect rather than an
    # animated width. The rect's *resting* transform is scaleX(1) so a viewer
    # whose renderer never runs the animation still sees the full text;
    # animation-fill-mode:both hides it only during the stagger delay.
    y = 72
    star_row = 0
    for i, (text, colour, indent, is_cmd) in enumerate(lines):
        if not text:
            y += 16
            continue
        x = 28 + indent * 16
        wipe_w = len(text) * 9.0 + 40
        delay = 0.30 + i * 0.32
        dur = min(0.55, max(0.22, len(text) * 0.018))
        cid = f"type{i}"
        out.append(
            f'<clipPath id="{cid}" clipPathUnits="userSpaceOnUse">'
            f'<rect x="{x}" y="{y - 19}" width="{wipe_w:.0f}" height="26" '
            f'style="transform-origin:{x}px 0;'
            f'animation:type {dur:.2f}s steps({max(6, len(text))},end) {delay:.2f}s both"/>'
            f"</clipPath>"
        )
        out.append(f'<g clip-path="url(#{cid})">')
        out.append(
            f'<text x="{x}" y="{y}" font-size="14.5" fill="{colour}" '
            f'letter-spacing="0.2">{text.replace("&", "&amp;").replace("<", "&lt;")}</text>'
        )
        out.append("</g>")

        # The star count is right-aligned, well outside the line's wipe rect,
        # so it needs its own clip — otherwise the typing animation eats it.
        if text in ("awesome-academic-research-skills", "openworker", "kv-streaming-2080ti-22G"):
            sx, sw = w - 34, 90
            sid = f"star{i}"
            out.append(
                f'<clipPath id="{sid}" clipPathUnits="userSpaceOnUse">'
                f'<rect x="{sx - sw}" y="{y - 19}" width="{sw}" height="26" '
                f'style="transform-origin:{sx - sw}px 0;'
                f'animation:type 0.18s steps(8,end) {delay + 0.16:.2f}s both"/>'
                f"</clipPath>"
            )
            out.append(f'<g clip-path="url(#{sid})">')
            out.append(
                f'<text x="{sx}" y="{y}" font-size="14" fill="{t["amber"]}" '
                f'text-anchor="end">★ {stars[star_row]}</text>'
            )
            out.append("</g>")
            star_row += 1
        y += 30 if is_cmd else 26

    # Prompt with a blinking block cursor
    out.append(f'<text x="28" y="{y + 12}" font-size="14.5" fill="{t["c1"]}">$</text>')
    out.append(
        f'<rect class="blink" x="48" y="{y}" width="9" height="16" fill="{t["c1"]}"/>'
    )

    out.append("</svg>\n")
    return "".join(out)


# ---------------------------------------------------------------------------
# Divider / footer
# ---------------------------------------------------------------------------


def divider(t: dict) -> str:
    w, h = WIDE, 10
    defs = (
        f'<linearGradient id="pulseGrad" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0%" stop-color="{t["c1"]}" stop-opacity="0"/>'
        f'<stop offset="50%" stop-color="{t["c1"]}" stop-opacity="1"/>'
        f'<stop offset="100%" stop-color="{t["c1"]}" stop-opacity="0"/></linearGradient>'
    )
    return (
        head(w, h, t, defs)
        + f'<line x1="0" y1="5" x2="{w}" y2="5" stroke="{t["rule"]}" stroke-width="1"/>'
        + f'<rect class="pulse" x="-260" y="3.5" width="260" height="3" rx="1.5" '
        f'fill="url(#pulseGrad)"/>'
        + "</svg>\n"
    )


def footer(t: dict) -> str:
    w, h = WIDE, 156
    defs = (
        f'<linearGradient id="wordGrad" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0%" stop-color="{t["c1"]}"/>'
        f'<stop offset="50%" stop-color="{t["c2"]}"/>'
        f'<stop offset="100%" stop-color="{t["c3"]}"/></linearGradient>'
        f'<linearGradient id="pulseGrad" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0%" stop-color="{t["c3"]}" stop-opacity="0"/>'
        f'<stop offset="50%" stop-color="{t["c3"]}" stop-opacity="1"/>'
        f'<stop offset="100%" stop-color="{t["c3"]}" stop-opacity="0"/></linearGradient>'
    )
    out = [head(w, h, t, defs)]
    out.append(grid_rect(w, h, t, cell=48, opacity=0.3 if t["glow"] else 0.45))
    out.append(f'<line x1="0" y1="8" x2="{w}" y2="8" stroke="{t["rule"]}" stroke-width="1"/>')
    out.append(
        f'<text x="{w / 2}" y="72" font-size="30" font-weight="700" letter-spacing="14" '
        f'fill="url(#wordGrad)" text-anchor="middle">KAEL ODIN</text>'
    )
    out.append(
        f'<text x="{w / 2}" y="102" font-size="12" fill="{t["muted"]}" letter-spacing="4.6" '
        f'text-anchor="middle">TURNING IDEAS INTO REPOSITORIES</text>'
    )
    out.append(f'<line x1="0" y1="132" x2="{w}" y2="132" stroke="{t["rule"]}" stroke-width="1"/>')
    out.append(
        f'<rect class="pulse" x="-260" y="130.5" width="260" height="3" rx="1.5" '
        f'fill="url(#pulseGrad)"/>'
    )
    out.append("</svg>\n")
    return "".join(out)


# ---------------------------------------------------------------------------
# Focus panels
# ---------------------------------------------------------------------------

PANELS = [
    ("01", "LOCAL LLM", "本地推理 / 量化", "RTX 2080 Ti 22G · KV streaming"),
    ("02", "AGENT TOOLING", "智能体工作台", "protocol reverse · plugin · orchestration"),
    ("03", "I18N & MIRRORS", "中文本地化", "docs & product mirrors for zh-CN"),
    ("04", "DATA PIPELINES", "采集与清洗", "scraping · structuring · proxies"),
]


def esc(text: str) -> str:
    """Focus-panel copy contains '&' and would otherwise break XML parsing."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def focus(t: dict) -> str:
    w, h = WIDE, 232
    pad, gap = 56, 20
    pw = (w - pad * 2 - gap * 3) / 4
    ph, py = 172, 30
    accents = [t["c1"], t["c3"], t["c2"], t["c1"]]

    out = [head(w, h, t)]
    for i, (idx, title, zh, desc) in enumerate(PANELS):
        x = pad + i * (pw + gap)
        accent = accents[i]
        out.append(
            f'<rect x="{x:.0f}" y="{py}" width="{pw:.0f}" height="{ph}" rx="12" '
            f'fill="{accent}" fill-opacity=".05" stroke="{t["border"]}" stroke-width="1"/>'
        )
        out.append(
            f'<rect class="breathe" style="animation-delay:{i * 0.8:.1f}s" '
            f'x="{x:.0f}" y="{py}" width="{pw:.0f}" height="3" rx="1.5" fill="{accent}"/>'
        )
        out.append(
            f'<text x="{x + 20:.0f}" y="{py + 44}" font-size="15" font-weight="700" '
            f'fill="{accent}" letter-spacing="2">{idx}</text>'
        )
        out.append(
            f'<text x="{x + pw - 20:.0f}" y="{py + 44}" font-size="12" fill="{t["dim"]}" '
            f'letter-spacing="1.6" text-anchor="end">{esc(zh)}</text>'
        )
        out.append(
            f'<text x="{x + 20:.0f}" y="{py + 84}" font-size="19" font-weight="700" '
            f'fill="{t["ink"]}" letter-spacing="1.4">{esc(title)}</text>'
        )
        out.append(
            f'<line x1="{x + 20:.0f}" y1="{py + 102}" x2="{x + pw - 20:.0f}" y2="{py + 102}" '
            f'stroke="{t["border"]}" stroke-width="1"/>'
        )
        out.append(
            f'<text x="{x + 20:.0f}" y="{py + 128}" font-size="12.5" fill="{t["muted"]}" '
            f'letter-spacing="0.4">{esc(desc)}</text>'
        )
        out.append(
            f'<text x="{x + 20:.0f}" y="{py + 152}" font-size="11" fill="{t["dim"]}" '
            f'letter-spacing="2.4">FOCUS AREA</text>'
        )
    out.append("</svg>\n")
    return "".join(out)


# ---------------------------------------------------------------------------

BUILDERS = {
    "hero": hero,
    "terminal": terminal,
    "divider": divider,
    "focus": focus,
    "footer": footer,
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="assets")
    args = parser.parse_args()
    os.makedirs(args.out, exist_ok=True)

    for theme_name, theme in THEMES.items():
        for name, builder in BUILDERS.items():
            path = os.path.join(args.out, f"{name}-{theme_name}.svg")
            with open(path, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(builder(theme))
            print(f"  wrote {path}")


if __name__ == "__main__":
    main()

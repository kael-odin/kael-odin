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
import math
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
    """Mission-control hero: glitch-draw wordmark over a synthwave grid floor,
    telemetry ring and HUD readouts — same palette and type as every other
    asset on the page. Pure declarative SVG (CSS/SMIL, no scripts), safe to
    serve from raw.githubusercontent inside <img>/<picture>."""
    w, h = WIDE, 420
    dark = t["glow"]
    go = ".5" if dark else ".26"          # resting RGB-fringe opacity
    burst = ".9" if dark else ".55"       # glitch burst peak opacity
    aur1 = ".15" if dark else ".09"       # purple aurora wash
    aur2 = ".11" if dark else ".07"       # cyan aurora wash
    ray_o = ".22" if dark else ".30"
    ring_cx, ring_cy = 1128.0, 190.0

    circ66 = 2 * math.pi * 66
    trace = "M 350 250 H 556 L 568 242 H 712 L 724 250 H 930"
    glow_attr = ' filter="url(#glow)"' if dark else ""

    ticks = " ".join(
        f"M {ring_cx + 74 * math.cos(math.radians(k * 30)):.1f} "
        f"{ring_cy + 74 * math.sin(math.radians(k * 30)):.1f} L "
        f"{ring_cx + 80 * math.cos(math.radians(k * 30)):.1f} "
        f"{ring_cy + 80 * math.sin(math.radians(k * 30)):.1f}"
        for k in range(12)
    )
    hex_out = " ".join(
        f"{ring_cx + 32 * math.cos(math.radians(-90 + 60 * k)):.1f},"
        f"{ring_cy + 32 * math.sin(math.radians(-90 + 60 * k)):.1f}"
        for k in range(6)
    )
    hex_in = " ".join(
        f"{ring_cx + 24 * math.cos(math.radians(-90 + 60 * k)):.1f},"
        f"{ring_cy + 24 * math.sin(math.radians(-90 + 60 * k)):.1f}"
        for k in range(6)
    )

    defs = (
        f'<linearGradient id="bgG" x1="0" y1="0" x2="0" y2="1">'
        f'<stop stop-color="{t["bg0"]}"/><stop offset="100%" stop-color="{t["bg1"]}"/></linearGradient>'
        f'<radialGradient id="aur1"><stop stop-color="{t["c2"]}" stop-opacity=".9"/>'
        f'<stop offset="100%" stop-color="{t["c2"]}" stop-opacity="0"/></radialGradient>'
        f'<radialGradient id="aur2"><stop stop-color="{t["c1"]}" stop-opacity=".9"/>'
        f'<stop offset="100%" stop-color="{t["c1"]}" stop-opacity="0"/></radialGradient>'
        f'<radialGradient id="clear"><stop stop-color="{t["bg0"]}" stop-opacity=".6"/>'
        f'<stop offset="100%" stop-color="{t["bg0"]}" stop-opacity="0"/></radialGradient>'
        f'<linearGradient id="nameGrad" x1="0" y1="0" x2="1" y2="0">'
        f'<stop stop-color="{t["c1"]}"/><stop offset=".52" stop-color="{t["c2"]}"/>'
        f'<stop offset="100%" stop-color="{t["c3"]}"/></linearGradient>'
        f'<linearGradient id="scanG" x1="0" y1="0" x2="0" y2="1">'
        f'<stop stop-color="{t["c1"]}" stop-opacity="0"/>'
        f'<stop offset=".5" stop-color="{t["c1"]}" stop-opacity=".12"/>'
        f'<stop offset="100%" stop-color="{t["c1"]}" stop-opacity="0"/></linearGradient>'
        f'<linearGradient id="hzG" x1="0" y1="0" x2="0" y2="1">'
        f'<stop stop-color="{t["c1"]}" stop-opacity=".38"/>'
        f'<stop offset="100%" stop-color="{t["c1"]}" stop-opacity="0"/></linearGradient>'
        f'<clipPath id="floorClip"><rect x="0" y="352" width="{w}" height="{h - 352}"/></clipPath>'
    )
    if dark:
        defs += glow_filter(t, 3.2)

    css = f"""
      .han {{ font-family: 'PingFang SC', 'Microsoft YaHei', 'Noto Sans CJK SC', sans-serif; }}
      .gl-a {{ animation: glz-a 7.3s steps(1,end) infinite; }}
      .gl-b {{ animation: glz-b 7.3s steps(1,end) infinite; }}
      @keyframes glz-a {{ 0%,90.9% {{ transform: translate(0,0); opacity: {go}; }}
        91.4% {{ transform: translate(-8px,3px); opacity: {burst}; }}
        92.6% {{ transform: translate(6px,-2px); opacity: .55; }}
        93.8% {{ transform: translate(-4px,1px); opacity: {burst}; }}
        94.6%,100% {{ transform: translate(0,0); opacity: {go}; }} }}
      @keyframes glz-b {{ 0%,44.9% {{ transform: translate(0,0); opacity: {go}; }}
        45.4% {{ transform: translate(7px,-3px); opacity: {burst}; }}
        46.6% {{ transform: translate(-5px,2px); opacity: .5; }}
        47.8% {{ transform: translate(3px,-1px); opacity: {burst}; }}
        48.6%,100% {{ transform: translate(0,0); opacity: {go}; }} }}
      .name-line {{ animation: nDraw 1.7s cubic-bezier(.25,.6,.2,1) .15s backwards; }}
      @keyframes nDraw {{ from {{ stroke-dashoffset: 660; }} }}
      .trace {{ animation: tDraw 1.1s cubic-bezier(.3,.7,.2,1) 2.15s backwards; }}
      @keyframes tDraw {{ from {{ stroke-dashoffset: 600; }} }}
      .cdot {{ offset-path: path('{trace}'); offset-rotate: 0deg;
               animation: cdot 5.6s cubic-bezier(.45,.05,.55,.95) 3.2s infinite; }}
      @keyframes cdot {{ 0% {{ offset-distance: 0%; opacity: 0; }} 10% {{ opacity: 1; }}
        88% {{ opacity: 1; }} 100% {{ offset-distance: 100%; opacity: 0; }} }}
      .orb-a {{ animation: spin 46s linear infinite; }}
      .orb-b {{ animation: spinR 30s linear infinite; }}
      @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
      @keyframes spinR {{ to {{ transform: rotate(-360deg); }} }}
      .arc {{ animation: arcSweep 7s linear infinite; }}
      @keyframes arcSweep {{ to {{ stroke-dashoffset: -{circ66:.1f}; }} }}
      .ray {{ animation: rayFlow 5.5s linear infinite; }}
      @keyframes rayFlow {{ to {{ stroke-dashoffset: -130; }} }}
      .tw {{ animation: twinkle 4.6s ease-in-out infinite; }}
      @keyframes twinkle {{ 0%,100% {{ opacity: .5; }} 50% {{ opacity: .06; }} }}
      .scan {{ animation: scanMove 9s linear infinite 2.6s backwards; }}
      @keyframes scanMove {{ from {{ transform: translateY(0); }} to {{ transform: translateY(580px); }} }}
      .drift-a {{ animation: drift 19s ease-in-out infinite alternate; }}
      .drift-b {{ animation: drift 24s ease-in-out infinite alternate-reverse; }}
      @keyframes drift {{ from {{ transform: translate(0,0); }} to {{ transform: translate(26px,14px); }} }}
      @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}
    """

    out = [head(w, h, t, defs, css.strip())]
    out.append("<title>Kael Odin — mission control</title>")
    out.append(
        "<desc>Neon HUD hero: the name KAEL ODIN assembles over a synthwave grid floor "
        "with a telemetry ring, signal trace and scanline sweep, in a light or dark palette.</desc>"
    )
    out.append(f'<rect width="{w}" height="{h}" fill="url(#bgG)"/>')

    # Ambient depth: aurora washes drifting on their own periods.
    out.append(f'<g opacity="{aur1}" class="drift-a"><ellipse cx="240" cy="70" rx="430" ry="240" fill="url(#aur1)"/></g>')
    out.append(f'<g opacity="{aur2}" class="drift-b"><ellipse cx="1050" cy="360" rx="470" ry="250" fill="url(#aur2)"/></g>')

    # Fine grid — the same cell size the footer uses.
    out.append(grid_rect(w, h, t, cell=64, opacity=0.55 if dark else 0.6, scroll=False))

    stars = [
        (61, 84, 1.1, .35, 0), (142, 61, .9, .3, 0), (214, 102, 1.3, 1, 0),
        (305, 58, .8, .3, 0), (388, 88, 1.0, .3, 0), (502, 64, 1.2, 1, 2.1),
        (612, 52, .9, .3, 0), (706, 74, 1.1, .3, 0), (818, 58, 1.3, 1, 3.0),
        (902, 96, .9, .3, 0), (985, 60, 1.1, .3, 0), (1078, 86, 1.2, 1, .8),
        (1196, 72, .9, .3, 0), (95, 168, 1.0, .3, 0), (1210, 150, 1.1, 1, 2.8),
        (74, 262, 1.0, .3, 0), (1216, 258, 1.2, .3, 0), (132, 338, 1.1, 1, 1.7),
        (286, 318, .9, .3, 0), (994, 320, 1.0, .3, 0), (1122, 342, 1.2, 1, 3.6),
        (452, 342, .9, .3, 0), (768, 334, 1.0, .3, 0), (640, 44, 1.1, .3, 0),
    ]
    for x, y, r, op, delay in stars:
        if delay:
            out.append(
                f'<circle class="tw" style="animation-delay:{delay}s" cx="{x}" cy="{y}" '
                f'r="{r}" fill="{t["c1"]}"/>'
            )
        else:
            out.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{t["ink"]}" opacity="{op}"/>')

    # Keep the centre readable over the grid.
    out.append('<ellipse cx="640" cy="225" rx="440" ry="195" fill="url(#clear)"/>')

    # Synthwave floor: static horizontals + rays with energy flowing outward.
    out.append('<g clip-path="url(#floorClip)" fill="none">')
    for y, op in ((358, .16), (366, .22), (377, .3), (392, .4), (410, .5)):
        out.append(f'<line x1="0" y1="{y}" x2="{w}" y2="{y}" stroke="{t["grid"]}" stroke-width="1" stroke-opacity="{op}"/>')
    for i in range(-4, 5):
        out.append(
            f'<path class="ray" style="animation-delay:{-i * .45:.2f}s" d="M 640 352 L {640 + i * 190} 436" '
            f'stroke="{t["c1"]}" stroke-width="1" stroke-opacity="{ray_o}" stroke-dasharray="4 9"/>'
        )
    out.append("</g>")
    out.append(f'<rect x="0" y="346" width="{w}" height="12" fill="url(#hzG)"/>')
    out.append(
        f'<line x1="0" y1="352" x2="{w}" y2="352" stroke="{t["c1"]}" stroke-width="1.3" '
        f'stroke-opacity=".5"{glow_attr}/>'
    )

    # Left flank: telemetry rows with meters that fill in.
    for j, (label, val, p, accent) in enumerate(
        (("LOCAL LLM", "22G VRAM", .86, t["c1"]),
         ("AGENT OPS", "TOOLING", .62, t["c2"]),
         ("I18N MIRRORS", "ZH-CN", .74, t["c3"]))
    ):
        ry = 172 + j * 44
        out.append(f'<text x="64" y="{ry - 8}" font-size="12" fill="{t["dim"]}" letter-spacing="2">{label}</text>')
        out.append(f'<text x="214" y="{ry - 8}" font-size="12" fill="{t["muted"]}" text-anchor="end">{val}</text>')
        out.append(f'<rect x="64" y="{ry}" width="150" height="3" rx="1.5" fill="{t["border"]}"/>')
        out.append(
            f'<rect x="64" y="{ry}" width="{150 * p:.0f}" height="3" rx="1.5" fill="{accent}"/>'
        )

    # Right flank: telemetry ring around the 造 core.
    out.append('<g class="orb-a" style="transform-origin:%.0fpx %.0fpx">' % (ring_cx, ring_cy))
    out.append(
        f'<circle cx="{ring_cx}" cy="{ring_cy}" r="84" fill="none" stroke="{t["muted"]}" '
        f'stroke-opacity=".45" stroke-width="1" stroke-dasharray="2 7"/>'
    )
    for dx, dy in ((0, -84), (84, 0), (0, 84), (-84, 0)):
        out.append(
            f'<rect x="{ring_cx + dx - 3:.0f}" y="{ring_cy + dy - 3:.0f}" width="6" height="6" '
            f'fill="{t["c1"]}" opacity=".7"/>'
        )
    out.append("</g>")
    out.append(f'<path d="{ticks}" stroke="{t["dim"]}" stroke-width="1.2" fill="none" opacity=".8"/>')
    arc_end_x = ring_cx + 66 * math.sin(math.radians(120))
    arc_end_y = ring_cy - 66 * math.cos(math.radians(120))
    out.append(
        f'<path class="arc" d="M {ring_cx:.0f} {ring_cy - 66:.0f} A 66 66 0 0 1 {arc_end_x:.1f} {arc_end_y:.1f}" '
        f'fill="none" stroke="{t["c3"]}" stroke-width="2" stroke-linecap="round" '
        f'stroke-dasharray="{circ66 / 3:.1f} {2 * circ66 / 3:.1f}"/>'
    )
    out.append('<g class="orb-b" style="transform-origin:%.0fpx %.0fpx">' % (ring_cx, ring_cy))
    out.append(
        f'<circle cx="{ring_cx}" cy="{ring_cy}" r="56" fill="none" stroke="{t["c1"]}" '
        f'stroke-opacity=".55" stroke-width="1.4" stroke-dasharray="34 14"/>'
    )
    out.append("</g>")
    out.append(
        f'<polygon points="{hex_out}" fill="{t["panel"]}" fill-opacity=".94" '
        f'stroke="{t["c1"]}" stroke-width="1.5"{glow_attr}/>'
    )
    out.append(
        f'<polygon class="breathe" points="{hex_in}" fill="none" stroke="{t["border"]}" '
        f'stroke-width="1" stroke-dasharray="3 4"/>'
    )
    out.append(
        f'<text x="{ring_cx:.0f}" y="{ring_cy + 9:.0f}" text-anchor="middle" class="han" '
        f'font-size="26" font-weight="700" fill="{t["ink"]}">造</text>'
    )
    out.append(
        f'<text x="{ring_cx:.0f}" y="296" text-anchor="middle" font-size="12" fill="{t["muted"]}" '
        f'letter-spacing="2.4">SYS.CORE // ONLINE</text>'
    )

    # Top HUD row.
    out.append(f'<text x="64" y="56" font-size="15" fill="{t["muted"]}" letter-spacing=".3">~/kael-odin · main</text>')
    out.append(f'<circle cx="1062" cy="51.5" r="3.5" fill="{t["c1"]}" class="blink"/>')
    out.append(
        f'<text x="{w - 56}" y="56" text-anchor="end" font-size="12.5" fill="{t["c1"]}" '
        f'letter-spacing="3">SYSTEMS ONLINE</text>'
    )

    # Kicker: shell prompt with a blinking block cursor.
    out.append(f'<path d="M 520 113 H 594 M 686 113 H 760" stroke="{t["rule"]}" stroke-width="1"/>')
    out.append(
        f'<text x="640" y="118" text-anchor="middle" font-size="16" letter-spacing="1.2" '
        f'fill="{t["c1"]}">$ whoami</text>'
    )
    out.append(f'<rect x="690" y="104" width="9" height="17" fill="{t["c1"]}" class="blink"/>')

    # The wordmark: RGB-fringed ghosts plus a permanent gradient fill; the
    # outline traces itself around the finished letters like a plasma rim.
    # Motion only ever ADDS — the resting state must be the complete artwork,
    # because static renderers (social cards, scrapers) never run the clock.
    name_attrs = 'x="640" y="224" text-anchor="middle" font-size="96" font-weight="700" letter-spacing="6"'
    out.append(f'<g transform="translate(-2.5 0)"><text class="gl-a" {name_attrs} fill="{t["c3"]}" opacity="{go}">KAEL ODIN</text></g>')
    out.append(f'<g transform="translate(2.5 0)"><text class="gl-b" {name_attrs} fill="{t["c1"]}" opacity="{go}">KAEL ODIN</text></g>')
    out.append(
        f'<text class="name-line" {name_attrs} fill="none" stroke="{t["c1"]}" stroke-width="1.3" '
        f'opacity=".6" stroke-dasharray="660 660">KAEL ODIN</text>'
    )
    out.append(
        f'<text {name_attrs} fill="url(#nameGrad)"{glow_attr}>KAEL ODIN</text>'
    )

    # Signal trace under the name: draws itself, then a pulse keeps commuting.
    out.append(f'<path d="{trace}" fill="none" stroke="{t["rule"]}" stroke-width="1.2"/>')
    out.append(
        f'<path class="trace" d="{trace}" fill="none" stroke="{t["c1"]}" stroke-width="2" '
        f'stroke-linecap="round" stroke-dasharray="600 600"/>'
    )
    for nx in (350, 930):
        out.append(f'<circle cx="{nx}" cy="250" r="3" fill="{t["c1"]}"/>')
    out.append(f'<circle class="cdot" cx="350" cy="250" r="3.5" fill="{t["c1"]}"/>')

    out.append(
        f'<text x="640" y="296" text-anchor="middle" class="han" '
        f'font-size="23" fill="{t["ink"]}">把复杂的问题，做成简单可用的工具</text>'
    )
    out.append(
        f'<text x="640" y="324" text-anchor="middle" '
        f'font-size="13" fill="{t["muted"]}" letter-spacing="3">SYSTEMS ENGINEERING · LOCAL MODELS · AGENT TOOLING · I18N</text>'
    )

    # CRT scanline sweep parked off-canvas at rest.
    out.append('<g class="scan"><rect x="-40" y="-130" width="1360" height="90" fill="url(#scanG)"/></g>')

    out.append(brackets(w, h, t))
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

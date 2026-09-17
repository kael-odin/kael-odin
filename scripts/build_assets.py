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
        "hero": {
            "bg0": "#070b0a", "bg1": "#121a17", "ink": "#eee8dc",
            "soft": "#91a097", "jade": "#72b7a6", "cinnabar": "#d45d43",
            "frame": "#46534d", "land": "#31483f", "seal_ink": "#f8eee0",
        },
        "glow": True,
    },
    "light": {
        "bg0": "#ffffff", "bg1": "#eef3fb",
        "panel": "#ffffff", "panel2": "#f4f7fc",
        "border": "#d9e2f0", "ink": "#0b1020", "muted": "#5a6b85", "dim": "#9aa8bf",
        "grid": "#dce6f5", "rule": "#d9e2f0",
        "c1": "#009e8e", "c2": "#6236c9", "c3": "#d4247a", "amber": "#b57300",
        "hero": {
            "bg0": "#f6f1e7", "bg1": "#e9e1d2", "ink": "#1d2823",
            "soft": "#617068", "jade": "#2f7e70", "cinnabar": "#b84b35",
            "frame": "#a9a194", "land": "#9cad9f", "seal_ink": "#fff8ea",
        },
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
    c = t["hero"]
    defs = (
        f'<linearGradient id="paper" x1="0" y1="0" x2="1" y2="1">'
        f'<stop stop-color="{c["bg0"]}"/>'
        f'<stop offset="100%" stop-color="{c["bg1"]}"/></linearGradient>'
        f'<radialGradient id="clearing">'
        f'<stop offset="20%" stop-color="{c["bg0"]}" stop-opacity=".96"/>'
        f'<stop offset="100%" stop-color="{c["bg0"]}" stop-opacity="0"/></radialGradient>'
        f'<pattern id="fibers" width="31" height="29" patternUnits="userSpaceOnUse">'
        f'<circle cx="3" cy="7" r=".65" fill="{c["soft"]}" opacity=".25"/>'
        f'<circle cx="21" cy="23" r=".45" fill="{c["soft"]}" opacity=".2"/>'
        f'</pattern>'
        f'<clipPath id="field"><rect x="38" y="38" width="1204" height="274"/></clipPath>'
    )
    css = """
      .display { font-family: Georgia, Cambria, 'Times New Roman', serif; }
      .han { font-family: SimSun, 'Noto Serif CJK SC', serif; }
      .signal { stroke-dasharray: 22 1200; animation: follow-ridge 14s linear infinite; }
      @keyframes follow-ridge { to { stroke-dashoffset: -1222; } }
      @media (prefers-reduced-motion: reduce) { .signal { animation: none; opacity: 0; } }
    """
    out = [head(w, h, t, defs, css.strip())]
    out.append('<title>Kael Odin — engineering in ink</title>')
    out.append('<desc>Centered name over ink-wash mountains traced like a circuit, in a light or dark palette.</desc>')
    out.append(f'<rect width="{w}" height="{h}" fill="url(#paper)"/>')
    out.append(f'<rect width="{w}" height="{h}" fill="url(#fibers)"/>')

    # A single landscape is both the Song-painting gesture and the circuit diagram.
    left = (
        'M -18 257 C 48 255 67 213 117 218 S 181 155 227 167 S 275 208 321 166 S 379 124 449 134',
        'M -18 279 C 53 274 80 235 126 240 S 186 176 236 192 S 289 226 335 186 S 389 147 451 157',
        'M -18 301 C 60 292 88 256 139 264 S 200 199 248 216 S 307 244 346 208 S 409 169 465 181',
        'M -18 325 C 60 309 97 278 147 287 S 214 223 264 240 S 318 264 361 232 S 418 192 470 205',
    )
    right = (
        'M 831 145 C 897 126 920 188 972 178 S 1036 130 1082 151 S 1139 226 1190 213 S 1251 246 1298 238',
        'M 825 169 C 886 150 923 211 977 200 S 1048 156 1091 174 S 1144 249 1194 236 S 1259 267 1298 262',
        'M 817 193 C 876 172 931 232 984 221 S 1051 178 1103 198 S 1147 272 1200 258 S 1262 289 1298 283',
        'M 809 215 C 870 197 936 255 995 245 S 1065 205 1114 223 S 1161 293 1209 281 S 1270 311 1298 305',
    )
    out.append('<g clip-path="url(#field)" fill="none">')
    for i, path in enumerate(left + right):
        out.append(
            f'<path d="{path}" stroke="{c["land"]}" stroke-width="{1.5 if i in (0, 4) else 1}" '
            f'opacity="{.84 - (i % 4) * .12:.2f}"/>'
        )
    for x, y in ((88, 189), (161, 149), (359, 137), (936, 150), (1069, 115), (1183, 184)):
        out.append(
            f'<circle cx="{x}" cy="{y}" r="2.2" fill="{c["jade"]}" opacity=".6"/>'
        )
    out.append(
        f'<path class="signal" d="{right[0]}" stroke="{c["jade"]}" '
        f'stroke-width="2.6" stroke-linecap="round" opacity=".95"/>'
    )
    out.append('</g>')
    out.append(f'<ellipse cx="640" cy="181" rx="397" ry="166" fill="url(#clearing)"/>')

    out.append(
        f'<path d="M 39 81 V 39 H 81 M 1199 39 H 1241 V 81 M 39 269 V 311 H 81 '
        f'M 1199 311 H 1241 V 269" fill="none" stroke="{c["frame"]}" stroke-width="1.2"/>'
    )
    out.append(
        f'<text x="70" y="66" font-size="15" fill="{c["soft"]}" '
        f'letter-spacing=".3">~/kael-odin</text>'
    )
    out.append(
        f'<text x="1210" y="66" font-size="15" fill="{c["soft"]}" '
        f'text-anchor="end">git branch: main</text>'
    )

    out.append(
        f'<path d="M 461 103 H 543 M 737 103 H 819" stroke="{c["frame"]}" stroke-width="1"/>'
    )
    out.append(
        f'<text x="640" y="108" text-anchor="middle" font-size="16" '
        f'letter-spacing="1.1" fill="{c["jade"]}">$ whoami</text>'
    )
    out.append(
        f'<text x="640" y="190" text-anchor="middle" class="display" '
        f'font-size="98" font-weight="700" letter-spacing="3" '
        f'fill="{c["ink"]}">KAEL ODIN</text>'
    )
    out.append(
        f'<rect x="993" y="120" width="39" height="39" rx="2" '
        f'fill="{c["cinnabar"]}" transform="rotate(7 1012.5 139.5)"/>'
    )
    out.append(
        f'<text x="1012.5" y="148" text-anchor="middle" font-size="24" class="han" '
        f'font-weight="700" fill="{c["seal_ink"]}">造</text>'
    )
    out.append(
        f'<text x="640" y="240" text-anchor="middle" font-size="23" class="han" '
        f'fill="{c["ink"]}">把复杂的问题，做成简单可用的工具</text>'
    )
    out.append(
        f'<text x="640" y="272" text-anchor="middle" font-size="16" '
        f'fill="{c["soft"]}">Systems engineering / local models / tools that ship</text>'
    )
    out.append(
        f'<path d="M 590 290 H 630 M 650 290 H 690" stroke="{c["frame"]}" stroke-width="1"/>'
        f'<circle cx="640" cy="290" r="2.5" fill="{c["cinnabar"]}"/>'
    )
    out.append('</svg>\n')
    return ''.join(out)


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

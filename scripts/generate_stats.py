#!/usr/bin/env python3
"""Generate the self-hosted stat cards for the kael-odin profile README.

Deliberately dependency-free (stdlib only) so it runs on a bare
ubuntu-latest runner with no install step. Emits:

    assets/stats-dark.svg   assets/stats-light.svg
    assets/langs-dark.svg   assets/langs-light.svg

Usage:
    python scripts/generate_stats.py [--user kael-odin] [--out assets]

The GitHub token is optional: every endpoint used here serves public data,
so unauthenticated runs work. Passing a token just raises the rate limit.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

API = "https://api.github.com"
UA = "kael-odin-profile-stats"

# --------------------------------------------------------------------------
# Theme
# --------------------------------------------------------------------------

THEMES = {
    "dark": {
        "bg0": "#05070d",
        "bg1": "#0b1220",
        "border": "#16223a",
        "ink": "#e6f1ff",
        "muted": "#7a8ba3",
        "dim": "#3c4a63",
        # cyan, magenta, violet, teal, amber, green, coral, periwinkle
        "accents": [
            "#00ffe5", "#ff2e97", "#7b2ff7", "#22d3ee",
            "#ffb020", "#36f097", "#ff6b6b", "#8b9dff",
        ],
        "glow": 0.55,
    },
    "light": {
        "bg0": "#ffffff",
        "bg1": "#f2f6fc",
        "border": "#d9e2f0",
        "ink": "#0b1020",
        "muted": "#5a6b85",
        "dim": "#a9b6cc",
        "accents": [
            "#009e8e", "#d4247a", "#6236c9", "#0e7f96",
            "#b57300", "#1f9254", "#c93b3b", "#4356b8",
        ],
        "glow": 0.0,
    },
}

FONT = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"


# --------------------------------------------------------------------------
# Fetching
# --------------------------------------------------------------------------


def api(path: str, token: str | None = None, attempts: int = 4) -> object:
    req = urllib.request.Request(API + path)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", UA)
    if token:
        req.add_header("Authorization", f"Bearer {token}")

    last: Exception | None = None
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.load(resp)
        except urllib.error.HTTPError:
            raise  # real HTTP status (404/403/...) - retrying won't help
        except Exception as exc:  # noqa: BLE001 - transient TLS/DNS resets
            last = exc
            if attempt < attempts - 1:
                time.sleep(1.5 * (attempt + 1))
    raise last  # type: ignore[misc]


def api_optional(path: str, token: str | None = None) -> object | None:
    """Return None instead of raising, so one dead endpoint can't blank the card."""
    try:
        return api(path, token)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"  ! {path} -> {exc}")
        return None


def fetch_repos(user: str, token: str | None) -> list[dict]:
    repos: list[dict] = []
    for page in range(1, 4):  # 3 pages is plenty; bail early when short
        chunk = api_optional(f"/users/{user}/repos?per_page=100&page={page}&sort=updated", token)
        if not isinstance(chunk, list) or not chunk:
            break
        repos.extend(chunk)
        if len(chunk) < 100:
            break
    return repos


def fetch_languages(repos: list[dict], token: str | None, limit: int = 40) -> dict[str, int]:
    """Aggregate byte counts per language across the largest repos."""
    totals: dict[str, int] = {}
    ordered = sorted(repos, key=lambda r: r.get("size") or 0, reverse=True)[:limit]
    for repo in ordered:
        full = repo.get("full_name")
        if not full:
            continue
        langs = api_optional(f"/repos/{full}/languages", token)
        if isinstance(langs, dict):
            for name, count in langs.items():
                totals[name] = totals.get(name, 0) + int(count)
    return totals


def fetch_contributions(user: str) -> int | None:
    """Scrape the public contribution calendar header for the 12-month total."""
    req = urllib.request.Request(
        f"https://github.com/users/{user}/contributions", headers={"User-Agent": UA}
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            html = resp.read().decode("utf-8", "replace")
    except Exception as exc:  # noqa: BLE001 - network best-effort
        print(f"  ! contributions scrape -> {exc}")
        return None
    match = re.search(r"([\d,]+)\s+contributions?\s+in the last year", html)
    if not match:
        return None
    return int(match.group(1).replace(",", ""))


def collect(user: str, token: str | None) -> dict:
    print(f"fetching stats for {user} ...")
    profile = api_optional(f"/users/{user}", token) or {}
    repos = fetch_repos(user, token)
    stars = sum(r.get("stargazers_count", 0) for r in repos)

    prs = api_optional(f"/search/issues?q=author:{user}+type:pr&per_page=1", token)
    issues = api_optional(f"/search/issues?q=author:{user}+type:issue&per_page=1", token)

    langs = fetch_languages(repos, token)
    contributions = fetch_contributions(user)

    return {
        "stars": stars,
        "repos": profile.get("public_repos", len(repos)),
        "followers": profile.get("followers", 0),
        "contributions": contributions,
        "prs": (prs or {}).get("total_count"),
        "issues": (issues or {}).get("total_count"),
        "languages": langs,
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }


# --------------------------------------------------------------------------
# Rendering helpers
# --------------------------------------------------------------------------


def fmt(value: int | None) -> str:
    if value is None:
        return "--"
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M".replace(".0M", "M")
    if value >= 10_000:
        return f"{value / 1000:.1f}k".replace(".0k", "k")
    return f"{value:,}"


def esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def svg_open(width: int, height: int, theme: dict, glow: bool = False) -> str:
    t = theme
    filters = ""
    if glow:
        # color-interpolation-filters="sRGB" is load-bearing here: the SVG
        # default of linearRGB washes the neon accents out to near-white.
        filters = """
  <defs>
    <filter id="glow" x="-40%" y="-40%" width="180%" height="180%" color-interpolation-filters="sRGB">
      <feGaussianBlur stdDeviation="2.6" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>"""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">
  <style>
    text {{ font-family: {FONT}; }}
    /* .val intentionally sets no fill: a CSS fill would beat the per-tile
       fill="" presentation attribute in the cascade and flatten every accent. */
    .val {{ font-size: 32px; font-weight: 700; }}
    .lbl {{ font-size: 10.5px; font-weight: 600; fill: {t["muted"]}; letter-spacing: 2.2px; }}
    .ttl {{ font-size: 12px; font-weight: 600; fill: {t["muted"]}; letter-spacing: 3px; }}
    .foot {{ font-size: 9.5px; fill: {t["dim"]}; letter-spacing: 1px; }}
    .sweep {{ animation: sweep 9s linear infinite; }}
    .blink {{ animation: blink 2.4s ease-in-out infinite; }}
    @keyframes sweep {{
      0%   {{ transform: translateX(-260px); }}
      100% {{ transform: translateX({width}px); }}
    }}
    @keyframes blink {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: .25; }} }}
  </style>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{t["bg0"]}"/>
      <stop offset="100%" stop-color="{t["bg1"]}"/>
    </linearGradient>
    <linearGradient id="scan" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{t["accents"][0]}" stop-opacity="0"/>
      <stop offset="50%" stop-color="{t["accents"][0]}" stop-opacity=".55"/>
      <stop offset="100%" stop-color="{t["accents"][0]}" stop-opacity="0"/>
    </linearGradient>
    <clipPath id="card"><rect x="0" y="0" width="{width}" height="{height}" rx="14"/></clipPath>
  </defs>
  <g clip-path="url(#card)">
    <rect width="{width}" height="{height}" fill="url(#bg)"/>
  </g>
  <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="13.5" fill="none" stroke="{t["border"]}" stroke-width="1"/>
  <rect class="sweep" y="0" width="260" height="1.5" fill="url(#scan)"/>
{filters}"""


def svg_close() -> str:
    return "</svg>\n"


def status_dot(x: int, y: int, theme: dict) -> str:
    accent = theme["accents"][0]
    return (
        f'<circle class="blink" cx="{x}" cy="{y}" r="3.5" fill="{accent}"/>'
        f'<circle cx="{x}" cy="{y}" r="7" fill="none" stroke="{accent}" stroke-opacity=".35"/>'
    )


# --------------------------------------------------------------------------
# Cards
# --------------------------------------------------------------------------


def render_stats(data: dict, theme: dict) -> str:
    t = theme
    w, h = 860, 214
    out = [svg_open(w, h, t, glow=t["glow"] > 0)]
    out.append(status_dot(30, 29, t))
    out.append(f'<text class="ttl" x="46" y="33">// STATS</text>')
    out.append(
        f'<text class="foot" x="{w - 24}" y="33" text-anchor="end">updated {esc(data["generated"])}</text>'
    )

    tiles = [
        ("STARS", data["stars"], 0),
        ("REPOS", data["repos"], 1),
        ("FOLLOWERS", data["followers"], 2),
        ("CONTRIBUTIONS / 12MO", data["contributions"], 3),
        ("PULL REQUESTS", data["prs"], 4),
        ("ISSUES", data["issues"], 5),
    ]

    pad, gap, cols = 24, 14, 3
    col_w = (w - pad * 2 - gap * (cols - 1)) / cols
    tile_h, row_gap, top = 68, 12, 52

    for i, (label, value, accent_idx) in enumerate(tiles):
        col, row = i % cols, i // cols
        x = pad + col * (col_w + gap)
        y = top + row * (tile_h + row_gap)
        accent = t["accents"][accent_idx]
        glow_attr = ' filter="url(#glow)"' if t["glow"] > 0 else ""

        out.append(
            f'<rect x="{x:.1f}" y="{y}" width="{col_w:.1f}" height="{tile_h}" rx="10" '
            f'fill="{accent}" fill-opacity="0.045" stroke="{t["border"]}" stroke-width="1"/>'
        )
        out.append(
            f'<rect x="{x + 12:.1f}" y="{y + 14}" width="3" height="{tile_h - 28}" rx="1.5" '
            f'fill="{accent}"/>'
        )
        out.append(
            f'<text class="val" x="{x + 26:.1f}" y="{y + 38}" fill="{accent}"{glow_attr}>'
            f'{esc(fmt(value))}</text>'
        )
        out.append(f'<text class="lbl" x="{x + 26:.1f}" y="{y + 57}">{esc(label)}</text>')

    out.append(svg_close())
    return "".join(out)


# Neon palette order doubles as the language colour ramp so the theme stays coherent.
def render_langs(data: dict, theme: dict) -> str:
    t = theme
    w, h = 860, 186
    out = [svg_open(w, h, t, glow=t["glow"] > 0)]

    langs = data.get("languages") or {}
    total = sum(langs.values())
    ranked = sorted(langs.items(), key=lambda kv: kv[1], reverse=True)[:8]

    out.append(status_dot(30, 29, t))
    out.append('<text class="ttl" x="46" y="33">// LANGUAGES</text>')
    if not total:
        out.append(f'<text class="lbl" x="24" y="80">no language data</text>')
        out.append(svg_close())
        return "".join(out)

    # Stacked byte-share bar
    bar_x, bar_y, bar_w, bar_h, rx = 24, 50, w - 48, 16, 8
    out.append(
        f'<clipPath id="bar"><rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="{bar_h}" rx="{rx}"/></clipPath>'
    )
    out.append(f'<g clip-path="url(#bar)">')
    cursor = bar_x
    for i, (_, count) in enumerate(ranked):
        seg = bar_w * count / total
        if i == len(ranked) - 1:
            seg = bar_x + bar_w - cursor
        out.append(
            f'<rect x="{cursor:.2f}" y="{bar_y}" width="{max(seg, 0):.2f}" height="{bar_h}" '
            f'fill="{t["accents"][i % len(t["accents"])]}"/>'
        )
        cursor += seg
    out.append("</g>")
    out.append(
        f'<rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="{bar_h}" rx="{rx}" '
        f'fill="none" stroke="{t["border"]}" stroke-width="1"/>'
    )

    # Legend chips, 2 rows x 4
    chip_w = (w - 48) / 4
    for i, (name, count) in enumerate(ranked):
        col, row = i % 4, i // 4
        x = 24 + col * chip_w
        y = 100 + row * 32
        accent = t["accents"][i % len(t["accents"])]
        pct = count * 100 / total
        out.append(f'<rect x="{x:.1f}" y="{y - 9}" width="10" height="10" rx="3" fill="{accent}"/>')
        label = name if len(name) <= 16 else name[:15] + "…"
        out.append(
            f'<text x="{x + 18:.1f}" y="{y}" font-size="12" fill="{t["ink"]}">{esc(label)}</text>'
        )
        out.append(
            f'<text x="{x + 18:.1f}" y="{y + 14}" font-size="10" fill="{t["muted"]}">'
            f'{pct:.1f}%</text>'
        )

    out.append(
        f'<text class="foot" x="{w - 24}" y="{h - 12}" text-anchor="end">'
        f'{len(langs)} languages · {total / 1_000_000:.2f} MB of code indexed</text>'
    )
    out.append(svg_close())
    return "".join(out)


# --------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--user", default=os.environ.get("GH_USER", "kael-odin"))
    parser.add_argument("--out", default="assets")
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    data = collect(args.user, token)

    for name, theme in THEMES.items():
        for kind, renderer in (("stats", render_stats), ("langs", render_langs)):
            path = os.path.join(args.out, f"{kind}-{name}.svg")
            with open(path, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(renderer(data, theme))
            print(f"  wrote {path}")

    print(
        f"done: {data['stars']} stars, {data['repos']} repos, "
        f"{data['followers']} followers, {data['contributions']} contributions"
    )


if __name__ == "__main__":
    main()

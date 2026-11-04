#!/usr/bin/env python3
"""Render the profile's public GitHub data, using only the Python stdlib.

Daily update (the token is optional)::

    python scripts/generate_stats.py --user kael-odin --out assets

Offline restyling, with no network requests::

    python scripts/generate_stats.py --snapshot assets/profile-data.json --out assets

A successful collection saves profile-data.json alongside stats-dark/light.svg
and langs-dark/light.svg. Missing measurements remain null, never invented zeros.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html import escape
from pathlib import Path

API = "https://api.github.com"
UA = "kael-odin-profile-stats"
LANGUAGE_REPO_LIMIT = 40
METRICS = (
    ("stars", "Stars earned"),
    ("repos", "Public repositories"),
    ("followers", "Followers"),
    ("contributions", "Contributions / 12 mo"),
    ("prs", "Pull requests"),
    ("issues", "Issues opened"),
)

THEMES = {
    "dark": {
        "bg": "#111315",
        "ink": "#f3eee6",
        "muted": "#aaa69f",
        "copper": "#e8b983",
        "accent": "#9baec4",
    },
    "light": {
        "bg": "#f5f2ec",
        "ink": "#242423",
        "muted": "#666761",
        "copper": "#986232",
        "accent": "#536b85",
    },
}

FONT = "'Segoe UI', Helvetica, Arial, sans-serif"
TITLE_FONT = "'Iowan Old Style', 'Palatino Linotype', Georgia, serif"
INVALID_XML = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\ud800-\udfff\U0000FFFE\U0000FFFF]")


# --------------------------------------------------------------------------
# Collection. An empty successful response and an unavailable endpoint differ.
# --------------------------------------------------------------------------


def count(value: object) -> int | None:
    """Accept actual, nonnegative integer measurements, including a real zero."""
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


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
            raise  # A real HTTP status is not a transient TLS/DNS reset.
        except (OSError, json.JSONDecodeError) as exc:
            last = exc
            if attempt < attempts - 1:
                time.sleep(1.5 * (attempt + 1))
    if last is not None:
        raise last
    raise ValueError("attempts must be positive")


def api_optional(path: str, token: str | None = None) -> object | None:
    """One unavailable endpoint must not turn the other measurements into zero."""
    try:
        return api(path, token)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"  ! {path} -> {exc}")
        return None


def fetch_repos(user: str, token: str | None) -> list[dict] | None:
    """Fetch all public repositories; never present a partial star sum as a total."""
    repos: list[dict] = []
    page = 1
    while True:
        chunk = api_optional(
            f"/users/{urllib.parse.quote(user, safe='')}/repos?per_page=100&page={page}&sort=updated",
            token,
        )
        if not isinstance(chunk, list) or any(not isinstance(repo, dict) for repo in chunk):
            return None
        repos.extend(chunk)
        if len(chunk) < 100:
            return repos
        page += 1


def fetch_languages(
    repos: list[dict] | None, token: str | None, limit: int = LANGUAGE_REPO_LIMIT
) -> dict[str, int] | None:
    """Sum bytes actually returned for up to 40 of the largest public repositories.

    Failed samples are excluded, not filled with zero. These are sampled bytes,
    not a census of every repository and certainly not a measure of proficiency.
    """
    if repos is None:
        return None
    ordered = sorted(
        (repo for repo in repos if repo.get("private") is not True),
        key=lambda repo: count(repo.get("size")) or 0,
        reverse=True,
    )[:limit]
    totals: dict[str, int] = {}
    successful = not ordered  # No repositories is a known empty sample.
    for repo in ordered:
        full = repo.get("full_name")
        if not isinstance(full, str) or not full:
            continue
        langs = api_optional(f"/repos/{urllib.parse.quote(full, safe='/')}/languages", token)
        if not isinstance(langs, dict) or any(
            not isinstance(name, str) or count(size) is None for name, size in langs.items()
        ):
            continue
        successful = True
        for name, size in langs.items():
            totals[name] = totals.get(name, 0) + size
    return totals if successful else None


def fetch_contributions(user: str) -> int | None:
    """Read the public contribution calendar's own rolling 12-month total."""
    req = urllib.request.Request(
        f"https://github.com/users/{urllib.parse.quote(user, safe='')}/contributions",
        headers={"User-Agent": UA},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            html = resp.read().decode("utf-8", "replace")
    except OSError as exc:
        print(f"  ! contributions scrape -> {exc}")
        return None
    match = re.search(r"([\d,]+)\s+contributions?\s+in the last year", html)
    return int(match.group(1).replace(",", "")) if match else None


def collect(user: str, token: str | None) -> dict:
    print(f"fetching stats for {user} ...")
    profile = api_optional(f"/users/{urllib.parse.quote(user, safe='')}", token)
    profile = profile if isinstance(profile, dict) else {}
    repos = fetch_repos(user, token)
    stars = None
    if repos is not None:
        star_counts = [count(repo.get("stargazers_count")) for repo in repos]
        if all(value is not None for value in star_counts):
            stars = sum(value for value in star_counts if value is not None)

    def search_total(kind: str) -> int | None:
        query = urllib.parse.urlencode({"q": f"author:{user} type:{kind}", "per_page": 1})
        response = api_optional(f"/search/issues?{query}", token)
        if not isinstance(response, dict) or response.get("incomplete_results") is True:
            return None
        return count(response.get("total_count"))

    repo_count = count(profile.get("public_repos"))
    if repo_count is None and repos is not None:
        repo_count = len(repos)
    return {
        "schema_version": 1,
        "user": user,
        "stars": stars,
        "repos": repo_count,
        "followers": count(profile.get("followers")),
        "contributions": fetch_contributions(user),
        "prs": search_total("pr"),
        "issues": search_total("issue"),
        "languages": fetch_languages(repos, token),
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }


# --------------------------------------------------------------------------
# Rendering helpers
# --------------------------------------------------------------------------


def fmt(value: object) -> str:
    value = count(value)
    if value is None:
        return "—"
    for scale, suffix in ((10**12, "T"), (10**9, "B"), (10**6, "M")):
        if value >= scale:
            return f"{value / scale:.1f}".removesuffix(".0") + suffix
    if value >= 10_000:
        return f"{value / 1000:.1f}".removesuffix(".0") + "k"
    return f"{value:,}"


def esc(text: object) -> str:
    """Escape markup and remove characters XML 1.0 cannot represent."""
    return escape(INVALID_XML.sub("", str(text)), quote=True)


def language_rows(languages: object, limit: int = 6) -> list[tuple[str, int]]:
    """Top six plus an explicit byte-exact Other; no bytes are lost in truncation.

    Treat an existing Other entry as an aggregate too, so a restyled snapshot
    cannot produce two identically named Other segments. Zero-byte languages do
    not occupy a display slot or change the denominator.
    """
    if not isinstance(languages, dict):
        return []
    clean = {
        name: size for name, size in languages.items()
        if isinstance(name, str) and name and count(size) is not None and size > 0
    }
    other = clean.pop("Other", 0)
    ranked = sorted(clean.items(), key=lambda pair: (-pair[1], pair[0].casefold(), pair[0]))
    rows = ranked[:limit]
    other += sum(size for _, size in ranked[limit:])
    if other:
        rows.append(("Other", other))
    return rows


def percentage(size: int, total: int) -> str:
    share = size * 100 / total
    return "<0.1%" if share < 0.1 else f"{share:.1f}%"


def svg_open(height: int, theme: dict, kind: str, title: str, description: str) -> str:
    t = theme
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="{height}" viewBox="0 0 1200 {height}" role="img" aria-labelledby="{kind}-title {kind}-desc">
  <title id="{kind}-title">{esc(title)}</title>
  <desc id="{kind}-desc">{esc(description)}</desc>
  <style>
    text {{ font-family: {FONT}; fill: {t["ink"]}; }}
    .title {{ font-family: {TITLE_FONT}; font-size: 26px; }}
    .meta {{ font-size: 20px; fill: {t["muted"]}; }}
    .value {{ font-size: 68px; font-weight: 500; letter-spacing: -2px; }}
    .secondary {{ font-size: 64px; }}
    .label {{ font-size: 22px; fill: {t["muted"]}; }}
    .language {{ font-size: 22px; }}
    .share {{ font-size: 32px; font-variant-numeric: tabular-nums; }}
    .empty {{ font-size: 32px; }}
  </style>
  <rect width="1200" height="{height}" fill="{t["bg"]}"/>
  <path d="M40 54.5H1160" fill="none" stroke="{t["accent"]}" stroke-opacity=".3"/>
  <path d="M40 54.5H104" fill="none" stroke="{t["copper"]}"/>
  <text class="title" x="40" y="35">{esc(title)}</text>
'''


def render_stats(data: dict, theme: dict) -> str:
    values = [(key, label, count(data.get(key))) for key, label in METRICS]
    description = "; ".join(
        f"{label}: {value:,}" if value is not None else f"{label}: unavailable"
        for _, label, value in values
    )
    description += ". An em dash means unavailable, not zero. Contributions cover the last 12 months."
    out = [svg_open(280, theme, "stats", "GitHub activity", description)]
    generated = data.get("generated")
    updated = f"Updated {generated}" if generated else "Update time unavailable"
    if any(value is None for _, _, value in values):
        updated += " · — unavailable"
    out.append(f'<text class="meta" x="1160" y="35" text-anchor="end">{esc(updated)}</text>\n')
    out.append(
        f'<path d="M40 175.5H1160" fill="none" stroke="{theme["ink"]}" stroke-opacity=".18"/>\n'
    )
    for index, (_, label, value) in enumerate(values):
        x = 40 + (index % 3) * 384
        row = index // 3
        value_y, label_y = (125, 156) if row == 0 else (237, 266)
        style = "value" if row == 0 else "value secondary"
        out.append(
            f'<g><title>{esc(label)}: {esc(f"{value:,}" if value is not None else "unavailable")}</title>'
            f'<text class="{style}" x="{x}" y="{value_y}">{esc(fmt(value))}</text>'
            f'<text class="label" x="{x}" y="{label_y}">{esc(label)}</text></g>\n'
        )
    out.append("</svg>\n")
    return "".join(out)


def render_langs(data: dict, theme: dict) -> str:
    rows = language_rows(data.get("languages"))
    total = sum(size for _, size in rows)  # Includes every sampled byte, including Other.
    caveat = "Measured public repo language bytes — not skill levels."
    description = caveat + " Up to 40 of the largest public repositories are sampled; unavailable responses are excluded. "
    description += "Segments follow the language list in reading order. "
    if total:
        description += "; ".join(
            f"{name}: {size:,} bytes ({percentage(size, total)})" for name, size in rows
        )
        description += f". Denominator: all {total:,} sampled bytes. Percentages are rounded."
    else:
        description += "No language byte measurements to display."
    out = [svg_open(328, theme, "langs", "Repository languages", description)]
    out.append(f'<text class="meta" x="40" y="79">{esc(caveat)}</text>\n')
    if not total:
        known_empty = isinstance(data.get("languages"), dict)
        message = "No language bytes measured" if known_empty else "Language data unavailable"
        explanation = (
            "The sampled public repositories returned no language bytes."
            if known_empty else "No successful language sample is available in this snapshot."
        )
        out.append(f'<text class="empty" x="40" y="166">{message}</text>\n')
        out.append(f'<text class="meta" x="40" y="204">{explanation}</text>\n')
        out.append("</svg>\n")
        return "".join(out)

    language_count = sum(
        1 for name, size in data["languages"].items()
        if isinstance(name, str) and name and count(size) is not None and size > 0
    )
    out.append(
        f'<text class="meta" x="1160" y="35" text-anchor="end">'
        f'{language_count} languages · public repo sample</text>\n'
    )
    # One quiet ink, not seven categorical hues. The strip and the list share
    # reading order, with exact counts in titles/desc; hue never carries identity.
    # Calculate every segment from its own bytes. In particular, the sixth
    # language must NOT inherit bytes belonging to the undisplayed tail.
    bar_x, bar_y, bar_width, bar_height = 40, 99, 1120, 14
    cumulative = 0
    boundaries = []
    for name, size in rows:
        x = bar_x + bar_width * cumulative / total
        width = bar_width * size / total
        out.append(
            f'<rect class="language-segment" x="{x:.6f}" y="{bar_y}" width="{width:.6f}" '
            f'height="{bar_height}" fill="{theme["copper"]}" data-bytes="{size}">'
            f'<title>{esc(name)}: {size:,} bytes · {esc(percentage(size, total))}</title></rect>\n'
        )
        cumulative += size
        if cumulative < total:
            boundaries.append(bar_x + bar_width * cumulative / total)
    # Surface-colored separators overlay the true widths, rather than changing
    # the byte-to-width mapping or artificially enlarging tiny categories.
    for x in boundaries:
        out.append(
            f'<path d="M{x:.6f} {bar_y}v{bar_height}" stroke="{theme["bg"]}" stroke-width="2"/>\n'
        )

    for index, (name, size) in enumerate(rows):
        x = 40 + (index % 4) * 288
        y = 149 + (index // 4) * 84
        label = name if len(name) <= 20 else name[:19] + "…"
        out.append(
            f'<g><title>{esc(name)}: {size:,} of {total:,} sampled bytes</title>'
            f'<text class="language" x="{x}" y="{y}">{esc(label)}</text>'
            f'<text class="share" x="{x}" y="{y + 34}">{esc(percentage(size, total))}</text></g>\n'
        )
    out.append(
        f'<text class="meta" x="40" y="309">'
        f'{total:,} bytes measured · segments follow the list, left to right</text>\n'
    )
    out.append("</svg>\n")
    return "".join(out)


def mobile_open(height: int, theme: dict, title: str, description: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="720" height="{height}" viewBox="0 0 720 {height}" role="img" aria-labelledby="title desc">
<title id="title">{esc(title)}</title><desc id="desc">{esc(description)}</desc>
<style>text{{font-family:{FONT};fill:{theme['ink']}}}.muted{{fill:{theme['muted']}}}</style>
<rect width="720" height="{height}" rx="22" fill="{theme['bg']}"/>
<text x="40" y="54" font-size="30">{esc(title)}</text>
<path d="M40 78H680" stroke="{theme['accent']}" stroke-opacity=".3"/>
'''


def render_stats_mobile(data: dict, theme: dict) -> str:
    description = "; ".join(f"{label}: {fmt(data.get(key))}" for key, label in METRICS)
    out = [mobile_open(570, theme, "GitHub activity", description + ". An em dash means unavailable.")]
    for index, (key, label) in enumerate(METRICS):
        x, y = 40 + index % 2 * 334, 163 + index // 2 * 143
        out.append(f'<text x="{x}" y="{y}" font-size="62">{esc(fmt(data.get(key)))}</text>')
        out.append(f'<text x="{x}" y="{y + 39}" font-size="25" class="muted">{esc(label)}</text>')
    out.append(f'<text x="40" y="540" font-size="21" class="muted">{esc(data.get("generated") or "Update time unavailable")}</text></svg>\n')
    return "".join(out)


def render_langs_mobile(data: dict, theme: dict) -> str:
    rows = language_rows(data.get("languages"))
    total = sum(size for _, size in rows)
    description = "Measured public repo bytes, not skill levels. " + "; ".join(
        f"{name}: {size:,} bytes ({percentage(size, total)})" for name, size in rows
    )
    height = max(310, 188 + len(rows) * 76)
    out = [mobile_open(height, theme, "Repository languages", description)]
    out.append('<text x="40" y="115" font-size="23" class="muted">PUBLIC REPO BYTES / NOT SKILL LEVELS</text>')
    if not total:
        out.append('<text x="40" y="215" font-size="30" class="muted">No language measurements</text>')
    for index, (name, size) in enumerate(rows):
        y = 165 + index * 76
        label = name if len(name) <= 32 else name[:31] + "…"
        out.append(f'<text x="40" y="{y}" font-size="27">{esc(label)}</text>')
        out.append(f'<text x="680" y="{y}" font-size="27" text-anchor="end">{esc(percentage(size, total))}</text>')
        out.append(f'<rect x="40" y="{y + 16}" width="640" height="12" rx="4" fill="{theme["accent"]}" opacity=".16"/>')
        out.append(f'<rect x="40" y="{y + 16}" width="{640 * size / total:.6f}" height="12" rx="4" fill="{theme["copper"]}" data-bytes="{size}"/>')
    out.append('</svg>\n')
    return "".join(out)


# --------------------------------------------------------------------------
# Offline snapshots and the existing daily CLI
# --------------------------------------------------------------------------


def load_snapshot(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("snapshot must be a JSON object")
    for key, _ in METRICS:
        if data.get(key) is not None and count(data[key]) is None:
            raise ValueError(f"{key} must be a nonnegative integer or null")
    languages = data.get("languages")
    if languages is not None and (
        not isinstance(languages, dict) or any(
            not isinstance(name, str) or not name or count(size) is None
            for name, size in languages.items()
        )
    ):
        raise ValueError("languages must be an object of nonnegative byte counts or null")
    if data.get("generated") is not None and not isinstance(data["generated"], str):
        raise ValueError("generated must be a string or null")
    return data


def has_measurements(data: dict) -> bool:
    return any(count(data.get(key)) is not None for key, _ in METRICS) or isinstance(data.get("languages"), dict)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--user", default=os.environ.get("GH_USER", "kael-odin"))
    parser.add_argument("--out", default="assets")
    parser.add_argument("--snapshot", type=Path, help="Render a profile-data.json file without fetching anything")
    args = parser.parse_args(argv)

    if args.snapshot is not None:
        try:
            data = load_snapshot(args.snapshot)
        except (OSError, ValueError) as exc:
            parser.error(f"cannot load snapshot: {exc}")
    else:
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        data = collect(args.user, token)
        if not has_measurements(data):
            raise SystemExit("No GitHub data collected; existing assets and snapshot were left unchanged.")

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if args.snapshot is None:
        path = out / "profile-data.json"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        print(f"  wrote {path}")
    for name, theme in THEMES.items():
        for kind, renderer in (("stats", render_stats), ("langs", render_langs),
                               ("stats-mobile", render_stats_mobile), ("langs-mobile", render_langs_mobile)):
            path = out / (f"{kind[:-7]}-{name}-mobile.svg" if kind.endswith("-mobile") else f"{kind}-{name}.svg")
            path.write_text(renderer(data, theme), encoding="utf-8", newline="\n")
            print(f"  wrote {path}")
    print("done: " + ", ".join(f"{label.lower()} {fmt(data.get(key))}" for key, label in METRICS))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Build the profile's original, self-contained vector artwork.

A projected metallic trefoil is the identity, not a stock illustration. Its
geometry, surface normals and lighting are computed here. Static SVGs work
without JavaScript; render_readme.cjs optionally renders the same scene as GIF.

python scripts/build_assets.py --out assets
"""
from __future__ import annotations

import argparse
import json
import math
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FONT = "Arial, 'Segoe UI', 'Noto Sans', sans-serif"
HAN = "'Microsoft YaHei', 'Noto Sans SC', sans-serif"
MONO = "Consolas, 'Liberation Mono', monospace"
THEMES = {
    "dark": {
        "bg": "#111315", "panel": "#191c1f", "ink": "#f3eee6",
        "muted": "#aaa69f", "dim": "#767b7d", "line": "#373b3d",
        "copper": "#e8b983", "blue": "#9baec4", "shadow": "#07090b",
    },
    "light": {
        "bg": "#f5f2ec", "panel": "#ede9e1", "ink": "#242423",
        "muted": "#666761", "dim": "#74756f", "line": "#d2cec4",
        "copper": "#986232", "blue": "#536b85", "shadow": "#c2b7a8",
    },
}


def text(x, y, value, size=24, fill="#f3eee6", weight=400, font=FONT, **attrs):
    attr = " ".join(f'{k.replace("_", "-")}="{escape(str(v), quote=True)}"' for k, v in attrs.items())
    return (f'<text x="{x}" y="{y}" font-family="{font}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" {attr}>{escape(value)}</text>')


def line(x1, y1, x2, y2, color, opacity=1):
    return (f'<path d="M{x1} {y1}H{x2}" stroke="{color}" opacity="{opacity}"/>'
            if y1 == y2 else
            f'<path d="M{x1} {y1}L{x2} {y2}" stroke="{color}" opacity="{opacity}"/>')


def document(w, h, t, title, body, defs="", css=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" role="img" aria-labelledby="title desc">\n'
            f'<title id="title">{escape(title)}</title>\n'
            f'<desc id="desc">{escape(title)}. Original artwork for Kael Odin.</desc>\n'
            f'<defs>{defs}<clipPath id="canvas"><rect width="{w}" height="{h}" rx="22"/></clipPath></defs>\n'
            f'<style>text{{text-rendering:geometricPrecision}} {css}'
            '@media(prefers-reduced-motion:reduce){*{animation:none!important}}</style>\n'
            f'<g clip-path="url(#canvas)"><rect width="{w}" height="{h}" fill="{t["bg"]}"/>'
            f'{body}</g></svg>\n')


def normalized(a):
    length = math.sqrt(sum(v * v for v in a))
    return tuple(v / length for v in a)


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def center(u):
    r = 2 + .66 * math.cos(3 * u)
    return (r * math.cos(2 * u), r * math.sin(2 * u), .86 * math.sin(3 * u))


def rotate(p, phase):
    x, y, z = p
    ax, ay, az = .84 + .08 * math.cos(phase), .22 + .42 * math.sin(phase), -.28
    y, z = y * math.cos(ax) - z * math.sin(ax), y * math.sin(ax) + z * math.cos(ax)
    x, z = x * math.cos(ay) + z * math.sin(ay), -x * math.sin(ay) + z * math.cos(ay)
    return (x * math.cos(az) - y * math.sin(az), x * math.sin(az) + y * math.cos(az), z)


def sculpture(cx, cy, scale, phase=0):
    """Painter-sorted tube mesh, with directional and specular copper lighting."""
    around, sides = 128, 16
    light = normalized((-.4, -.7, 1.4))
    points, normals = [], []
    for i in range(around):
        u = i / around * math.tau
        c, nxt = center(u), center(u + .001)
        tangent = normalized(tuple(nxt[k] - c[k] for k in range(3)))
        normal = normalized(cross(tangent, (0, 0, 1)))
        bitangent = cross(tangent, normal)
        ring, nr = [], []
        for j in range(sides):
            v = j / sides * math.tau
            n = tuple(normal[k] * math.cos(v) + bitangent[k] * math.sin(v) for k in range(3))
            ring.append(rotate(tuple(c[k] + .29 * n[k] for k in range(3)), phase))
            nr.append(rotate(n, phase))
        points.append(ring)
        normals.append(nr)
    faces = []
    for i in range(around):
        for j in range(sides):
            corners = [(i, j), ((i + 1) % around, j), ((i + 1) % around, (j + 1) % sides), (i, (j + 1) % sides)]
            ps = [points[a][b] for a, b in corners]
            n = normalized(tuple(sum(normals[a][b][k] for a, b in corners) / 4 for k in range(3)))
            diffuse = max(0, sum(n[k] * light[k] for k in range(3)))
            half = normalized((light[0], light[1], light[2] + 1))
            specular = max(0, sum(n[k] * half[k] for k in range(3))) ** 28
            shade = min(1, .14 + .64 * diffuse + .6 * specular)
            rgb = tuple(round(a + (b - a) * shade) for a, b in zip((42, 31, 25), (255, 222, 181)))
            color = '#' + ''.join(f'{c:02x}' for c in rgb)
            coords = ' '.join(f'{cx + x * scale:.2f},{cy + y * scale:.2f}' for x, y, _ in ps)
            faces.append((sum(p[2] for p in ps), f'<polygon points="{coords}" fill="{color}" stroke="{color}" stroke-width=".38" stroke-linejoin="round"/>'))
    return ''.join(svg for _, svg in sorted(faces))


def hero(t, mobile=False, phase=0):
    w, h = (720, 920) if mobile else (1200, 620)
    cx, cy, scale = (370, 674, 85) if mobile else (913, 305, 83)
    title_size = 128 if mobile else 138
    defs = (f'<radialGradient id="ambient"><stop stop-color="{t["copper"]}" stop-opacity=".17"/>'
            '<stop offset="1" stop-color="#e8b983" stop-opacity="0"/></radialGradient>'
            '<filter id="soft"><feGaussianBlur stdDeviation="13"/></filter>')
    b = [f'<ellipse cx="{cx}" cy="{cy}" rx="310" ry="300" fill="url(#ambient)"/>']
    b.append(text(48, 53, 'K / O', 22, t['copper'], 700, MONO, letter_spacing=2))
    b.append(text(w - 48, 52, 'ENGINEERING / IN THE OPEN', 14 if mobile else 16, t['muted'], font=MONO, text_anchor='end', letter_spacing=1.6))
    b.append(line(48, 78, w - 48, 78, t['line']))
    b.append(text(48, 131 if mobile else 144, 'FULL-STACK  /  SYSTEMS ENGINEER', 17 if mobile else 18, t['muted'], font=MONO, letter_spacing=1))
    b.append(text(40, 261 if mobile else 290, 'KAEL', title_size, t['ink'], 900, letter_spacing=-7))
    b.append(text(40, 387 if mobile else 420, 'ODIN.', title_size, t['copper'], 900, letter_spacing=-8))
    b.append(text(48, 442 if mobile else 480, '把想法变成仓库。', 33 if mobile else 32, t['ink'], 500, HAN, letter_spacing=2))
    if not mobile:
        b.append(text(48, 514, 'LOCAL MODELS. USEFUL TOOLS. OPEN SOURCE.', 16, t['muted'], font=MONO))
    # The orbit has a quiet rear half and a bright foreground arc.
    b.append(f'<ellipse cx="{cx}" cy="{cy + 48}" rx="264" ry="103" fill="none" stroke="{t["line"]}" transform="rotate(-24 {cx} {cy + 48})"/>')
    b.append(f'<ellipse cx="{cx}" cy="{cy + 151}" rx="142" ry="22" fill="{t["shadow"]}" opacity=".65" filter="url(#soft)"/>')
    b.append(sculpture(cx, cy, scale, phase))
    b.append(f'<path d="M{cx - 211} {cy + 164}Q{cx - 125} {cy + 205} {cx + 205} {cy - 22}" fill="none" stroke="{t["copper"]}" stroke-width="1.2" opacity=".55"/>')
    b.append(f'<circle cx="{cx + 205}" cy="{cy - 22}" r="4" fill="{t["copper"]}"/>')
    if not mobile:
        b.append(text(708, 113, '01 / THE BUILDER’S KNOT', 14, t['muted'], font=MONO, letter_spacing=1))
        b.append(text(1147, 514, 'IDEA → SYSTEM → REPOSITORY', 14, t['muted'], font=MONO, text_anchor='end'))
    by = h - 58
    b.append(line(48, by - 23, w - 48, by - 23, t['line']))
    for x, s in zip((48, w * .39, w - 48), ('LOCAL INFERENCE', 'AGENT SYSTEMS', 'ZH-CN / I18N')):
        b.append(text(x, by + 7, s, 15 if mobile else 17, t['muted'], font=MONO, text_anchor='end' if x == w - 48 else 'start'))
    return document(w, h, t, 'Kael Odin — full-stack and systems engineer, local inference, agent tooling, Chinese localization', ''.join(b), defs)


def focus(t, mobile=False):
    w, h = (720, 500) if mobile else (1200, 286)
    items = [('01', 'LOCAL INFERENCE', '本地推理与显存优化'), ('02', 'AGENT SYSTEMS', '把工具连接成工作流'), ('03', 'LOCALIZATION', '让好工具说中文'), ('04', 'DATA ENGINEERING', '从采集到结构化数据')]
    b = []
    for i, (n, label, detail) in enumerate(items):
        x, y = (42 + (i % 2) * 338, 74 + (i // 2) * 220) if mobile else (40 + i * 296, 76)
        b.append(text(x, y, n, 26, t['copper'], 400, MONO))
        b.append(line(x, y + 28, x + (285 if mobile else 240), y + 28, t['line']))
        b.append(text(x, y + 76, label, 21 if mobile else 20, t['ink'], 700, letter_spacing=.3))
        b.append(text(x, y + 119, detail, 23 if mobile else 22, t['muted'], font=HAN))
    return document(w, h, t, 'Focus: local inference, agent systems, localization and data engineering', ''.join(b))


def readable_brand(hex_color, t):
    def luminance(rgb):
        values = [v / 255 for v in rgb]
        linear = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in values]
        return sum(v * k for v, k in zip(linear, (.2126, .7152, .0722)))
    rgb = [int(hex_color[k:k + 2], 16) for k in (0, 2, 4)]
    bg = luminance([int(t['bg'][k:k + 2], 16) for k in (1, 3, 5)])
    target = [int(t['ink'][k:k + 2], 16) for k in (1, 3, 5)]
    for _ in range(25):
        value = luminance(rgb)
        if (max(value, bg) + .05) / (min(value, bg) + .05) >= 3:
            break
        rgb = [round(v + (goal - v) * .18) for v, goal in zip(rgb, target)]
    return '#' + ''.join(f'{v:02x}' for v in rgb)


def toolkit(t, mobile=False):
    icons = json.loads((ROOT / 'assets/readme/source/brand-icons.json').read_text(encoding='utf-8'))
    w, h = (720, 694) if mobile else (1200, 358)
    b = []
    groups = ['CODE / RUNTIMES', 'BUILD / DELIVERY', 'INFRASTRUCTURE / DATA']
    for i, icon in enumerate(icons):
        if mobile:
            x, y = 40 + (i % 3) * 230, 65 + (i // 3) * 104
            size = 34
        else:
            row, col = i // 6, i % 6
            x, y, size = 235 + col * 158, 69 + row * 110, 30
            if col == 0:
                b.append(text(32, y + 4, groups[row].split(' / ')[0], 16, t['muted'], font=MONO))
                b.append(text(32, y + 28, '/ ' + groups[row].split(' / ')[1], 16, t['muted'], font=MONO))
                if row < 2:
                    b.append(line(32, y + 60, w - 32, y + 60, t['line']))
        color = readable_brand(icon['hex'], t)
        b.append(f'<g transform="translate({x} {y - 23}) scale({size / 24})"><path d="{icon["path"]}" fill="{color}"/></g>')
        b.append(text(x + size + 12 if mobile else x, y + 3 if mobile else y + 42, icon['title'], 24 if mobile else 19, t['ink']))
    return document(w, h, t, 'Tools: TypeScript, Python, Go, C++, JavaScript, Node.js, React, Vue, Vite, FastAPI, Docker, Linux, Git, Nginx, Redis, PostgreSQL, MySQL, Cloudflare', ''.join(b))


def footer(t, mobile=False):
    w, h = (720, 314) if mobile else (1200, 230)
    b = [line(42, 38, w - 42, 38, t['line'])]
    b.append(text(42, 105, 'GOOD TOOLS.', 54 if mobile else 56, t['ink'], 800, letter_spacing=-2))
    b.append(text(42, 171, 'SHOULD BE SHARED.', 49 if mobile else 56, t['copper'], 800, letter_spacing=-2))
    if not mobile:
        b.append(text(w - 42, 102, 'KAEL ODIN', 22, t['ink'], 700, MONO, text_anchor='end'))
        b.append(text(w - 42, 141, 'KEEP BUILDING ↗', 17, t['muted'], font=MONO, text_anchor='end'))
    b.append(text(42, h - 25, '把工具做好，把过程开源。', 24, t['muted'], font=HAN))
    return document(w, h, t, 'Good tools should be shared. Kael Odin — keep building.', ''.join(b))


def terminal(t):
    b = [text(48, 57, '$ whoami', 22, t['copper'], font=MONO),
         text(48, 137, 'kael-odin', 66, t['ink'], 700),
         text(48, 193, 'Full-stack / systems engineer at Thordata', 26, t['muted']),
         line(640, 40, 640, 210, t['line'])]
    for i, s in enumerate(['local inference', 'agent tooling', 'Chinese localization']):
        b.append(text(690, 70 + i * 61, f'0{i + 1}  {s}', 25, t['ink'], font=MONO))
    return document(1200, 250, t, 'Kael Odin — engineer at Thordata', ''.join(b))


def divider(t):
    return document(1200, 18, t, 'Section divider', line(0, 9, 1200, 9, t['line']))


PROJECTS = [
    {'id': 'research', 'number': '01', 'category': 'RESEARCH / DISCOVERY',
     'title': ['Academic', 'Research Skills'], 'zh': ['科研工具太多，', '先把值得用的找出来。'],
     'tags': 'DAILY RANKING  /  AGENT SKILLS', 'capture': 'research.png',
     'url': 'https://kael-odin.github.io/awesome-academic-research-skills/'},
    {'id': 'plugins', 'number': '02', 'category': 'LOCALIZATION / TOOLING',
     'title': ['Good tools.', 'In Chinese.'], 'zh': ['同步、汉化、验证，', '让插件市场真正可用。'],
     'tags': 'CODEX  /  CLAUDE CODE  /  ZCODE', 'capture': 'plugins.png',
     'url': 'https://kael-odin.github.io/codex-plugins-zh/'},
    {'id': 'bifrost', 'number': '04', 'category': 'INTERFACES / PERSONAL SYSTEMS',
     'title': ['The Odin', 'Collection.'], 'zh': ['主页、作品集与数字花园，', '给每一种表达一个空间。'],
     'tags': 'BIFROST  /  VALHALLA  /  SAGA', 'capture': 'bifrost.png',
     'url': 'https://kael-odin.github.io/odin-bifrost/'},
]


def project_card(t, p, mobile=False):
    w, h = (720, 784) if mobile else (1200, 430)
    sx, sy, sw, sh = (40, 345, 640, 382) if mobile else (604, 53, 572, 342)
    image_path = '../captures/' + p['capture']
    defs = f'<clipPath id="screen"><rect x="{sx}" y="{sy}" width="{sw}" height="{sh}" rx="10"/></clipPath>'
    b = [text(40, 50, p['number'] + ' / ' + p['category'], 18 if mobile else 17, t['copper'], font=MONO)]
    for i, s in enumerate(p['title']):
        b.append(text(38, 124 + i * 64, s, 56 if mobile else 54, t['ink'], 700, letter_spacing=-2))
    for i, s in enumerate(p['zh']):
        b.append(text(42, 249 + i * 39, s, 28 if mobile else 26, t['muted'], font=HAN))
    b.append(text(42, h - 21, p['tags'], 18 if mobile else 16, t['muted'], font=MONO))
    b.append(f'<rect x="{sx - 9}" y="{sy - 14}" width="{sw + 18}" height="{sh + 25}" rx="15" fill="{t["panel"]}" stroke="{t["line"]}"/>')
    b.append(f'<image href="{image_path}" x="{sx}" y="{sy}" width="{sw}" height="{sh}" preserveAspectRatio="xMidYMin slice" clip-path="url(#screen)"/>')
    return document(w, h, t, 'Selected work ' + ' '.join(p['title']) + ' — actual live page screenshot captured 2026-11-04', ''.join(b), defs)


def gpu_card(t, mobile=False):
    w, h = (720, 784) if mobile else (1200, 430)
    b = [text(40, 50, '03 / LOCAL INFERENCE', 18 if mobile else 17, t['copper'], font=MONO)]
    for i, s in enumerate(['Old silicon.', 'New limits.']):
        b.append(text(38, 124 + i * 64, s, 56 if mobile else 54, t['ink'], 700, letter_spacing=-2))
    for i, s in enumerate(['在 RTX 2080 Ti 22G 上，', '继续向长上下文推进。']):
        b.append(text(42, 249 + i * 39, s, 28 if mobile else 26, t['muted'], font=HAN))
    ox, oy = (360, 513) if mobile else (910, 209)
    # A deliberately schematic GPU package: stacked planes, pins and a die.
    b.append(f'<ellipse cx="{ox}" cy="{oy + 133}" rx="212" ry="29" fill="{t["shadow"]}" opacity=".5"/>')
    points = [(-200, 0), (0, -98), (200, 0), (0, 98)]
    for offset, fill in [(34, t['line']), (24, t['panel']), (0, t['panel'])]:
        s = ' '.join(f'{ox + x},{oy + y + offset}' for x, y in points)
        b.append(f'<polygon points="{s}" fill="{fill}" stroke="{t["line"]}"/>')
    for i in range(12):
        x, y = -167 + i * 13, 18 + i * 6.5
        b.append(line(ox + x, oy + y, ox + x, oy + y + 25, t['copper'], .65))
        b.append(line(ox - x, oy + y, ox - x, oy + y + 25, t['copper'], .65))
    b.append(f'<polygon points="{ox - 115},{oy} {ox},{oy - 57} {ox + 115},{oy} {ox},{oy + 57}" fill="{t["copper"]}"/>')
    b.append(text(ox, oy + 8, 'TU102 / 22G', 25, t['bg'], 700, MONO, text_anchor='middle'))
    b.append(text(42 if mobile else 620, h - 57, '262K CONTEXT  /  36.6 TOK/S', 23 if mobile else 25, t['ink'], 600, MONO))
    b.append(text(42, h - 21, 'KVMEM / QWEN3.8-27B · 项目记录实测，配置见仓库', 17 if mobile else 16, t['muted'], font=HAN))
    return document(w, h, t, 'RTX 2080 Ti 22G KVMem project. Repository-reported 262K context and 36.6 tokens per second; see repository for exact configuration. GPU drawing is schematic.', ''.join(b))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', default=str(ROOT / 'assets'))
    parser.add_argument('--motion-frames', type=int, default=0)
    parser.add_argument('--theme', choices=list(THEMES), default='dark')
    parser.add_argument('--mobile', action='store_true')
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if args.motion_frames:
        for i in range(args.motion_frames):
            (out / f'{i:03}.svg').write_text(hero(THEMES[args.theme], args.mobile, i / args.motion_frames * math.tau), encoding='utf-8', newline='\n')
        return
    for theme, t in THEMES.items():
        for name, builder in [('hero', hero), ('focus', focus), ('toolkit', toolkit), ('footer', footer)]:
            for mobile in (False, True):
                suffix = '-mobile' if mobile else ''
                (out / f'{name}-{theme}{suffix}.svg').write_text(builder(t, mobile), encoding='utf-8', newline='\n')
        for name, builder in [('terminal', terminal), ('divider', divider)]:
            (out / f'{name}-{theme}.svg').write_text(builder(t), encoding='utf-8', newline='\n')
        source = out / 'readme/source'
        source.mkdir(parents=True, exist_ok=True)
        for p in PROJECTS:
            for mobile in (False, True):
                suffix = '-mobile' if mobile else ''
                (source / f'project-{p["id"]}-{theme}{suffix}.svg').write_text(project_card(t, p, mobile), encoding='utf-8', newline='\n')
        for mobile in (False, True):
            suffix = '-mobile' if mobile else ''
            (out / f'project-gpu-{theme}{suffix}.svg').write_text(gpu_card(t, mobile), encoding='utf-8', newline='\n')
    print('Built original artwork for both themes and mobile layouts.')


if __name__ == '__main__':
    main()

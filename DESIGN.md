# The Builder’s Knot

Visual system for [kael-odin](https://github.com/kael-odin). This is a GitHub profile, not an application landing page: native Markdown carries the biography, links and maintenance notes, while self-hosted assets provide the visual identity.

## Art direction

| Role | Dark | Light |
| --- | --- | --- |
| Ground | `#111315` | `#f5f2ec` |
| Primary ink | `#f3eee6` | `#242423` |
| Supporting ink | `#aaa69f` | `#666761` |
| Copper | `#e8b983` | `#986232` |
| Blue-gray | `#9baec4` | `#536b85` |

The three interwoven arcs represent the profile’s recurring work: local inference, useful agent systems and making tools accessible. The mesh is an original parametric trefoil tube. Surface normals, camera projection and directional/specular lighting are calculated in `scripts/build_assets.py`; no stock 3D image, model API or external GIF host is used.

The name and description remain stationary. Only the sculpture’s viewing angle changes slowly, returning continuously to its starting phase. Mobile uses a separate taller static composition, not a shrunken desktop banner. Reduced-motion visitors receive SVG instead of GIF.

Typography uses system sans-serif, CJK sans-serif and monospace. There are no remote webfont dependencies. Published project boards are PNGs so their exact typography and screenshot composition do not depend on a visitor’s fonts.

## Reference, not a copied template

The user asked to study [Vincentwei1021/video-shotcraft](https://github.com/Vincentwei1021/video-shotcraft). The useful ideas here were its single-subject spotlight, depth hierarchy, stable foreground typography, and real-page evidence. This project does not reuse its logo, stock cards, brand assets or implementation code. The geometry and SVG composition are original to this repository.

## Actual project imagery

Captured on **2026-11-04**, at **1440 × 860** CSS pixels:

- `assets/readme/captures/research.png`: <https://kael-odin.github.io/awesome-academic-research-skills/>
- `assets/readme/captures/plugins.png`: <https://kael-odin.github.io/codex-plugins-zh/>
- `assets/readme/captures/bifrost.png`: <https://kael-odin.github.io/odin-bifrost/>

These are dated screenshots, not live claims about repository counts. The GPU drawing is explicitly schematic; its performance figures are attributed to the linked inference repository and are not cross-hardware promises.

The 18 vendor icon paths in `assets/readme/source/brand-icons.json` come from [Simple Icons](https://simpleicons.org/), distributed under [CC0](https://github.com/simple-icons/simple-icons/blob/develop/LICENSE.md). Brand marks remain the property of their respective owners. Icon colors are lifted/darkened when needed to reach a 3:1 contrast ratio against the panel.

## Rebuild

The static artwork and daily data generator use Python’s standard library. Run from the repository root:

```bash
python scripts/build_assets.py --out assets
```

Fetch current public data, optionally supplying a GitHub token through the environment (never in a file):

```bash
python scripts/generate_stats.py --out assets
```

Restyle an existing public-data snapshot without contacting GitHub:

```bash
python scripts/generate_stats.py --snapshot assets/profile-data.json --out assets
```

The language panel uses bytes from up to 40 of the largest public repositories. It is not a proficiency score. The top six and an explicit Other preserve the denominator. Unavailable metrics render as unavailable, not fabricated zeros. Daily updates generate desktop and mobile panels together.

### Optional raster and motion tools

Requires Node.js 22+; GIF rendering additionally requires `ffmpeg` on PATH. On Linux, install DejaVu Sans and Noto Sans CJK for predictable CJK rasterization; Windows uses Arial, Consolas and Microsoft YaHei.

```bash
npm ci
```

```bash
npm run render:boards
```

```bash
python scripts/build_motion.py
```

`assets/readme/source/project-*.svg` are editable layout sources with relative references to the captured PNGs. The renderer resolves those local images into memory; the README publishes only the final standalone PNGs, never externally-dependent SVG compositions.

Each GIF is 60 frames at a nominal 12 fps, forming a five-second loop. `assets/hero-*.svg` are the matching editable static fallbacks. `.preview-cache/` holds disposable frames and is not committed.

### Preview and tests

```bash
npm run build:preview
```

Serve this directory using the local HTTP preview configuration, then open `_preview.html`. This preview renders **the actual README** with GitHub Markdown CSS, rather than maintaining an unrelated mock layout. Both `_preview.html` and machine-specific launch configuration are ignored by git.

```bash
python -I -B -m unittest discover -s tests -v
```

Check the desktop and mobile breakpoints in both color schemes; verify reduced-motion selects the static hero; inspect GIF phase samples and loop continuity; verify all local assets resolve and the page has no horizontal overflow.

## Automation preserved

- `stats.yml`: daily public data snapshot plus eight desktop/mobile metric and language assets.
- `snake.yml`: genuine contribution-calendar animation in warm copper colors, published to the existing `output` branch.
- `3d-contrib.yml`: original isometric graph, intentionally retained inside a disclosure rather than recoloring unverified generated data.
- `blog-posts.yml`: the original `BLOG-POST-LIST` markers and RSS source remain intact.

There is no third-party visitor counter, typing widget or badge dependency in the main identity and project panels.

#!/usr/bin/env python3
"""Optional GitHub-safe GIF derivative; every frame is the same source scene.

Requires Node + @resvg/resvg-js and ffmpeg. No browser or network is used.
python scripts/build_motion.py [--frames 60] [--fps 12]
"""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--frames', type=int, default=60)
    parser.add_argument('--fps', type=int, default=12)
    args = parser.parse_args()
    for theme in ('dark', 'light'):
        directory = ROOT / '.preview-cache' / ('motion-' + theme)
        directory.mkdir(parents=True, exist_ok=True)
        # Each invocation owns this fixed cache directory. Remove obsolete frames
        # so changing --frames cannot accidentally append an old sequence.
        for old in directory.glob('*.svg'):
            old.unlink()
        for old in directory.glob('*.png'):
            old.unlink()
        subprocess.run([sys.executable, '-I', str(ROOT / 'scripts/build_assets.py'), '--out', str(directory), '--motion-frames', str(args.frames), '--theme', theme], check=True)
        subprocess.run(['node', str(ROOT / 'scripts/render_readme.cjs'), '--frames', str(directory), str(directory), '1000'], check=True)
        output = ROOT / 'assets/readme' / ('hero-' + theme + '.gif')
        subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-framerate', str(args.fps), '-i', str(directory / '%03d.png'), '-filter_complex', '[0:v]split[a][b];[a]palettegen=max_colors=256:stats_mode=diff[p];[b][p]paletteuse=dither=sierra2_4a:diff_mode=rectangle', '-loop', '0', str(output)], check=True)
        print(f'{output.name}: {output.stat().st_size / 1024 / 1024:.2f} MiB')


if __name__ == '__main__':
    main()

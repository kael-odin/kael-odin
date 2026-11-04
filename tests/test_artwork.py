"""Offline acceptance tests for the profile's vector artwork and mobile panels."""
import importlib.util
import math
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SVG = '{http://www.w3.org/2000/svg}'


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


art = load('profile_art', 'build_assets.py')
stats = load('profile_stats_mobile', 'generate_stats.py')


class ArtworkTests(unittest.TestCase):
    def test_published_vectors_are_self_contained_and_accessible(self):
        for path in (ROOT / 'assets').glob('*.svg'):
            with self.subTest(file=path.name):
                source = path.read_text(encoding='utf-8')
                root = ET.fromstring(source)
                self.assertIsNotNone(root.find(SVG + 'title'))
                self.assertIsNotNone(root.find(SVG + 'desc'))
                self.assertNotIn('foreignObject', source)
                self.assertNotIn('<script', source)
                self.assertNotIn('<image', source)
                self.assertNotIn('https://', source)

    def test_every_mobile_composition_has_a_real_mobile_viewbox(self):
        for theme, colors in art.THEMES.items():
            for builder in (art.hero, art.focus, art.toolkit, art.footer, art.gpu_card):
                root = ET.fromstring(builder(colors, True))
                self.assertEqual(root.get('viewBox').split()[2], '720')
                self.assertGreater(float(root.get('height')), 300)

    def test_sculpture_geometry_is_finite_and_periodic(self):
        a = ET.fromstring('<svg>' + art.sculpture(0, 0, 1, 0) + '</svg>')
        b = ET.fromstring('<svg>' + art.sculpture(0, 0, 1, math.tau) + '</svg>')
        self.assertEqual(len(a), 128 * 16)
        self.assertEqual([p.get('points') for p in a], [p.get('points') for p in b])
        for polygon in a:
            for coord in polygon.get('points').replace(',', ' ').split():
                self.assertTrue(math.isfinite(float(coord)))

    def test_missing_mobile_metrics_remain_unavailable(self):
        root = ET.fromstring(stats.render_stats_mobile({}, stats.THEMES['dark']))
        values = [el.text for el in root.iter(SVG + 'text') if el.get('font-size') == '62']
        self.assertEqual(values, ['—'] * 6)

    def test_mobile_language_widths_preserve_exact_denominator(self):
        data = {'languages': {f'Language {i}': i * 11 for i in range(1, 10)}}
        root = ET.fromstring(stats.render_langs_mobile(data, stats.THEMES['dark']))
        bars = [el for el in root.iter(SVG + 'rect') if el.get('data-bytes')]
        self.assertEqual(sum(int(el.get('data-bytes')) for el in bars), 495)
        for bar in bars:
            self.assertAlmostEqual(float(bar.get('width')), 640 * int(bar.get('data-bytes')) / 495, places=5)

    def test_mobile_empty_and_escaped_language_names(self):
        for colors in stats.THEMES.values():
            for languages in (None, {}, {'C<&': 40}):
                root = ET.fromstring(stats.render_langs_mobile({'languages': languages}, colors))
                self.assertEqual(root.get('width'), '720')


if __name__ == '__main__':
    unittest.main()

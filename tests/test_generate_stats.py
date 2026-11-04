"""Offline stdlib tests; render into memory and never fetch or write profile assets."""

import contextlib
import importlib.util
import io
import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "generate_stats.py"
SPEC = importlib.util.spec_from_file_location("generate_stats", SCRIPT)
stats = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(stats)
SVG = "{http://www.w3.org/2000/svg}"


class LanguageTests(unittest.TestCase):
    def setUp(self):
        self.languages = {
            "Python": 400, "JavaScript": 200, "TypeScript": 100,
            "HTML": 80, "CSS": 60, "Shell": 40,
            "Rust": 30, "Go": 20, "Makefile": 10,
        }

    def test_top_six_and_other_preserve_all_sampled_bytes(self):
        rows = stats.language_rows(self.languages)
        self.assertEqual(len(rows), 7)
        self.assertEqual(rows[-2], ("Shell", 40))
        self.assertEqual(rows[-1], ("Other", 60))
        total = sum(self.languages.values())
        self.assertEqual(sum(size for _, size in rows), total)
        self.assertAlmostEqual(sum(size / total for _, size in rows), 1)
        self.assertEqual(stats.percentage(40, total), "4.3%")
        self.assertEqual(stats.percentage(60, total), "6.4%")

    def test_stack_geometry_does_not_assign_tail_to_sixth_language(self):
        root = ET.fromstring(stats.render_langs({"languages": self.languages}, stats.THEMES["dark"]))
        segments = root.findall(f"{SVG}rect[@class='language-segment']")
        total = sum(self.languages.values())
        self.assertEqual([int(segment.get("data-bytes")) for segment in segments],
                         [400, 200, 100, 80, 60, 40, 60])
        self.assertAlmostEqual(sum(float(segment.get("width")) for segment in segments), 1120, places=5)
        cursor = 40
        for segment in segments:
            size = int(segment.get("data-bytes"))
            self.assertAlmostEqual(float(segment.get("width")), 1120 * size / total, places=5)
            self.assertAlmostEqual(float(segment.get("x")), cursor, places=5)
            cursor += 1120 * size / total
        self.assertAlmostEqual(cursor, 1160)
        labels = root.findall(f".//{SVG}text[@class='share']")
        self.assertEqual([label.text for label in labels],
                         [stats.percentage(size, total) for _, size in stats.language_rows(self.languages)])

    def test_other_only_when_needed_and_not_duplicated(self):
        self.assertEqual(stats.language_rows({"Python": 3, "Shell": 1}),
                         [("Python", 3), ("Shell", 1)])
        self.assertEqual(stats.language_rows({"Python": 3, "Other": 2}),
                         [("Python", 3), ("Other", 2)])
        rows = stats.language_rows(dict(self.languages, Other=5))
        self.assertEqual(rows[-1], ("Other", 65))
        self.assertEqual(sum(name == "Other" for name, _ in rows), 1)

    def test_zero_bytes_and_invalid_values_do_not_change_denominator(self):
        self.assertEqual(stats.language_rows({"Python": 5, "Empty": 0, "Bad": -8,
                                             "Missing": None, "Boolean": True}), [("Python", 5)])
        self.assertEqual(stats.percentage(1, 10000), "<0.1%")
        tied = {"Rust": 1, "Go": 1, "Python": 1}
        self.assertEqual(stats.language_rows(tied), [("Go", 1), ("Python", 1), ("Rust", 1)])

    def test_empty_and_unavailable_samples_are_distinct(self):
        for languages, expected in ((None, "Language data unavailable"),
                                    ({}, "No language bytes measured"),
                                    ({"Python": 0}, "No language bytes measured")):
            with self.subTest(languages=languages):
                root = ET.fromstring(stats.render_langs({"languages": languages}, stats.THEMES["light"]))
                self.assertEqual(root.find(f"{SVG}text[@class='empty']").text, expected)
                self.assertFalse(root.findall(f"{SVG}rect[@class='language-segment']"))
                self.assertIn("not skill levels", " ".join(root.itertext()))


class MeasurementTests(unittest.TestCase):
    def test_missing_values_never_become_zero(self):
        root = ET.fromstring(stats.render_stats({}, stats.THEMES["dark"]))
        values = [node.text for node in root.iter(f"{SVG}text")
                  if "value" in node.get("class", "").split()]
        self.assertEqual(values, ["—"] * 6)
        self.assertEqual(stats.fmt(0), "0")
        self.assertEqual(stats.fmt(None), "—")
        self.assertEqual(stats.fmt(True), "—")
        self.assertIn("unavailable, not zero", root.find(f"{SVG}desc").text)

    def test_failed_collection_does_not_invent_api_numbers(self):
        with patch.object(stats, "api_optional", return_value=None), \
             patch.object(stats, "fetch_repos", return_value=None), \
             patch.object(stats, "fetch_languages", return_value=None), \
             patch.object(stats, "fetch_contributions", return_value=None), \
             contextlib.redirect_stdout(io.StringIO()):
            data = stats.collect("offline-user", None)
        for key, _ in stats.METRICS:
            self.assertIsNone(data[key], key)
        self.assertIsNone(data["languages"])
        self.assertFalse(stats.has_measurements(data))

    def test_incomplete_star_counts_and_search_results_are_unavailable(self):
        responses = [{"public_repos": 2}, {"total_count": 99, "incomplete_results": True}, {}]
        with patch.object(stats, "api_optional", side_effect=responses), \
             patch.object(stats, "fetch_repos", return_value=[{"stargazers_count": 3}, {}]), \
             patch.object(stats, "fetch_languages", return_value=None), \
             patch.object(stats, "fetch_contributions", return_value=None), \
             contextlib.redirect_stdout(io.StringIO()):
            data = stats.collect("offline-user", None)
        self.assertEqual(data["repos"], 2)
        for key in ("stars", "followers", "prs", "issues"):
            self.assertIsNone(data[key])

    def test_empty_successful_repository_response_is_a_real_zero(self):
        with patch.object(stats, "api_optional", return_value={"total_count": 0}), \
             patch.object(stats, "fetch_repos", return_value=[]), \
             patch.object(stats, "fetch_contributions", return_value=None), \
             contextlib.redirect_stdout(io.StringIO()):
            data = stats.collect("offline-user", None)
        self.assertEqual(data["stars"], 0)
        self.assertEqual(data["repos"], 0)
        self.assertEqual(data["prs"], 0)
        self.assertIsNone(data["followers"])
        self.assertEqual(data["languages"], {})

    def test_failed_repository_page_is_not_a_partial_total(self):
        with patch.object(stats, "api_optional", side_effect=[[{"stargazers_count": 1}] * 100, None]) as api:
            self.assertIsNone(stats.fetch_repos("offline-user", None))
        self.assertEqual(api.call_count, 2)

    def test_failed_language_samples_are_not_filled_with_zero(self):
        repos = [{"full_name": "sample/first", "size": 100},
                 {"full_name": "sample/second", "size": 20}]
        with patch.object(stats, "api_optional", side_effect=[None, {"Python": 5}]):
            self.assertEqual(stats.fetch_languages(repos, None), {"Python": 5})
        with patch.object(stats, "api_optional", return_value=None):
            self.assertIsNone(stats.fetch_languages(repos, None))
        self.assertEqual(stats.fetch_languages([], None), {})


class RendererAndCliTests(unittest.TestCase):
    def test_xml_accessibility_and_geometry_in_both_themes(self):
        data = {"generated": '2026-11-04 <time> & "quotes"\x01',
                "languages": {'C<&"\'\x00': 12, "Shell": 3}}
        for theme in stats.THEMES.values():
            for renderer, expected in ((stats.render_stats, "0 0 1200 280"),
                                       (stats.render_langs, "0 0 1200 328")):
                with self.subTest(theme=theme["bg"], renderer=renderer.__name__):
                    svg = renderer(data, theme)
                    root = ET.fromstring(svg)
                    self.assertEqual(root.get("viewBox"), expected)
                    self.assertEqual(root.get("role"), "img")
                    ids = {node.get("id") for node in root if node.tag in (SVG + "title", SVG + "desc")}
                    self.assertEqual(set(root.get("aria-labelledby").split()), ids)
                    self.assertTrue(root.find(f"{SVG}title").text)
                    self.assertTrue(root.find(f"{SVG}desc").text)
                    self.assertNotIn("animation:", svg)
                    self.assertNotIn("<animate", svg)
                    self.assertIn("font-size: 68px", svg)
                    self.assertIn("font-size: 64px", svg)
                    self.assertIn(theme["bg"], svg)

    def test_offline_cli_never_fetches_or_rewrites_snapshot(self):
        snapshot = {"stars": 12, "followers": None, "languages": {"Python": 3}}
        with patch.object(stats, "collect", side_effect=AssertionError("network forbidden")) as collect, \
             patch.object(stats.Path, "read_text", return_value=json.dumps(snapshot)), \
             patch.object(stats.Path, "mkdir"), \
             patch.object(stats.Path, "write_text", autospec=True) as write, \
             contextlib.redirect_stdout(io.StringIO()):
            stats.main(["--snapshot", "offline.json", "--out", "unused-output"])
        collect.assert_not_called()
        self.assertEqual({call.args[0].name for call in write.call_args_list},
                         {"stats-dark.svg", "stats-light.svg", "langs-dark.svg", "langs-light.svg",
                          "stats-dark-mobile.svg", "stats-light-mobile.svg", "langs-dark-mobile.svg", "langs-light-mobile.svg"})
        for call in write.call_args_list:
            ET.fromstring(call.args[1])

    def test_successful_collection_saves_reusable_json(self):
        data = {"stars": 0, "repos": 0, "followers": None, "languages": {}, "generated": "now"}
        with patch.object(stats, "collect", return_value=data), \
             patch.object(stats.Path, "mkdir"), \
             patch.object(stats.Path, "write_text", autospec=True) as write, \
             contextlib.redirect_stdout(io.StringIO()):
            stats.main(["--user", "offline-user", "--out", "unused-output"])
        files = {call.args[0].name: call.args[1] for call in write.call_args_list}
        self.assertEqual(len(files), 9)
        self.assertEqual(json.loads(files["profile-data.json"]), data)

    def test_failed_collection_preserves_existing_outputs(self):
        with patch.object(stats, "collect", return_value={"languages": None}), \
             patch.object(stats.Path, "mkdir") as mkdir, \
             patch.object(stats.Path, "write_text") as write:
            with self.assertRaisesRegex(SystemExit, "left unchanged"):
                stats.main(["--out", "unused-output"])
        mkdir.assert_not_called()
        write.assert_not_called()

    def test_snapshot_validation_accepts_missing_data_but_not_fake_counts(self):
        cases = (({}, True), ({"stars": None, "languages": None}, True),
                 ([], False), ({"stars": "0"}, False), ({"stars": True}, False),
                 ({"languages": {"Python": -2}}, False),
                 ({"languages": {"Python": 1.5}}, False), ({"generated": 123}, False))
        for data, valid in cases:
            with self.subTest(data=data), patch.object(stats.Path, "read_text", return_value=json.dumps(data)):
                if valid:
                    self.assertEqual(stats.load_snapshot(Path("offline.json")), data)
                else:
                    with self.assertRaises(ValueError):
                        stats.load_snapshot(Path("offline.json"))


if __name__ == "__main__":
    unittest.main()

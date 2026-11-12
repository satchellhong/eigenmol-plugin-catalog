"""Tests for tools/catalog.py. Standard library only: `python3 -m unittest`.

The fixtures under tests/fixtures/ are test data. They name example.org
addresses that serve nothing and are never part of the catalog.
"""

import hashlib
import io
import json
import sys
import unittest
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tools"))

import catalog  # noqa: E402


def fixture(name: str) -> dict:
    return json.loads((HERE / "fixtures" / name).read_text(encoding="utf-8"))


def package(plugin_id: str, version: str, prefix: str = "x-1.0.0") -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(
            f"{prefix}/plugin.json",
            json.dumps({"id": plugin_id, "version": version, "spec_version": "1.2"}),
        )
        archive.writestr(f"{prefix}/run.sh", "#!/bin/sh\nexit 0\n")
    return buffer.getvalue()


class EntryRules(unittest.TestCase):
    def test_the_valid_fixture_is_valid(self):
        entry = fixture("org.example.fixture.json")
        self.assertEqual(catalog.check_entry(entry, "org.example.fixture.json"), [])

    def test_the_file_name_has_to_be_the_id(self):
        entry = fixture("org.example.fixture.json")
        problems = catalog.check_entry(entry, "something-else.json")
        self.assertTrue(any("org.example.fixture.json" in p for p in problems), problems)

    def test_ids_follow_the_manifest_rule(self):
        for bad in ("NoDots", "org..example", ".org.example", "org.Example", "org.example."):
            self.assertFalse(catalog.id_is_well_formed(bad), bad)
        for good in ("org.example.x", "io.github.someone.my-plugin_2"):
            self.assertTrue(catalog.id_is_well_formed(good), good)

    def test_a_repository_page_is_not_a_package(self):
        for url in (
            "https://github.com/someone/x",
            "https://github.com/someone/x/releases/tag/v1.0.0",
            "https://github.com/someone/x/archive/refs/heads/main.zip",
            "http://example.org/x.zip",
            "https://example.org/x.zip?token=abc",
            "https://example.org/x.tar.gz",
        ):
            self.assertIsNotNone(catalog.package_url_problem(url), url)
        self.assertIsNone(
            catalog.package_url_problem(
                "https://github.com/someone/x/releases/download/v1.0.0/x-1.0.0.zip"
            )
        )
        self.assertIsNone(catalog.package_url_problem("https://downloads.example.org/x-1.0.0.zip"))

    def test_unknown_fields_and_bad_values_are_named(self):
        entry = fixture("org.example.fixture.json")
        entry["rating"] = 5
        entry["category"] = "magic"
        entry["releases"][0]["sha256"] = "ABC"
        entry["releases"][0]["platforms"] = ["mac"]
        entry["releases"].append(dict(entry["releases"][0]))
        problems = catalog.check_entry(entry, "org.example.fixture.json")
        joined = "\n".join(problems)
        for expected in ("rating", "category", "sha256", "platforms", "listed twice"):
            self.assertIn(expected, joined)

    def test_a_plugin_that_sends_data_has_to_say_what(self):
        entry = fixture("org.example.fixture.json")
        entry["network"] = {"setup": False, "runs": True}
        problems = catalog.check_entry(entry, "org.example.fixture.json")
        self.assertTrue(any("network.note" in p for p in problems), problems)

    def test_the_index_is_sorted_and_strips_the_file_markers(self):
        first = fixture("org.example.fixture.json")
        second = dict(first, id="org.example.another")
        text = catalog.build_index([first, second])
        document = json.loads(text)
        self.assertEqual(document["format"], "eigenmol-plugin-catalog")
        self.assertEqual([p["id"] for p in document["plugins"]], ["org.example.another", "org.example.fixture"])
        self.assertNotIn("format", document["plugins"][0])
        self.assertEqual(catalog.build_index([second, first]), text, "the index is deterministic")


class PackageVerification(unittest.TestCase):
    def entry_for(self, body: bytes, version="1.0.0") -> tuple[dict, dict]:
        entry = fixture("org.example.fixture.json")
        release = dict(entry["releases"][0], version=version, sha256=hashlib.sha256(body).hexdigest())
        release.pop("size", None)
        return entry, release

    def test_a_matching_package_passes(self):
        body = package("org.example.fixture", "1.0.0")
        entry, release = self.entry_for(body)
        self.assertEqual(catalog.verify_release(entry, release, fetch=lambda _: body), [])

    def test_another_plugin_with_the_right_checksum_is_still_refused(self):
        body = package("org.example.someone-else", "1.0.0")
        entry, release = self.entry_for(body)
        problems = catalog.verify_release(entry, release, fetch=lambda _: body)
        self.assertTrue(any("someone-else" in p for p in problems), problems)

    def test_other_bytes_and_another_version_are_named(self):
        body = package("org.example.fixture", "2.0.0")
        entry, release = self.entry_for(b"other bytes")
        problems = "\n".join(catalog.verify_release(entry, release, fetch=lambda _: body))
        self.assertIn("SHA-256", problems)
        self.assertIn("version", problems)

    def test_an_escaping_entry_is_refused_without_extracting_it(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("../evil/plugin.json", "{}")
        with self.assertRaises(ValueError):
            catalog.manifest_in(buffer.getvalue())

    def test_a_download_failure_is_a_sentence(self):
        entry, release = self.entry_for(b"x")

        def fail(_url):
            raise OSError("connection refused")

        problems = catalog.verify_release(entry, release, fetch=fail)
        self.assertIn("could not be downloaded", problems[0])


class ChangedReleases(unittest.TestCase):
    """A pull request downloads what it changes, not the whole catalog."""

    def test_a_new_entry_verifies_every_release(self):
        entry = fixture("org.example.fixture.json")
        self.assertEqual(catalog.changed_releases(entry, None), entry["releases"])

    def test_an_unchanged_release_is_not_downloaded_again(self):
        before = fixture("org.example.fixture.json")
        after = json.loads(json.dumps(before))
        after["summary"] = "Reworded summary."
        after["releases"][0]["published"] = "2026-11-12"
        self.assertEqual(catalog.changed_releases(after, before), [])

    def test_a_new_version_is_the_only_one_verified(self):
        before = fixture("org.example.fixture.json")
        after = json.loads(json.dumps(before))
        new = dict(after["releases"][0], version="1.1.0", url="https://example.org/fixture-1.1.0.zip")
        after["releases"].insert(0, new)
        self.assertEqual([r["version"] for r in catalog.changed_releases(after, before)], ["1.1.0"])

    def test_a_changed_checksum_or_address_is_verified_again(self):
        before = fixture("org.example.fixture.json")
        for field, value in (("sha256", "1" * 64), ("url", "https://example.org/other.zip")):
            after = json.loads(json.dumps(before))
            after["releases"][0][field] = value
            self.assertEqual(len(catalog.changed_releases(after, before)), 1, field)


class Scale(unittest.TestCase):
    """Hundreds of listings: generated test data, never part of the catalog."""

    COUNT = 600

    def entries(self) -> list[dict]:
        base = fixture("org.example.fixture.json")
        out = []
        for index in range(self.COUNT):
            entry = json.loads(json.dumps(base))
            entry["id"] = f"org.example.scale.plugin{index:04d}"
            entry["name"] = f"Scale fixture {index:04d}"
            entry["category"] = sorted(catalog.CATEGORIES)[index % len(catalog.CATEGORIES)]
            entry["releases"] = [
                dict(base["releases"][0], version=f"1.{minor}.0", url=f"https://example.org/s{index}-{minor}.zip")
                for minor in range(3, 0, -1)
            ]
            out.append(entry)
        return out

    def test_six_hundred_entries_validate_and_build_quickly(self):
        import time

        entries = self.entries()
        started = time.perf_counter()
        for entry in entries:
            self.assertEqual(catalog.check_entry(entry, f"{entry['id']}.json"), [])
        text = catalog.build_index(entries)
        elapsed = time.perf_counter() - started
        document = json.loads(text)
        self.assertEqual(len(document["plugins"]), self.COUNT)
        # One static document, read in one GET; small enough to keep.
        self.assertLess(len(text.encode("utf-8")), 2 * 1024 * 1024, len(text))
        self.assertLess(elapsed, 5.0, elapsed)

    def test_a_change_to_one_entry_verifies_one_package(self):
        entries = self.entries()
        before = {entry["id"]: entry for entry in entries}
        changed = json.loads(json.dumps(entries[17]))
        changed["releases"].insert(
            0, dict(changed["releases"][0], version="1.4.0", url="https://example.org/new.zip")
        )
        fetched = []
        for entry in entries[:17] + [changed] + entries[18:]:
            for release in catalog.changed_releases(entry, before[entry["id"]]):
                fetched.append(release["url"])
        self.assertEqual(fetched, ["https://example.org/new.zip"])


if __name__ == "__main__":
    unittest.main()

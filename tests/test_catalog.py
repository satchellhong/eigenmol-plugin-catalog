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


class Availability(unittest.TestCase):
    """The weekly report: newest releases only, capped, HEAD with a ranged-GET
    fallback, and never a download."""

    class Response:
        def __init__(self, status):
            self.status = status
            self.read_sizes = []

        def read(self, size=-1):
            self.read_sizes.append(size)
            return b"x"[: max(size, 0)]

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

    def opener(self, answers):
        """A fake `urlopen` answering each method with a status; records calls."""
        import urllib.error

        calls = []

        def open_(request, timeout):
            calls.append((request.get_method(), dict(request.header_items()), timeout))
            status = answers[request.get_method()]
            if status >= 400:
                raise urllib.error.HTTPError(request.full_url, status, "x", {}, None)
            response = Availability.Response(status)
            calls.append(response)
            return response

        return open_, calls

    def test_a_head_answer_is_one_request(self):
        opener, calls = self.opener({"HEAD": 200})
        self.assertEqual(catalog.head_status("https://example.org/a.zip", opener), (200, "HEAD"))
        self.assertEqual([c[0] for c in calls if isinstance(c, tuple)], ["HEAD"])
        self.assertEqual(calls[0][2], catalog.AVAILABILITY_TIMEOUT)

    def test_a_refused_head_falls_back_to_one_byte(self):
        for refused in (403, 405, 501):
            opener, calls = self.opener({"HEAD": refused, "GET": 206})
            self.assertEqual(
                catalog.head_status("https://example.org/a.zip", opener), (206, "GET bytes=0-0")
            )
            get = [c for c in calls if isinstance(c, tuple)][1]
            self.assertEqual(get[1].get("Range"), "bytes=0-0", refused)
            response = [c for c in calls if isinstance(c, Availability.Response)][-1]
            self.assertEqual(response.read_sizes, [1], "at most one byte is read")

    def test_a_missing_file_is_not_retried_as_a_get(self):
        opener, calls = self.opener({"HEAD": 404, "GET": 200})
        self.assertEqual(catalog.head_status("https://example.org/a.zip", opener), (404, "HEAD"))
        self.assertEqual([c[0] for c in calls if isinstance(c, tuple)], ["HEAD"])

    def test_only_the_newest_release_by_default_and_a_cap(self):
        entries = Scale().entries()
        pairs, left = catalog.availability_targets(entries)
        self.assertEqual(len(pairs), catalog.AVAILABILITY_LIMIT)
        self.assertEqual(left, len(entries) - catalog.AVAILABILITY_LIMIT)
        self.assertTrue(all(release is entry["releases"][0] for entry, release in pairs))
        every, _ = catalog.availability_targets(entries, every_release=True, limit=10_000)
        self.assertEqual(len(every), 3 * len(entries))

    def test_failures_are_sentences_and_the_budget_stops_asking(self):
        entry = fixture("org.example.fixture.json")
        answers = iter([(200, "HEAD"), (404, "HEAD")])
        failures, unasked = catalog.check_availability(
            [(entry, entry["releases"][0])] * 2, status=lambda url: next(answers)
        )
        self.assertEqual(unasked, 0)
        self.assertEqual(len(failures), 1)
        self.assertIn("HTTP 404 (HEAD)", failures[0])

        def broken(url):
            raise TimeoutError("timed out")

        failures, _ = catalog.check_availability([(entry, entry["releases"][0])], status=broken)
        self.assertIn("no answer (timed out)", failures[0])
        ticks = iter([0, 0, 1000, 1000])
        failures, unasked = catalog.check_availability(
            [(entry, entry["releases"][0])] * 3,
            status=lambda url: (200, "HEAD"),
            budget=10,
            clock=lambda: next(ticks),
        )
        self.assertEqual((failures, unasked), ([], 2))


class ChangedFiles(unittest.TestCase):
    """What `verify --changed` reads from git, on a real repository."""

    def git(self, *args):
        import subprocess

        subprocess.run(["git", *args], cwd=self.root, check=True, capture_output=True)

    def write(self, plugin_id, entry):
        (self.root / "plugins" / f"{plugin_id}.json").write_text(json.dumps(entry), encoding="utf-8")

    def setUp(self):
        import tempfile

        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "plugins").mkdir()
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "test@example.org")
        self.git("config", "user.name", "test")
        base = fixture("org.example.fixture.json")
        for name in ("org.example.a", "org.example.b", "org.example.c"):
            self.write(name, dict(base, id=name))
        self.git("add", ".")
        self.git("commit", "-q", "-m", "base")
        self.git("checkout", "-q", "-b", "change")

    def tearDown(self):
        self.temp.cleanup()

    def commit(self):
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "change")

    def test_a_deleted_entry_names_nothing_to_download(self):
        (self.root / "plugins" / "org.example.b.json").unlink()
        self.commit()
        self.assertEqual(catalog.changed_ids("main", self.root), [])

    def test_a_deleted_release_downloads_nothing(self):
        entry = fixture("org.example.fixture.json")
        before = dict(entry, id="org.example.a")
        before["releases"] = [
            dict(entry["releases"][0], version="1.1.0", url="https://example.org/a-1.1.0.zip"),
            entry["releases"][0],
        ]
        self.write("org.example.a", before)
        self.commit()
        self.git("checkout", "-q", "-b", "drop")
        after = dict(before, releases=before["releases"][1:])
        self.write("org.example.a", after)
        self.commit()
        self.assertEqual(catalog.changed_ids("change", self.root), ["org.example.a"])
        self.assertEqual(
            catalog.changed_releases(after, catalog.entry_at("change", "org.example.a", self.root)), []
        )

    def test_a_changed_id_is_a_new_entry_and_verifies_everything(self):
        self.git("mv", "plugins/org.example.c.json", "plugins/org.example.renamed.json")
        entry = json.loads((self.root / "plugins" / "org.example.renamed.json").read_text())
        entry["id"] = "org.example.renamed"
        self.write("org.example.renamed", entry)
        self.commit()
        self.assertEqual(catalog.changed_ids("main", self.root), ["org.example.renamed"])
        before = catalog.entry_at("main", "org.example.renamed", self.root)
        self.assertIsNone(before)
        self.assertEqual(catalog.changed_releases(entry, before), entry["releases"])

    def test_a_metadata_edit_names_the_entry_and_downloads_nothing(self):
        entry = json.loads((self.root / "plugins" / "org.example.a.json").read_text())
        entry["summary"] = "Reworded."
        self.write("org.example.a", entry)
        self.commit()
        self.assertEqual(catalog.changed_ids("main", self.root), ["org.example.a"])
        before = catalog.entry_at("main", "org.example.a", self.root)
        self.assertEqual(catalog.changed_releases(entry, before), [])

    def test_one_change_among_many_is_the_only_one_named(self):
        entry = json.loads((self.root / "plugins" / "org.example.b.json").read_text())
        entry["releases"][0]["sha256"] = "2" * 64
        self.write("org.example.b", entry)
        self.commit()
        self.assertEqual(catalog.changed_ids("main", self.root), ["org.example.b"])
        before = catalog.entry_at("main", "org.example.b", self.root)
        self.assertEqual(len(catalog.changed_releases(entry, before)), 1)

    def test_a_bad_address_is_refused_before_anything_is_downloaded(self):
        entry = json.loads((self.root / "plugins" / "org.example.a.json").read_text())
        entry["releases"][0]["url"] = "https://github.com/someone/x/archive/refs/heads/main.zip"
        problems = catalog.check_entry(entry, "org.example.a.json")
        self.assertTrue(any("url" in p or "package" in p for p in problems), problems)


if __name__ == "__main__":
    unittest.main()

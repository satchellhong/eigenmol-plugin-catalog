#!/usr/bin/env python3
"""Validate, build and verify the EigenMol plugin catalog.

    python3 tools/catalog.py validate          check every file in plugins/
    python3 tools/catalog.py build             write index.json from plugins/
    python3 tools/catalog.py build --check     fail if index.json is out of date
    python3 tools/catalog.py verify [ID ...]   download listed packages and
                                               compare them with their entries
    python3 tools/catalog.py verify --changed REF
                                               download only the releases a
                                               change adds or edits against REF
    python3 tools/catalog.py availability [--all] [--limit N]
                                               ask each plugin's newest package
                                               address whether it still answers
                                               (HEAD, or a 1-byte ranged GET where
                                               HEAD is refused; nothing else is
                                               downloaded or checked)

Standard library only, so it runs the same on a contributor's laptop and in
CI without installing anything.

`verify` downloads a package and reads it as a ZIP. It never extracts a file
to disk and never runs anything from it: it reads `plugin.json` out of the
archive, compares the plugin id and version with the entry, and compares the
SHA-256 of the bytes with the one the entry lists.

The rules here are the rules EigenMol applies when it reads the catalog
(`rust/src/plugin/catalog.rs` in EigenMol). An entry this script accepts is an
entry EigenMol lists; one it refuses, EigenMol would skip with a reason.
"""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import io
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGINS = ROOT / "plugins"
INDEX = ROOT / "index.json"

CATALOG_FORMAT = "eigenmol-plugin-catalog"
ENTRY_FORMAT = "eigenmol-plugin-catalog-entry"
SCHEMA_VERSION = 1
CATALOG_NAME = "EigenMol plugin catalog"
CATALOG_HOMEPAGE = "https://github.com/satchellhong/eigenmol-plugin-catalog"

CATEGORIES = {
    "docking",
    "energy",
    "structure-prediction",
    "analysis",
    "preparation",
    "utility",
    "example",
}
STATUSES = {"active", "deprecated"}
PLATFORM = re.compile(r"^(macos|windows|linux)(-(arm64|x86_64))?$")
VERSION = re.compile(r"^\d+\.\d+\.\d+([-+][0-9A-Za-z.\-+]*)?$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
SPEC = re.compile(r"^\d+\.\d+$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MAX_ID_LENGTH = 128
# What `verify` will download: a plugin package is its own code; an engine or
# an environment is built by the plugin's setup.
MAX_PACKAGE_BYTES = 256 * 1024 * 1024
MANIFEST_SEARCH_DEPTH = 3

ENTRY_FIELDS = {
    "format": True,
    "schema_version": True,
    "id": True,
    "name": True,
    "summary": True,
    "description": False,
    "publisher": True,
    "category": True,
    "license": True,
    "homepage": False,
    "source_repository": True,
    "status": False,
    "network": True,
    "releases": True,
}
RELEASE_FIELDS = {
    "version": True,
    "url": True,
    "sha256": True,
    "size": False,
    "platforms": True,
    "plugin_spec": True,
    "published": True,
}


def id_is_well_formed(value: str) -> bool:
    """The manifest's id rule, exactly."""
    if not value or len(value) > MAX_ID_LENGTH or "." not in value:
        return False
    if value.startswith(".") or value.endswith(".") or ".." in value:
        return False
    return all(c.islower() and c.isascii() or c.isdigit() or c in ".-_" for c in value)


def is_https(value: str) -> bool:
    parsed = urllib.parse.urlparse(value)
    return parsed.scheme == "https" and bool(parsed.netloc)


def package_url_problem(url: str) -> str | None:
    """A release must name the package itself, never a repository page."""
    if not is_https(url):
        return "url is not an https:// address"
    parsed = urllib.parse.urlparse(url)
    host = parsed.netloc.lower()
    if host in ("github.com", "www.github.com"):
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) != 6 or parts[2:4] != ["releases", "download"]:
            return (
                "a github.com url has to be a release asset: "
                "https://github.com/OWNER/REPO/releases/download/TAG/FILE.zip"
            )
    if not parsed.path.lower().endswith(".zip"):
        return "url does not name a .zip package"
    if parsed.query or parsed.fragment:
        return "url carries a query or a fragment; list a plain, permanent address"
    return None


def check_entry(entry: object, filename: str | None = None) -> list[str]:
    """Every reason this entry would not be listed. Empty when it is valid."""
    problems: list[str] = []
    if not isinstance(entry, dict):
        return ["the file is not a JSON object"]

    for field, required in ENTRY_FIELDS.items():
        if required and field not in entry:
            problems.append(f"`{field}` is missing")
    for field in entry:
        if field not in ENTRY_FIELDS:
            problems.append(f"`{field}` is not a field of a catalog entry")

    if entry.get("format") not in (None, ENTRY_FORMAT):
        problems.append(f"`format` has to be `{ENTRY_FORMAT}`")
    if "schema_version" in entry and entry.get("schema_version") != SCHEMA_VERSION:
        problems.append(f"`schema_version` has to be {SCHEMA_VERSION}")

    plugin_id = entry.get("id")
    if not isinstance(plugin_id, str) or not id_is_well_formed(plugin_id):
        problems.append(
            "`id` is not a plugin id: lowercase letters, digits, `.`, `-`, `_`, with at "
            "least one dot, as the plugin's manifest writes it"
        )
    elif filename is not None and filename != f"{plugin_id}.json":
        problems.append(f"the file has to be called {plugin_id}.json")

    for field, limit in (("name", 80), ("summary", 200), ("description", 4000)):
        value = entry.get(field)
        if field in entry and (not isinstance(value, str) or not value.strip()):
            problems.append(f"`{field}` has to be non-empty text")
        elif isinstance(value, str) and len(value) > limit:
            problems.append(f"`{field}` is longer than {limit} characters")

    publisher = entry.get("publisher")
    if "publisher" in entry:
        if not isinstance(publisher, dict) or not str(publisher.get("name", "")).strip():
            problems.append("`publisher.name` is missing")
        else:
            extra = set(publisher) - {"name", "url"}
            if extra:
                problems.append(f"`publisher` has unknown fields: {sorted(extra)}")
            if "url" in publisher and not is_https(str(publisher["url"])):
                problems.append("`publisher.url` is not an https:// address")

    if "category" in entry and entry.get("category") not in CATEGORIES:
        problems.append(f"`category` has to be one of {sorted(CATEGORIES)}")
    if "status" in entry and entry.get("status") not in STATUSES:
        problems.append(f"`status` has to be one of {sorted(STATUSES)}")
    if "license" in entry and (
        not isinstance(entry.get("license"), str) or not entry["license"].strip()
    ):
        problems.append("`license` has to name the plugin's licence (an SPDX id, or `proprietary`)")

    for field in ("homepage", "source_repository"):
        if field in entry and not is_https(str(entry.get(field))):
            problems.append(f"`{field}` is not an https:// address")

    network = entry.get("network")
    if "network" in entry:
        if not isinstance(network, dict):
            problems.append("`network` has to be an object")
        else:
            for key in ("setup", "runs"):
                if not isinstance(network.get(key), bool):
                    problems.append(f"`network.{key}` has to be true or false")
            extra = set(network) - {"setup", "runs", "note"}
            if extra:
                problems.append(f"`network` has unknown fields: {sorted(extra)}")
            if network.get("runs") is True and not str(network.get("note", "")).strip():
                problems.append(
                    "`network.note` has to say what a run sends and where, when "
                    "`network.runs` is true"
                )

    releases = entry.get("releases")
    if "releases" in entry:
        if not isinstance(releases, list) or not releases:
            problems.append("`releases` has to list at least one version")
        else:
            seen: set[str] = set()
            for index, release in enumerate(releases):
                label = f"releases[{index}]"
                if not isinstance(release, dict):
                    problems.append(f"{label} is not an object")
                    continue
                version = release.get("version")
                if isinstance(version, str):
                    label = f"version {version}"
                    if version in seen:
                        problems.append(f"{label} is listed twice")
                    seen.add(version)
                problems.extend(f"{label}: {p}" for p in check_release(release))
    return problems


def check_release(release: dict) -> list[str]:
    problems: list[str] = []
    for field, required in RELEASE_FIELDS.items():
        if required and field not in release:
            problems.append(f"`{field}` is missing")
    for field in release:
        if field not in RELEASE_FIELDS:
            problems.append(f"`{field}` is not a field of a release")
    version = release.get("version")
    if "version" in release and (not isinstance(version, str) or not VERSION.match(version)):
        problems.append("`version` is not three numbers (1.2.0), as the manifest writes it")
    url = release.get("url")
    if "url" in release:
        problem = package_url_problem(url) if isinstance(url, str) else "url is not text"
        if problem:
            problems.append(problem)
    sha = release.get("sha256")
    if "sha256" in release and (not isinstance(sha, str) or not SHA256.match(sha)):
        problems.append("`sha256` is not 64 lowercase hexadecimal characters")
    size = release.get("size")
    if "size" in release and (not isinstance(size, int) or size <= 0):
        problems.append("`size` has to be the package's size in bytes")
    platforms = release.get("platforms")
    if "platforms" in release:
        if not isinstance(platforms, list) or not all(
            isinstance(p, str) and PLATFORM.match(p) for p in platforms
        ):
            problems.append(
                "`platforms` has to list names like macos-arm64, windows-x86_64 or linux "
                "(an empty list means any platform)"
            )
    spec = release.get("plugin_spec")
    if "plugin_spec" in release and (not isinstance(spec, str) or not SPEC.match(spec)):
        problems.append("`plugin_spec` is the specification version, e.g. 1.2")
    published = release.get("published")
    if "published" in release and (not isinstance(published, str) or not DATE.match(published)):
        problems.append("`published` is a date, YYYY-MM-DD")
    return problems


def load_entries() -> tuple[list[dict], list[str]]:
    entries: list[dict] = []
    problems: list[str] = []
    ids: dict[str, str] = {}
    for path in sorted(PLUGINS.glob("*.json")):
        try:
            entry = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            problems.append(f"plugins/{path.name}: not readable JSON ({error})")
            continue
        found = check_entry(entry, path.name)
        problems.extend(f"plugins/{path.name}: {p}" for p in found)
        plugin_id = entry.get("id") if isinstance(entry, dict) else None
        if isinstance(plugin_id, str):
            if plugin_id in ids:
                problems.append(
                    f"plugins/{path.name}: the id {plugin_id} is already listed by "
                    f"plugins/{ids[plugin_id]}"
                )
            ids[plugin_id] = path.name
        if not found:
            entries.append(entry)
    for path in sorted(PLUGINS.iterdir()) if PLUGINS.exists() else []:
        if path.name in ("README.md", ".gitkeep") or path.suffix == ".json":
            continue
        problems.append(f"plugins/{path.name}: only one <plugin id>.json per plugin belongs here")
    return entries, problems


def build_index(entries: list[dict]) -> str:
    listed = []
    for entry in sorted(entries, key=lambda item: item["id"]):
        item = {key: value for key, value in entry.items() if key not in ("format", "schema_version")}
        item.setdefault("status", "active")
        listed.append(item)
    document = {
        "format": CATALOG_FORMAT,
        "schema_version": SCHEMA_VERSION,
        "name": CATALOG_NAME,
        "homepage": CATALOG_HOMEPAGE,
        "plugins": listed,
    }
    return json.dumps(document, indent=2, ensure_ascii=False) + "\n"


# ---------------------------------------------------------------------------
# Verifying packages against entries
# ---------------------------------------------------------------------------


def download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "eigenmol-plugin-catalog-verify"})
    with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310 - https only
        announced = response.headers.get("Content-Length")
        if announced and int(announced) > MAX_PACKAGE_BYTES:
            raise ValueError(f"the package is larger than {MAX_PACKAGE_BYTES} bytes")
        body = response.read(MAX_PACKAGE_BYTES + 1)
    if len(body) > MAX_PACKAGE_BYTES:
        raise ValueError(f"the package is larger than {MAX_PACKAGE_BYTES} bytes")
    return body


def manifest_in(archive: bytes) -> dict:
    """The one plugin.json in a package, read without extracting anything."""
    with zipfile.ZipFile(io.BytesIO(archive)) as package:
        candidates = []
        for info in package.infolist():
            name = info.filename
            parts = [part for part in name.split("/") if part]
            if name.startswith("/") or ".." in parts:
                raise ValueError(f"the package has an entry that escapes it: {name}")
            if parts and parts[-1] == "plugin.json" and len(parts) <= MANIFEST_SEARCH_DEPTH:
                candidates.append(info)
        if not candidates:
            raise ValueError("the package holds no plugin.json")
        shallowest = min(len(c.filename.strip("/").split("/")) for c in candidates)
        top = [c for c in candidates if len(c.filename.strip("/").split("/")) == shallowest]
        if len(top) > 1:
            raise ValueError("the package holds several plugins; list one package per plugin")
        if top[0].file_size > 1024 * 1024:
            raise ValueError("plugin.json is larger than 1 MB")
        return json.loads(package.read(top[0]).decode("utf-8"))


def verify_release(entry: dict, release: dict, fetch=download) -> list[str]:
    """Download one release and compare it with the entry. Runs nothing."""
    label = f"{entry['id']} {release['version']}"
    try:
        body = fetch(release["url"])
    except Exception as error:  # noqa: BLE001 - every failure is a sentence
        return [f"{label}: the package could not be downloaded ({error})"]
    problems = []
    digest = hashlib.sha256(body).hexdigest()
    if digest != release["sha256"]:
        problems.append(f"{label}: the package's SHA-256 is {digest}, the entry lists {release['sha256']}")
    if "size" in release and release["size"] != len(body):
        problems.append(f"{label}: the package is {len(body)} bytes, the entry lists {release['size']}")
    try:
        manifest = manifest_in(body)
    except (ValueError, zipfile.BadZipFile, json.JSONDecodeError, UnicodeDecodeError) as error:
        return problems + [f"{label}: {error}"]
    if manifest.get("id") != entry["id"]:
        problems.append(f"{label}: the package is the plugin {manifest.get('id')!r}, not {entry['id']}")
    if manifest.get("version") != release["version"]:
        problems.append(
            f"{label}: the package is version {manifest.get('version')!r}, not {release['version']}"
        )
    declared = manifest.get("platforms") or []
    listed = release.get("platforms") or []
    if declared and listed and not set(listed) <= set(declared) | {p.split("-")[0] for p in declared}:
        problems.append(
            f"{label}: the entry lists platforms {listed}, the manifest declares {declared}"
        )
    spec = str(manifest.get("spec_version", ""))
    if spec and release.get("plugin_spec") and spec != release["plugin_spec"]:
        problems.append(
            f"{label}: the entry lists plugin_spec {release['plugin_spec']}, the manifest declares {spec}"
        )
    return problems


# ---------------------------------------------------------------------------
# What a change touches
# ---------------------------------------------------------------------------

# A release field whose change means the package has to be downloaded again.
PACKAGE_FIELDS = ("version", "url", "sha256", "size", "platforms", "plugin_spec")


def entry_at(ref: str, plugin_id: str, root: Path = ROOT) -> dict | None:
    """The entry as it is at a git ref, or None when it did not exist there."""
    result = subprocess.run(
        ["git", "show", f"{ref}:plugins/{plugin_id}.json"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    try:
        entry = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None
    return entry if isinstance(entry, dict) else None


def changed_releases(entry: dict, before: dict | None) -> list[dict]:
    """The releases of `entry` that are new or whose package fields changed.

    A release that only moved, or whose `published` date or the entry's prose
    changed, names the same bytes and is not downloaded again. A catalog of
    hundreds of plugins is verified at the cost of what a pull request
    changes, not at the cost of everything listed.
    """
    old = {}
    for release in (before or {}).get("releases", []) or []:
        if isinstance(release, dict) and isinstance(release.get("version"), str):
            old[release["version"]] = release
    out = []
    for release in entry["releases"]:
        previous = old.get(release["version"])
        if previous is None or any(previous.get(f) != release.get(f) for f in PACKAGE_FIELDS):
            out.append(release)
    # A changed id is a different entry: everything is new.
    if before is not None and before.get("id") != entry.get("id"):
        return list(entry["releases"])
    return out


def changed_ids(ref: str, root: Path = ROOT) -> list[str]:
    """Plugin ids whose entry files differ from `ref`: added, modified, or the
    new name of a renamed file. A deleted entry names nothing to download."""
    result = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=AMR", f"{ref}...HEAD", "--", "plugins/"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git diff against {ref} failed")
    ids = []
    for line in result.stdout.splitlines():
        name = line.strip().removeprefix("plugins/")
        if name.endswith(".json") and "/" not in name:
            ids.append(name[: -len(".json")])
    return ids


# The answers to a HEAD request that mean "this server does not do HEAD here",
# not "the file is gone". GitHub's release CDN and some object stores answer
# HEAD with 403 or 405; a ranged GET of one byte asks the same question.
HEAD_NOT_SUPPORTED = {403, 405, 501}

# Availability limits: a weekly report, not a crawl. One request per listed
# address (two when HEAD is refused), each with its own timeout, and a cap on
# how many addresses one run asks about.
AVAILABILITY_TIMEOUT = 15
AVAILABILITY_LIMIT = 300


def head_status(url: str, opener=None, timeout: float = AVAILABILITY_TIMEOUT) -> tuple[int, str]:
    """The HTTP status `url` answers with, and how it was asked (`HEAD`, or
    `GET bytes=0-0` when the server refuses HEAD). Redirects are followed.

    Availability only: at most one byte is read, so this says the address
    still answers, not that the bytes still match. Integrity is `verify`'s job.
    """
    opener = opener or urllib.request.urlopen

    def ask(method: str, headers: dict) -> int:
        request = urllib.request.Request(
            url,
            method=method,
            headers={"User-Agent": "eigenmol-plugin-catalog-availability", **headers},
        )
        try:
            with opener(request, timeout=timeout) as response:  # noqa: S310 - https only
                if method == "GET":
                    response.read(1)
                return response.status
        except urllib.error.HTTPError as error:
            return error.code

    status = ask("HEAD", {})
    if status in HEAD_NOT_SUPPORTED:
        return ask("GET", {"Range": "bytes=0-0"}), "GET bytes=0-0"
    return status, "HEAD"


def availability_targets(
    entries: list[dict], every_release: bool = False, limit: int = AVAILABILITY_LIMIT
) -> tuple[list[tuple[dict, dict]], int]:
    """The (entry, release) pairs one availability run asks about, and how
    many it left out because of `limit`.

    By default only each plugin's newest listed release: that is the one the
    application offers first, and older releases were verified when they were
    added. `every_release` asks about all of them.
    """
    pairs = []
    for entry in entries:
        releases = entry["releases"] if every_release else entry["releases"][:1]
        pairs.extend((entry, release) for release in releases)
    return pairs[:limit], max(0, len(pairs) - limit)


AVAILABILITY_BUDGET = 900  # seconds for a whole run


def check_availability(
    pairs: list[tuple[dict, dict]],
    status=head_status,
    budget: float = AVAILABILITY_BUDGET,
    clock=None,
) -> tuple[list[str], int]:
    """One sentence per address that did not answer with a success, and how
    many addresses were not asked because the run's time budget ran out."""
    import time

    clock = clock or time.monotonic
    started = clock()
    failures = []
    for index, (entry, release) in enumerate(pairs):
        if clock() - started > budget:
            return failures, len(pairs) - index
        try:
            code, method = status(release["url"])
        except Exception as error:  # noqa: BLE001 - every failure is a sentence
            failures.append(f"{entry['id']} {release['version']}: no answer ({error})")
            continue
        if code >= 400:
            failures.append(f"{entry['id']} {release['version']}: HTTP {code} ({method})")
    return failures, 0


# ---------------------------------------------------------------------------
# Command line
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("validate", help="check every entry in plugins/")
    build = commands.add_parser("build", help="write index.json from plugins/")
    build.add_argument("--check", action="store_true", help="fail if index.json is out of date")
    verify = commands.add_parser("verify", help="download packages and compare them with their entries")
    verify.add_argument("ids", nargs="*", help="plugin ids to verify; every entry when none")
    verify.add_argument(
        "--changed",
        metavar="REF",
        help="verify only the releases added or edited since REF (a pull request's base)",
    )
    availability = commands.add_parser(
        "availability",
        help="ask each plugin's newest package address whether it answers; downloads nothing",
    )
    availability.add_argument(
        "--all", action="store_true", help="every listed release, not only each plugin's newest"
    )
    availability.add_argument(
        "--limit",
        type=int,
        default=AVAILABILITY_LIMIT,
        help=f"ask about at most this many addresses (default {AVAILABILITY_LIMIT})",
    )
    arguments = parser.parse_args(argv)

    entries, problems = load_entries()
    if problems:
        print("The catalog has problems:")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    if arguments.command == "validate":
        print(f"{len(entries)} entr{'y' if len(entries) == 1 else 'ies'} valid.")
        return 0

    if arguments.command == "build":
        text = build_index(entries)
        if arguments.check:
            current = INDEX.read_text(encoding="utf-8") if INDEX.exists() else ""
            if current != text:
                print("index.json is out of date. Run `python3 tools/catalog.py build` and commit it.")
                return 1
            print("index.json is up to date.")
            return 0
        INDEX.write_text(text, encoding="utf-8")
        print(f"Wrote index.json with {len(entries)} plugin(s).")
        return 0

    if arguments.command == "availability":
        pairs, left_out = availability_targets(entries, arguments.all, arguments.limit)
        failures, unasked = check_availability(pairs)
        if left_out:
            print(f"{left_out} address(es) not asked this run (--limit {arguments.limit}).")
        if unasked:
            print(f"{unasked} address(es) not asked: the {AVAILABILITY_BUDGET} s budget ran out.")
            pairs = pairs[: len(pairs) - unasked]
        if failures:
            print("Addresses that did not answer:")
            for failure in failures:
                print(f"  - {failure}")
            return 1
        print(f"{len(pairs)} address(es) answer. (Availability only; `verify` checks the bytes.)")
        return 0

    if arguments.changed:
        by_id = {entry["id"]: entry for entry in entries}
        try:
            ids = changed_ids(arguments.changed)
        except RuntimeError as error:
            print(error)
            return 1
        failures = []
        checked = 0
        for plugin_id in ids:
            entry = by_id.get(plugin_id)
            if entry is None:
                continue  # removed or renamed away: nothing to download
            for release in changed_releases(entry, entry_at(arguments.changed, plugin_id)):
                checked += 1
                failures.extend(verify_release(entry, release))
        if failures:
            print("Verification failed:")
            for failure in failures:
                print(f"  - {failure}")
            return 1
        print(
            f"{checked} changed package(s) match their entries "
            f"({len(ids)} entr{'y' if len(ids) == 1 else 'ies'} changed)."
        )
        return 0

    wanted = set(arguments.ids)
    unknown = wanted - {entry["id"] for entry in entries}
    if unknown:
        print(f"Not in the catalog: {', '.join(sorted(unknown))}")
        return 1
    failures: list[str] = []
    checked = 0
    for entry in entries:
        if wanted and entry["id"] not in wanted:
            continue
        for release in entry["releases"]:
            checked += 1
            failures.extend(verify_release(entry, release))
    if failures:
        print("Verification failed:")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print(f"{checked} package(s) match their entries.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

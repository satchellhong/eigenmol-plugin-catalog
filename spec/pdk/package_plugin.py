#!/usr/bin/env python3
"""Build the installable ZIP of any EigenMol plugin folder (part of the PDK).

    python3 package_plugin.py PLUGIN_FOLDER [--name NAME] [--out DIR]
    python3 package_plugin.py PLUGIN_FOLDER --check     # validates only

Writes DIR/<name>-<version>.zip and a .sha256 beside it. <name> defaults to the
plugin id. The archive holds the plugin folder's files wrapped in one folder
named `<name>-<version>/` — the layout EigenMol's installer expects of a
release asset (PACKAGING_AND_DISTRIBUTION.md). Everything a setup builds or downloads (env/, bin/, .tools/, .mamba/)
and every cache is left out: a package carries the plugin's own files, and its
setup fetches the engine on the user's machine.

Before writing anything this checks the manifest the way a careful installer
would, so a broken package is caught here rather than on a user's machine:
valid JSON, an id, a version equal to the adapter's PLUGIN_VERSION, a protocol,
every file the manifest names present (except files a declared setup creates),
and no file the package must not carry.

Standard library only.
"""
import argparse
import hashlib
import json
import os
import re
import stat
import sys
import zipfile

# Set from the command line in main(); module-level so the functions below
# read like the repository version of this tool.
PAYLOAD = os.getcwd()
NAME = None
# Built or downloaded by setup, or caches: never in a package.
EXCLUDED_DIRECTORIES = {"env", "bin", ".tools", ".mamba", "__pycache__", ".git", "dist"}
EXCLUDED_FILES = {".DS_Store"}
EXCLUDED_SUFFIXES = (".pyc", ".pyo", ".part")
# A package larger than this is almost certainly carrying an environment.
MAX_PACKAGE_BYTES = 20 * 1024 * 1024


def fail(message):
    print(f"package: {message}", file=sys.stderr)
    sys.exit(1)


def payload_files():
    files = []
    for directory, subdirectories, names in os.walk(PAYLOAD):
        subdirectories[:] = sorted(d for d in subdirectories if d not in EXCLUDED_DIRECTORIES)
        for name in sorted(names):
            if name in EXCLUDED_FILES or name.endswith(EXCLUDED_SUFFIXES):
                continue
            path = os.path.join(directory, name)
            if os.path.islink(path):
                fail(f"{os.path.relpath(path, PAYLOAD)} is a symbolic link; a package carries files")
            files.append(os.path.relpath(path, PAYLOAD))
    return files


def adapter_version(manifest):
    """PLUGIN_VERSION from the adapter the manifest runs, when it states one."""
    candidates = [manifest.get("entrypoint", "")] + list(manifest.get("args", []))
    for candidate in candidates:
        path = os.path.join(PAYLOAD, candidate)
        if candidate.endswith(".py") and os.path.isfile(path):
            match = re.search(r'^PLUGIN_VERSION\s*=\s*"([^"]+)"', open(path).read(), re.M)
            if match:
                return candidate, match.group(1)
    return None, None


def validate():
    path = os.path.join(PAYLOAD, "plugin.json")
    if not os.path.isfile(path):
        fail(f"{PAYLOAD} has no plugin.json")
    try:
        manifest = json.load(open(path))
    except ValueError as error:
        fail(f"plugin.json is not valid JSON: {error}")
    for field in ("id", "name", "version", "protocol", "runtime", "entrypoint", "actions"):
        if field not in manifest:
            fail(f"plugin.json has no `{field}`")
    if not re.fullmatch(r"[a-z0-9]+(\.[a-z0-9_-]+)+", manifest["id"]):
        fail(f"`{manifest['id']}` is not a reverse-domain plugin id")
    script, version = adapter_version(manifest)
    if version is not None and version != manifest["version"]:
        fail(f"plugin.json says version {manifest['version']} but {script} says PLUGIN_VERSION {version}")
    created_by_setup = {r.get("path") for r in manifest.get("requirements", []) if r.get("path")}
    has_setup = bool(manifest.get("setup"))
    named = [manifest["entrypoint"]] + [a for a in manifest.get("args", []) if not a.startswith("-")]
    for block in ("setup", "check"):
        for argv in (manifest.get(block) or {}).get("commands", {}).values():
            named += [a for a in argv[1:] if not a.startswith("-")]
            named.append(argv[0])
    for name in named:
        if os.path.isabs(name) or "/" not in name and not name.endswith((".py", ".sh")) and not os.path.exists(os.path.join(PAYLOAD, name)):
            continue  # an absolute program (/bin/sh) or a bare word
        if os.path.exists(os.path.join(PAYLOAD, name)):
            continue
        if has_setup and (name in created_by_setup or name.split("/")[0] in EXCLUDED_DIRECTORIES):
            continue  # setup builds it
        fail(f"plugin.json names `{name}`, which is not in the plugin folder")
    return manifest


def build(manifest, out):
    name = NAME or manifest["id"]
    stem = f"{name}-{manifest['version']}"
    os.makedirs(out, exist_ok=True)
    archive = os.path.join(out, f"{stem}.zip")
    temporary = archive + ".part"
    total = 0
    with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as package:
        for relative in payload_files():
            source = os.path.join(PAYLOAD, relative)
            info = zipfile.ZipInfo(f"{stem}/{relative.replace(os.sep, '/')}")
            info.date_time = (2026, 1, 1, 0, 0, 0)  # reproducible: no build-time stamps
            mode = os.stat(source).st_mode
            executable = mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            info.external_attr = ((0o755 if executable else 0o644) | stat.S_IFREG) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            data = open(source, "rb").read()
            total += len(data)
            package.writestr(info, data)
    if total > MAX_PACKAGE_BYTES:
        os.remove(temporary)
        fail(f"the package would be {total} bytes; does plugin/ contain an environment?")
    os.replace(temporary, archive)
    digest = hashlib.sha256(open(archive, "rb").read()).hexdigest()
    with open(archive + ".sha256", "w") as handle:
        handle.write(f"{digest}  {os.path.basename(archive)}\n")
    return archive, digest


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("folder", help="the plugin folder (the one holding plugin.json)")
    parser.add_argument("--check", action="store_true", help="validate only")
    parser.add_argument("--name", help="archive name; default: the plugin id")
    parser.add_argument("--out", default="dist")
    options = parser.parse_args()
    global PAYLOAD, NAME
    PAYLOAD = os.path.abspath(options.folder)
    NAME = options.name
    manifest = validate()
    files = payload_files()
    if options.check:
        print(f"{manifest['id']} {manifest['version']}: manifest valid, {len(files)} file(s) in the payload")
        return 0
    archive, digest = build(manifest, options.out)
    print(f"{archive}\nsha256 {digest}\n{len(files)} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

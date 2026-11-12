> **Public copy.** Generated from the documentation bundled with EigenMol
> (`tools/plugins/export_public_spec.py`); edit the source, not this copy.
> These documents describe the plugin interface EigenMol implements today and
> are published so a plugin can be written without EigenMol's source. Their
> licence is not chosen yet; until it is, they are published for reading and
> for writing plugins against.

# Automatic dependency installation

A user installs your plugin by pasting an address. Your plugin then needs an
engine, a Python library or model weights. This document is the contract that
lets **Set up…** build all of that on the user's machine, with their approval
and without manual steps. It uses manifest fields EigenMol already reads:
`requirements`, `setup`, `check`, `settings` and `system` (spec §12).

## When you need it, and when you do not

| Your plugin needs | Declare |
| --- | --- |
| nothing beyond `/usr/bin/env python3` and the standard library | no `setup`, no `requirements`. Say what it needs in `system.notes` |
| a self-contained binary you ship in the package | no `setup`. The binary is in the ZIP, and `platforms` matches the binaries you ship |
| a Python package, an engine binary, model weights | `requirements` + `setup` + `check` |
| a remote service | no `setup`; a `setting` for the address or key, and `capabilities: ["network"]` |

Do not add a setup that does nothing. A plugin with nothing to install has
nothing to approve.

## The four declarations

```json
"requirements": [
  { "name": "Private Python with MyLib", "path": "env/bin/python",
    "hint": "Run Set up. It builds this environment inside the plugin's folder." },
  { "name": "MyEngine 2.3", "path": "bin/myengine", "setting": "myengine_executable",
    "hint": "Run Set up, or point Settings at a myengine you already have." }
],
"settings": [
  { "key": "myengine_executable", "label": "MyEngine program", "kind": "file",
    "required": false, "description": "Leave empty to use the one Set up downloads." }
],
"setup": {
  "description": "Downloads micromamba 2.10.0, builds a private Python 3.12 with MyLib 4.1 from conda-forge, and downloads MyEngine 2.3. Everything stays inside this plugin's folder.",
  "network": true, "download_mb": 150, "disk_mb": 700, "timeout_seconds": 3600,
  "commands": {
    "macos": ["/bin/sh", "setup/install.sh"],
    "linux": ["/bin/sh", "setup/install.sh"]
  }
},
"check": {
  "commands": {
    "macos": ["env/bin/python", "my_plugin.py", "--check"],
    "linux": ["env/bin/python", "my_plugin.py", "--check"]
  }
}
```

- **`requirements`** are files EigenMol looks for without running anything. If
  one is missing and a setup is declared, the plugin's status is *needs setup*.
  `setting` lets an existing installation satisfy the requirement instead.
- **`setup`** is what EigenMol runs after the user approves it. The approval
  dialog shows `description`, the resolved command, `network`, `download_mb`
  and `disk_mb`, so state them honestly.
- **`commands`** keys are `macos`, `linux`, `windows`, optionally with a
  processor: `macos-arm64` takes precedence over `macos` on Apple silicon. A
  platform with no command has no setup there; leave it out of `platforms` too.
- **`check`** prints one JSON readiness report (spec §12). It must exercise the
  real path: import the library, run the engine's `--version`, load a parameter
  file, evaluate a tiny input.

## Rules for a setup

1. **Write only inside the plugin folder.** EigenMol runs the setup with that
   folder as the working directory and passes it as `EIGENMOL_PLUGIN_DIR`. Do
   not write to the user's home, a system location, a shared conda, or another
   plugin's folder.
2. **Assume no Python, conda or compiler.** Bring a self-contained installer
   (micromamba, a static binary) or a prebuilt binary.
3. **Pin versions, and verify what you download.** Every download is checked
   against a SHA-256 written in your script or published beside the file. Stop
   on a mismatch and say which file did not match.
4. **Use the engine's official distribution.** Download it from its publisher
   at install time. Do not commit someone else's binary into your repository
   or your package unless its licence allows redistribution and you comply.
5. **Be re-runnable.** Skip a step that is complete and redo one that is not.
   A failed setup must be fixable by pressing **Set up…** again.
6. **Fail in sentences.** Exit non-zero and say on stderr what failed and what
   to do. The last lines of stdout and stderr are shown to the user.
7. **No administrator rights, no system changes.** If something requires them,
   it is not automatic. Say so in `system.notes` and in your README.
8. **Choose a platform before downloading.** Refuse an unsupported OS or
   processor at once, with exit code 3, before downloading anything.

EigenMol gives the setup:

| Variable | Value |
| --- | --- |
| `EIGENMOL_PLUGIN_DIR` | the plugin folder |
| `EIGENMOL_PLUGIN_ID` | your id |
| `EIGENMOL_PLATFORM` | `macos`, `windows`, `linux` |
| `EIGENMOL_ARCH` | `arm64`, `x86_64` |
| `EIGENMOL_SETTING_<KEY>` | each declared setting |

The setup runs as one process group, so **Stop** stops everything it started.
Its timeout is `timeout_seconds`: 2 hours by default, at most 12.

## Patterns

### A private Python with conda-forge packages (macOS, Linux)

[`templates/python-with-setup/setup/install.sh`](templates/python-with-setup/setup/install.sh)
is a complete script. In outline:

```sh
MICROMAMBA_VERSION="2.10.0-0"
case "$(uname -s)-$(uname -m)" in
  Darwin-arm64)  MAMBA_PLATFORM=osx-arm64;     MAMBA_SHA256=c547639f…c01 ;;
  Darwin-x86_64) MAMBA_PLATFORM=osx-64;        MAMBA_SHA256=8421462a…172 ;;
  Linux-x86_64)  MAMBA_PLATFORM=linux-64;      MAMBA_SHA256=701f39c0…bd ;;
  Linux-aarch64) MAMBA_PLATFORM=linux-aarch64; MAMBA_SHA256=3bb56786…23c ;;
  *) echo "unsupported: $(uname -s) $(uname -m)" >&2; exit 3 ;;
esac
# fetch micromamba from github.com/mamba-org/micromamba-releases, verify, then
.tools/micromamba create -y -p "$DIR/env" -c conda-forge --override-channels \
  "python=3.12" "mylib=4.1"
rm -rf "$DIR/.mamba/pkgs"
```

micromamba publishes a `.sha256` for each binary, and conda-forge packages are
verified by micromamba against the channel's checksums. Pin exact package
versions where results depend on them.

### A Python package that is only on PyPI

Install it into the same environment with
`env/bin/python -m pip install --no-deps "package==X.Y"`, after the
conda-forge step has provided its dependencies. `--no-deps` keeps pip from
replacing them.

### An engine binary from its release page

```sh
fetch "https://github.com/publisher/engine/releases/download/v2.3/engine-$PLATFORM" \
  "bin/engine" "$ENGINE_SHA256"
chmod +x bin/engine
```

If the publisher does not publish a checksum, compute it yourself from the
official asset, write it in the script, and say in your README that you did.

### Model weights

These are large, and their licence is often not the code's. Download them in
setup, state `download_mb` and `disk_mb`, check them against a SHA-256, and
name the weights' licence in your README and in `setup.description`.

### Windows

Declare `"windows": ["powershell.exe", "-NoProfile", "-ExecutionPolicy",
"Bypass", "-File", "setup\\install.ps1"]` and the same steps in PowerShell
(`Invoke-WebRequest`, `Get-FileHash`). On Windows a Python environment's
interpreter is `env\python.exe`. Requirements and entrypoints that differ per
platform need their own `platforms` lists. If you have not run it on Windows,
do not list `windows`.

## What EigenMol records

After every setup and check, EigenMol records the outcome in the plugin's
install record (`plugins/.installs/<id>.json`): when it ran, whether it passed,
and the sentence it ended with. The status a user sees combines that record
with the requirements:

- *needs setup*: no setup has run yet;
- *setup failed*: the last setup failed;
- *missing dependency*: a requirement is missing with no setup to provide it;
- *not checked*: set up, not yet checked;
- *check failed*: the last check reported "not ready";
- *ready*: set up and checked.

Installing the files, setting up and being able to compute are three separate
results.

## Recovery

- **A failed setup** keeps what it finished. Pressing **Set up…** again re-runs
  it, and finished steps are skipped.
- **A broken upgrade.** Replacing a plugin keeps the previous version, with its
  environment, in `plugins/.previous/`. **Restore** swaps them back, and the
  restored version starts disabled.
- **Removal.** Uninstalling deletes the plugin folder, and with it everything
  setup built, and its record. Nothing outside the folder exists to clean up.

## What EigenMol does not provide

- **No sandbox.** A setup runs with the user's privileges. Isolation means
  separate folders and environments per plugin, not containment.
- **No package manager of its own.** The core is not tied to conda, pip or any
  other tool. Your setup picks one.
- **No bundled interpreter or engine.** The core ships none for plugins.

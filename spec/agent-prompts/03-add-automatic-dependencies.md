# Add automatic dependency installation

A prompt for a coding agent (Kiro, Codex, Claude Code or another). Give it this file with the EigenMol `docs/plugins/` folder in context. Nothing here requires any other plugin's source.

Fill in:

```text
PLUGIN_DIR:     path to the plugin folder (holding plugin.json)
DEPENDENCIES:   e.g. "Python 3.12, mylib==4.1 from conda-forge, myengine 2.3 binary from its GitHub releases"
PLATFORMS:      e.g. macos-arm64, macos-x86_64, linux-x86_64
```

## Task

Make PLUGIN_DIR install its own DEPENDENCIES when the user presses **Set up…**.

1. Read `docs/plugins/AUTOMATIC_DEPENDENCIES.md` and spec §12.
2. For each dependency, find the official distribution for each platform in PLATFORMS: package name and exact version on conda-forge or PyPI, or the release asset URL. Record the source links.
3. Pin every version. For every downloaded file, obtain the publisher's checksum, or compute it from the official file and say so in a comment.
4. Write `setup/install.sh` (and `setup/install.ps1` only if Windows is in PLATFORMS and you can run it). It must refuse an unsupported platform before downloading (exit 3), write only inside the plugin folder, verify every checksum, skip finished steps, and end by exercising what it installed.
5. Declare in `plugin.json`: `requirements` (the files setup creates), `setup` (an honest description, `network`, `download_mb`, `disk_mb`, `timeout_seconds`, per-platform `commands`), `platforms` matching what you support, and `entrypoint` pointing at the environment's interpreter if there is one.
6. Run `eigenmol-plugin-check PLUGIN_DIR --install --setup --root /tmp/fresh-plugins` with `PATH=/usr/bin:/bin` so that no Python of yours is used. Fix until it passes.
7. Run setup a second time in the same root and confirm it skips finished steps.
8. Report the measured download size, disk size and duration.

## Rules

- Base everything on the EigenMol Plugin Specification (`docs/plugins/PLUGIN_SPECIFICATION.md`, version 1.2, protocol 1) and the program's own official documentation. Do not guess either.
- Do not invent an API, a flag, a manifest field, a message or a result type. If something you need is missing from the specification, stop and report it.
- Never return synthetic or placeholder values as a result. A real result or a typed error. Test data is declared `"synthetic": true`.
- Do not change the protocol or the result schemas.
- Installation is automatic or it is not done: a declared `setup` installs everything inside the plugin folder, pinned and checksummed.
- Do not ask the user to fix their environment. Fix the plugin.
- Download third-party programs and weights from their publishers at setup. Do not commit them. Name their licences.
- Report each item as Verified, Implemented but not independently verified, Blocked, or Not implemented. A passing harness is not scientific validation.

# Prepare a plugin release

A prompt for a coding agent (Kiro, Codex, Claude Code or another). Give it this file with the EigenMol `docs/plugins/` folder in context. Nothing here requires any other plugin's source.

Fill in:

```text
REPOSITORY_DIR:  the plugin repository
VERSION:         e.g. 1.0.0
CHANNEL:         GitHub release | own HTTPS server
```

## Task

Prepare release VERSION of the plugin in REPOSITORY_DIR. Do not publish anything public without the owner's explicit approval.

1. Set `version` in `plugin.json` and `PLUGIN_VERSION` in the adapter to VERSION.
2. Run the repository tests.
3. Build the package: `python3 docs/plugins/pdk/package_plugin.py <plugin folder> --name <repo-name> --out dist` (or the repository's own `tools/package.py`).
4. Install the built ZIP in a clean root: `eigenmol-plugin-check dist/<zip> --install --setup --root /tmp/release-check`. It must pass.
5. Update the README: version, what changed, engine versions, platforms verified and not verified.
6. For a GitHub release: tag `vVERSION`; the release attaches the ZIP and its `.sha256`. For a server: the ZIP and `.sha256` are served over HTTPS at stable, versioned names.
7. Report the ZIP's SHA-256, the harness output, and anything not verified.

## Rules

- Base everything on the EigenMol Plugin Specification (`docs/plugins/PLUGIN_SPECIFICATION.md`, version 1.2, protocol 1) and the program's own official documentation. Do not guess either.
- Do not invent an API, a flag, a manifest field, a message or a result type. If something you need is missing from the specification, stop and report it.
- Never return synthetic or placeholder values as a result. A real result or a typed error. Test data is declared `"synthetic": true`.
- Do not change the protocol or the result schemas.
- Installation is automatic or it is not done: a declared `setup` installs everything inside the plugin folder, pinned and checksummed.
- Do not ask the user to fix their environment. Fix the plugin.
- Download third-party programs and weights from their publishers at setup. Do not commit them. Name their licences.
- Report each item as Verified, Implemented but not independently verified, Blocked, or Not implemented. A passing harness is not scientific validation.

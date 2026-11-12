# Add a plugin health check

A prompt for a coding agent (Kiro, Codex, Claude Code or another). Give it this file with the EigenMol `docs/plugins/` folder in context. Nothing here requires any other plugin's source.

Fill in:

```text
PLUGIN_DIR:   the plugin folder
WHAT_RUNS:    e.g. "env/bin/python imports mylib; bin/myengine --version"
```

## Task

Add a `check` to PLUGIN_DIR that tells the user whether the calculation can run here.

1. Read spec §12 (`check`) and `docs/plugins/AUTOMATIC_DEPENDENCIES.md`.
2. Implement `--check` in the adapter. It prints exactly one JSON object `{"ready": bool, "summary": str, "items": [{"name","status","detail","fix"}]}` on stdout and exits 0. Status is `ok`, `missing`, `warning` or `error`.
3. Exercise the real path on a tiny input: import each library the adapter uses, run the engine's version command, load any parameter or model file, and if cheap compute something trivial. A check that only tests file existence is not enough.
4. Each item that is not ok says how to fix it (`Run Set up again.`, `Open Settings and choose …`).
5. Declare `check.commands` for each platform in `plugin.json`.
6. Run `eigenmol-plugin-check PLUGIN_DIR --install --setup` and confirm the check stage passes; then break one dependency in the kept root and confirm the check reports it.

## Rules

- Base everything on the EigenMol Plugin Specification (`docs/plugins/PLUGIN_SPECIFICATION.md`, version 1.2, protocol 1) and the program's own official documentation. Do not guess either.
- Do not invent an API, a flag, a manifest field, a message or a result type. If something you need is missing from the specification, stop and report it.
- Never return synthetic or placeholder values as a result. A real result or a typed error. Test data is declared `"synthetic": true`.
- Do not change the protocol or the result schemas.
- Installation is automatic or it is not done: a declared `setup` installs everything inside the plugin folder, pinned and checksummed.
- Do not ask the user to fix their environment. Fix the plugin.
- Download third-party programs and weights from their publishers at setup. Do not commit them. Name their licences.
- Report each item as Verified, Implemented but not independently verified, Blocked, or Not implemented. A passing harness is not scientific validation.

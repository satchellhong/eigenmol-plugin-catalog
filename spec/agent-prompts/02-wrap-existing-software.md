# Wrap existing scientific software as an EigenMol plugin

A prompt for a coding agent (Kiro, Codex, Claude Code or another). Give it this file with the EigenMol `docs/plugins/` folder in context. Nothing here requires any other plugin's source.

Fill in:

```text
PROGRAM:            name and version, e.g. "MyEngine 2.3"
OFFICIAL_SOURCE:    the official repository or download page
DOCUMENTATION:      link to its user documentation
WHAT_TO_EXPOSE:     e.g. "rigid-receptor docking returning ranked poses"
PLATFORMS:          the platforms the program officially supports and you will test
TEST_DATA:          a real input the result can be checked against
```

## Task

Connect PROGRAM to EigenMol as a plugin. You are writing an adapter. Do not reimplement the program.

1. From OFFICIAL_SOURCE and DOCUMENTATION, write down: how the program is installed, its inputs, its outputs, its versions, its supported platforms and its licence. Link each fact.
2. Install it yourself and run it once on TEST_DATA. Keep the real input and the real output.
3. Read `docs/plugins/PLUGIN_SPECIFICATION.md`. Choose the result types (for docking: `pose_set`; for an energy: `energy_result`; for per-residue values: `residue_scalar`; for a complex: `structure`; otherwise `table` or `metadata`).
4. Start from `docs/plugins/templates/python-with-setup/` (or `python-minimal/` if the program needs nothing installed).
5. Map the input snapshot (spec §8) to the program's input. Run the program as a subprocess with an argument list. Map its output to typed results (spec §9), with units, quantity keys in your namespace, provenance (method, engine, engine_version) and names rather than indices. A docking score keeps the engine's score type and is never called an affinity.
6. Write `setup/install.sh` so the program and its libraries install automatically inside the plugin folder, from the official source, pinned and checksummed (`docs/plugins/AUTOMATIC_DEPENDENCIES.md`).
7. Write a `check` that runs the program's own version command and imports what the adapter imports.
8. Validate: run the plugin through `eigenmol-plugin-check plugin --install --setup` in a fresh `--root`. Then run the real action on TEST_DATA and compare the result with the program's own output from step 2. It must be the same.
9. Package with `docs/plugins/pdk/package_plugin.py` and install the ZIP with `--install --setup`.
10. Write the README: what it does, the engine and its licence, what setup downloads, platforms, limits.
11. Report verified and not-verified items separately.

## Rules

- Base everything on the EigenMol Plugin Specification (`docs/plugins/PLUGIN_SPECIFICATION.md`, version 1.2, protocol 1) and the program's own official documentation. Do not guess either.
- Do not invent an API, a flag, a manifest field, a message or a result type. If something you need is missing from the specification, stop and report it.
- Never return synthetic or placeholder values as a result. A real result or a typed error. Test data is declared `"synthetic": true`.
- Do not change the protocol or the result schemas.
- Installation is automatic or it is not done: a declared `setup` installs everything inside the plugin folder, pinned and checksummed.
- Do not ask the user to fix their environment. Fix the plugin.
- Download third-party programs and weights from their publishers at setup. Do not commit them. Name their licences.
- Report each item as Verified, Implemented but not independently verified, Blocked, or Not implemented. A passing harness is not scientific validation.

# Run the EigenMol plugin conformance tests

A prompt for a coding agent (Kiro, Codex, Claude Code or another). Give it this file with the EigenMol `docs/plugins/` folder in context. Nothing here requires any other plugin's source.

Fill in:

```text
SOURCE:   a plugin folder, a ZIP, or an https URL
```

## Task

Run the official compatibility harness against SOURCE and make it pass.

1. Locate `eigenmol-plugin-check` where your EigenMol build provides it; otherwise use **Plugins ▸ Create your own plugin ▸ Test a plugin folder…** in the app, which runs the same stages.
2. Run, in order:
   - `eigenmol-plugin-check SOURCE --list` if SOURCE is a URL;
   - `eigenmol-plugin-check SOURCE`;
   - `eigenmol-plugin-check SOURCE --install`;
   - `eigenmol-plugin-check SOURCE --install --setup --root /tmp/fresh-plugins --keep`.
3. For each failed stage, read its sentence, fix the plugin (never the harness), and rerun.
4. An action marked SKIPPED was not invoked by the harness (its shape is neither docking nor single-structure). Test it separately with real input and say so.
5. Report the final output of each command, and which actions were exercised with real input.

## Rules

- Base everything on the EigenMol Plugin Specification (`docs/plugins/PLUGIN_SPECIFICATION.md`, version 1.2, protocol 1) and the program's own official documentation. Do not guess either.
- Do not invent an API, a flag, a manifest field, a message or a result type. If something you need is missing from the specification, stop and report it.
- Never return synthetic or placeholder values as a result. A real result or a typed error. Test data is declared `"synthetic": true`.
- Do not change the protocol or the result schemas.
- Installation is automatic or it is not done: a declared `setup` installs everything inside the plugin folder, pinned and checksummed.
- Do not ask the user to fix their environment. Fix the plugin.
- Download third-party programs and weights from their publishers at setup. Do not commit them. Name their licences.
- Report each item as Verified, Implemented but not independently verified, Blocked, or Not implemented. A passing harness is not scientific validation.

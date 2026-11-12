# Troubleshoot a plugin installation

A prompt for a coding agent (Kiro, Codex, Claude Code or another). Give it this file with the EigenMol `docs/plugins/` folder in context. Nothing here requires any other plugin's source.

Fill in:

```text
SOURCE:        what the user tried to install (URL, ZIP or folder)
WHAT_HAPPENED: the sentence EigenMol showed, and the stage it stopped at
PLATFORM:      e.g. macOS 15 on Apple silicon
LOG:           the setup or check log from the plugin's card, if any
```

## Task

Find why installing SOURCE failed and fix the plugin, or explain precisely why the user's situation cannot work.

1. Read `docs/plugins/TROUBLESHOOTING.md` and find WHAT_HAPPENED there.
2. Reproduce with `eigenmol-plugin-check SOURCE --install --setup --root /tmp/repro --keep` on PLATFORM, with `PATH=/usr/bin:/bin`.
3. Classify the failure as one of: address or access; download or checksum; package structure; manifest validation; platform; setup (which step); check (which item); runtime protocol; the engine refusing an input.
4. Fix the plugin if the plugin is wrong (setup assumptions, missing file in the package, wrong checksum, wrong platform list). Never weaken a check to make it pass.
5. Verify the fix with the same command in a fresh root.
6. Report the cause, the fix, and the evidence.

## Rules

- Base everything on the EigenMol Plugin Specification (`docs/plugins/PLUGIN_SPECIFICATION.md`, version 1.2, protocol 1) and the program's own official documentation. Do not guess either.
- Do not invent an API, a flag, a manifest field, a message or a result type. If something you need is missing from the specification, stop and report it.
- Never return synthetic or placeholder values as a result. A real result or a typed error. Test data is declared `"synthetic": true`.
- Do not change the protocol or the result schemas.
- Installation is automatic or it is not done: a declared `setup` installs everything inside the plugin folder, pinned and checksummed.
- Do not ask the user to fix their environment. Fix the plugin.
- Download third-party programs and weights from their publishers at setup. Do not commit them. Name their licences.
- Report each item as Verified, Implemented but not independently verified, Blocked, or Not implemented. A passing harness is not scientific validation.

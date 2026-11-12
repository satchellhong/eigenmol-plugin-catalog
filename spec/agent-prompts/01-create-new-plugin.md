# Create a new EigenMol plugin

A prompt for a coding agent (Kiro, Codex, Claude Code or another). Give it this file with the EigenMol `docs/plugins/` folder in context. Nothing here requires any other plugin's source.

Fill in:

```text
PLUGIN_ID:        org.yourlab.yourplugin
PLUGIN_NAME:      Your plugin
WHAT_IT_DOES:     one sentence
ACTION:           analysis of the open structure | docking | energy | predicted complex
LANGUAGE:         Python 3 (or: …)
PLATFORMS:        macos, linux (only what you will test)
REPOSITORY_DIR:   ./my-eigenmol-plugin
```

## Task

Create a new EigenMol plugin repository at REPOSITORY_DIR.

1. Read `docs/plugins/PLUGIN_SPECIFICATION.md` and `docs/plugins/CREATE_YOUR_OWN_PLUGIN.md`.
2. Copy `docs/plugins/templates/python-minimal/` into `REPOSITORY_DIR/plugin/`.
3. Edit `plugin.json`: set the id, name, version `0.1.0`, `spec_version` `1.2`, platforms, author, licence placeholder, and one action whose `extension_point`, `inputs` and `results` match ACTION (CREATE_YOUR_OWN_PLUGIN.md step 3).
4. Rename the adapter, set `PLUGIN_ID` and `PLUGIN_VERSION`, and implement the action. Keep the transport, handshake and check structure of the template.
5. Add `README.md`, `.gitignore` (env/, bin/, .tools/, .mamba/, dist/, __pycache__/) and `tests/` with at least: the manifest parses, the handshake answers with the declared actions.
6. Run `eigenmol-plugin-check REPOSITORY_DIR/plugin` and fix every failed step.
7. Run `python3 docs/plugins/pdk/package_plugin.py REPOSITORY_DIR/plugin --name <repo-name> --out REPOSITORY_DIR/dist`, then `eigenmol-plugin-check REPOSITORY_DIR/dist/<zip> --install`.
8. Report the files created and the harness output.

## Rules

- Base everything on the EigenMol Plugin Specification (`docs/plugins/PLUGIN_SPECIFICATION.md`, version 1.2, protocol 1) and the program's own official documentation. Do not guess either.
- Do not invent an API, a flag, a manifest field, a message or a result type. If something you need is missing from the specification, stop and report it.
- Never return synthetic or placeholder values as a result. A real result or a typed error. Test data is declared `"synthetic": true`.
- Do not change the protocol or the result schemas.
- Installation is automatic or it is not done: a declared `setup` installs everything inside the plugin folder, pinned and checksummed.
- Do not ask the user to fix their environment. Fix the plugin.
- Download third-party programs and weights from their publishers at setup. Do not commit them. Name their licences.
- Report each item as Verified, Implemented but not independently verified, Blocked, or Not implemented. A passing harness is not scientific validation.

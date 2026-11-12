# Implement plugin input and output

A prompt for a coding agent (Kiro, Codex, Claude Code or another). Give it this file with the EigenMol `docs/plugins/` folder in context. Nothing here requires any other plugin's source.

Fill in:

```text
PLUGIN_DIR:     the plugin folder
ACTION_ID:      the action to implement
ENGINE_INPUT:   what the engine reads (format, fields)
ENGINE_OUTPUT:  what it writes (format, fields, units)
```

## Task

Implement ACTION_ID's mapping between EigenMol's snapshot and the engine, and between the engine's output and typed results.

1. Read spec §8 (inputs) and §9–§10 (results, scores, quantities, units, provenance).
2. Input: build ENGINE_INPUT from the snapshot. Use atom names, residue numbers, chains, elements, positions and stated bond orders as given. Do not guess bond orders, add hydrogens or change protonation unless the engine's documented preparation does that, and then report it in `parameters`.
3. Output: return the result types the manifest declares.
   - every number has its unit;
   - every scientific value has a quantity key in your namespace;
   - unavailable is `"unavailable": "reason"`, never `0`;
   - references use the names you received;
   - `pose_set` has one coordinate per ligand atom, in the order received;
   - a score has a `score_type`.
4. Errors: `invalid_input` for an input this engine cannot compute, `engine_missing`, `calculation_failed`, each with a sentence the user can act on.
5. Test with a real input and assert the result validates: `eigenmol-plugin-check PLUGIN_DIR`.
6. Report which fields of ENGINE_OUTPUT were mapped, which were dropped and why.

## Rules

- Base everything on the EigenMol Plugin Specification (`docs/plugins/PLUGIN_SPECIFICATION.md`, version 1.2, protocol 1) and the program's own official documentation. Do not guess either.
- Do not invent an API, a flag, a manifest field, a message or a result type. If something you need is missing from the specification, stop and report it.
- Never return synthetic or placeholder values as a result. A real result or a typed error. Test data is declared `"synthetic": true`.
- Do not change the protocol or the result schemas.
- Installation is automatic or it is not done: a declared `setup` installs everything inside the plugin folder, pinned and checksummed.
- Do not ask the user to fix their environment. Fix the plugin.
- Download third-party programs and weights from their publishers at setup. Do not commit them. Name their licences.
- Report each item as Verified, Implemented but not independently verified, Blocked, or Not implemented. A passing harness is not scientific validation.

# Starter template: Atom counts

A complete EigenMol plugin written from `docs/plugins/PLUGIN_SPECIFICATION.md`
alone, with no external program. Copy this folder to start your own plugin.

| File | What it is |
| --- | --- |
| `plugin.json` | the manifest: id, version, platforms, one `analysis_action`, a `check` |
| `atomcounts_plugin.py` | the program: transport (§6), handshake (§7), the input snapshot (§8), typed `table` and `metadata` results (§9), typed errors (§11), `--check` (§12) |

What it computes: the atoms of the open structure, counted by element and by
chain. That is real, if simple, arithmetic, so it is not declared synthetic.

```text
eigenmol-plugin-check .                         # compatibility test on the folder
eigenmol-plugin-check . --install               # through the real installer
python3 ../../pdk/package_plugin.py . --out dist  # the release ZIP
```

To make it yours, follow `docs/plugins/CREATE_YOUR_OWN_PLUGIN.md`:

1. change `id`, `name` and `PLUGIN_ID`;
2. replace `count_atoms` with your computation;
3. declare your results;
4. if you need dependencies, start from `../python-with-setup/` instead.

Needs `python3` 3.8+ on the PATH and the standard library only. It declares
macOS and Linux, because on Windows `/usr/bin/env` does not exist (see spec §13).

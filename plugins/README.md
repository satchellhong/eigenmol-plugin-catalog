# plugins/

One file per plugin, named after the plugin's id: `plugins/<id>.json`.

The file follows [`schema/entry.schema.json`](../schema/entry.schema.json).
[`docs/REGISTERING_A_PLUGIN.md`](../docs/REGISTERING_A_PLUGIN.md) explains every
field and the pull-request steps.

After adding or changing a file here, run

```sh
python3 tools/catalog.py validate
python3 tools/catalog.py build
```

and commit both the entry and the regenerated `index.json`.

The catalog lists no plugins yet.

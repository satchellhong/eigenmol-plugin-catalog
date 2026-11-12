# Setup template: a private Python environment

The starter template plus automatic dependency installation
(`docs/plugins/AUTOMATIC_DEPENDENCIES.md`):

| File | What it is |
| --- | --- |
| `plugin.json` | adds `requirements` (`env/bin/python`), `setup` (with honest sizes) and a `check` run in the private environment; `platforms` names OS and processor |
| `setup/install.sh` | downloads micromamba 2.10.0, checks its published SHA-256, and builds `env/` with Python 3.12 and NumPy from conda-forge, inside the plugin folder only; re-runnable; refuses an unsupported platform before downloading |
| `atomcounts_plugin.py` | the same program; `--check` imports and exercises NumPy |

NumPy stands in for your scientific library: replace it in `setup/install.sh`
and in `check`, pin the version you test with, and add your engine's official
binary download if you need one.

```text
eigenmol-plugin-check . --install --setup --root /tmp/fresh-plugins
```

That command installs this folder into a throw-away plugins folder, runs the
setup exactly as **Set up…** would, runs the check and then the compatibility
test. Measured on macOS arm64: about 1 minute, about 250 MB on disk.

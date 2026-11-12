# EigenMol plugin catalog

The list of plugins EigenMol offers under **Plugins ▸ Downloadable plugins**.

EigenMol is a desktop molecular workbench. A plugin is a separate program that
EigenMol can run for a computation it does not do itself — docking, an energy
estimate, a structure prediction. This repository is only the **list**: each
entry names a plugin, who publishes it, and where its package can be
downloaded, with the package's SHA-256. The packages themselves stay where
their publishers put them.

```text
this repository ──► index.json (public, static)
                        │  one HTTPS GET, no account
                        ▼
                 EigenMol ▸ Downloadable plugins
                        │  the user chooses a plugin
                        ▼
          the publisher's package (e.g. a GitHub release asset)
                        │  held to the SHA-256 listed here
                        ▼
          EigenMol's own installer: read, validate, approve, install (disabled)
```

## What EigenMol reads

```text
https://raw.githubusercontent.com/satchellhong/eigenmol-plugin-catalog/main/index.json
```

A plain JSON file, readable without signing in. EigenMol asks for it when the
Downloadable plugins panel opens (at most once an hour unless the user presses
Refresh) and keeps the last copy it read, so the list still shows — marked as
an older copy — when the computer is offline.

**Reading the list sends nothing about the user's work.** The request is a GET
of this one file; no structure, file, project, result or identifier travels
with it. Nothing is downloaded until the user chooses a plugin, and nothing
runs until the user enables it after installing.

A new listing, or a new version of a listed plugin, appears in EigenMol as soon
as it is merged here. EigenMol itself does not need to be updated.

## What a listing means, and what it does not

A listing means a maintainer of this catalog reviewed the pull request that
added it: the package downloads, its checksum and its `plugin.json` agree with
the entry, and the description is not misleading as far as the reviewer could
tell.

It does **not** mean that the plugin's code was audited, that it is safe to
run, or that its scientific results are correct. A plugin runs on the user's
computer with the user's permissions. EigenMol shows the program it will run
before it is enabled, and installs every plugin disabled.

## Writing a plugin

[`spec/`](spec/README.md) is the plugin specification, the tutorial, the
templates and the packaging tool — everything needed to write a plugin
without EigenMol's source. It is a generated copy of the documentation
EigenMol ships with; changes are made there and copied here.

## Plugins that are not listed

A plugin does not have to be in this catalog to be used. EigenMol installs a
plugin from a folder, a ZIP file or any HTTPS address under
**Plugins ▸ Install from a file or address**, exactly as it does a listed one.
A laboratory's internal tools and a plugin received from a colleague never
need to be published here. An organisation can also point EigenMol at its own
copy of a catalog with the `EIGENMOL_PLUGIN_CATALOG_URL` environment variable.

## Listing a plugin

Open a pull request that adds `plugins/<your.plugin.id>.json`. The steps, the
fields and what the reviewer checks are in
[docs/REGISTERING_A_PLUGIN.md](docs/REGISTERING_A_PLUGIN.md).

The checks run automatically on every pull request
([`.github/workflows/validate.yml`](.github/workflows/validate.yml)). They
validate the entry, regenerate `index.json`, and download each package the
change lists to compare its SHA-256, plugin id and version with the entry. They
never extract or run a package. A maintainer's approval is still required to
merge.

## Repository layout

| path | what it is |
| --- | --- |
| `index.json` | what EigenMol reads; generated, never edited by hand |
| `plugins/<id>.json` | one entry per plugin, the source of `index.json` |
| `schema/` | JSON Schemas for an entry and for `index.json` |
| `tools/catalog.py` | `validate`, `build`, `verify`; standard-library Python 3 |
| `tests/` | tests of `tools/catalog.py`; the fixtures are test data, not plugins |
| `docs/` | registering a plugin; maintaining the catalog |

## Status

The catalog lists no plugins yet. EigenMol's own plugins (AutoDock Vina,
MM/GBSA on OpenMM, the MyDock example) are distributed separately and are not
listed here.

No licence has been chosen for the contents of this repository yet.

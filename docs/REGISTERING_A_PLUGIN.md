# Registering a plugin

Listing a plugin is a pull request that adds one JSON file. Nothing in this
repository holds your code or your package.

## 1. Build the plugin

Follow the EigenMol plugin specification. It ships with EigenMol and is
readable offline: **Plugins ▸ Create your own plugin…** opens the specification and
the developer guide, saves the MyDock example and the templates to a folder,
and runs the compatibility test on your folder. Use whatever language and
libraries suit the engine; nothing requires you to copy an existing plugin.

Before listing it, the plugin should:

- pass the compatibility test (**Test a plugin folder…** in that dialog);
- declare `platforms` in `plugin.json` honestly, if it runs only on some;
- declare its `setup` (and its `network` and download size) if it installs
  dependencies, so the user is told before it runs;
- state in its own documentation what it computes and what its numbers are
  not (a docking score is not a binding affinity, for example).

## 2. Publish the package

Make a ZIP of the plugin folder. The packaging tool in the developer guide
(`package_plugin.py`) writes a reproducible ZIP and its `.sha256`.

Publish it at a **public, permanent** address:

- **A GitHub release asset** (recommended):
  `https://github.com/OWNER/REPO/releases/download/v1.0.0/my-plugin-1.0.0.zip`.
  Attach the `.sha256` file to the same release as well.
- **Any other HTTPS address** that will keep serving the same bytes.

Not accepted: a repository page, a `releases/tag/…` page, a branch archive
(`archive/refs/heads/main.zip`), an address with a query string or a token,
an address that needs signing in. A private repository's release cannot be
downloaded by other people, so it cannot be listed.

Compute the checksum of the exact file you uploaded:

```sh
shasum -a 256 my-plugin-1.0.0.zip      # macOS
sha256sum my-plugin-1.0.0.zip          # Linux
```

## 3. Add your entry

Fork this repository (or create a branch if you are a maintainer) and add
`plugins/<id>.json`, where `<id>` is the `id` in your `plugin.json`.

```json
{
  "format": "eigenmol-plugin-catalog-entry",
  "schema_version": 1,
  "id": "io.github.yourname.my-plugin",
  "name": "My plugin",
  "summary": "One sentence: what it computes, with which method.",
  "description": "A paragraph: inputs, outputs, assumptions and limits.",
  "publisher": { "name": "Your name or lab", "url": "https://github.com/yourname" },
  "category": "analysis",
  "license": "MIT",
  "homepage": "https://github.com/yourname/my-plugin",
  "source_repository": "https://github.com/yourname/my-plugin",
  "status": "active",
  "network": { "setup": true, "runs": false, "note": "Setup downloads its Python environment (about 300 MB)." },
  "releases": [
    {
      "version": "1.0.0",
      "url": "https://github.com/yourname/my-plugin/releases/download/v1.0.0/my-plugin-1.0.0.zip",
      "sha256": "…64 lowercase hex characters…",
      "size": 12345,
      "platforms": ["macos-arm64", "linux-x86_64"],
      "plugin_spec": "1.2",
      "published": "2026-11-11"
    }
  ]
}
```

### The fields

| field | required | what it holds |
| --- | --- | --- |
| `id` | yes | the manifest's `id`, exactly; the file name is `<id>.json` |
| `name`, `summary` | yes | shown in the list; at most 80 and 200 characters |
| `description` | no | shown when the user opens the entry |
| `publisher.name`, `publisher.url` | name yes | who publishes it |
| `category` | yes | `docking`, `energy`, `structure-prediction`, `analysis`, `preparation`, `utility` or `example` |
| `license` | yes | the plugin's licence, as an SPDX id, or `proprietary` |
| `homepage`, `source_repository` | source yes | `https://` addresses a user can read |
| `status` | no | `active` (default) or `deprecated` |
| `network.setup` | yes | whether setting it up downloads anything |
| `network.runs` | yes | whether a **run sends any of the user's data** to a remote service |
| `network.note` | when `runs` is true | what is sent and where |
| `releases[].version` | yes | the manifest's `version`, exactly |
| `releases[].url` | yes | the package, as in step 2 |
| `releases[].sha256` | yes | of that exact file |
| `releases[].size` | no | in bytes |
| `releases[].platforms` | yes | `macos`, `macos-arm64`, `windows-x86_64`, `linux`, …; `[]` for any |
| `releases[].plugin_spec` | yes | the manifest's `spec_version` |
| `releases[].published` | yes | `YYYY-MM-DD` |

Some of these repeat what `plugin.json` says. They are here so EigenMol can
show the list without downloading every package, and they are **checked
against the package**: the automatic checks and EigenMol itself refuse a
package whose id or version differs from its entry.

EigenMol users choose plugins partly on `network`. A plugin that sends a
structure, a sequence or a result to a server must say so. Getting this wrong
is a reason to remove a listing.

## 4. Check it locally

```sh
python3 tools/catalog.py validate
python3 tools/catalog.py verify io.github.yourname.my-plugin
python3 tools/catalog.py build
```

`verify` downloads your package, compares its SHA-256 and reads `plugin.json`
from the ZIP without extracting or running anything. `build` rewrites
`index.json`; commit it with your entry.

## 5. Open the pull request

Fill in the template. The checks run on their own. A maintainer then reviews
the listing — see [MAINTAINING.md](MAINTAINING.md) for what they look at —
and may ask questions. Only after it is merged does the plugin appear in
EigenMol.

## Releasing a new version

Add an object to `releases` (keep the older ones unless they must not be
installed any more), run `build`, and open a pull request. EigenMol offers the
newest version that suits the user's computer, and shows **Update available**
to users who have an older one.

## Deprecating, withdrawing or removing

- **Deprecated**: set `"status": "deprecated"` and say why in `description`.
  It stays installable and is marked.
- **A version must not be installed** (a serious bug): remove it from
  `releases` in a pull request.
- **Removing the listing**: delete `plugins/<id>.json` and run `build`.
  Users who installed it keep their copy; it simply stops appearing in the
  list.

A maintainer may remove a listing without a request from the publisher when
its package disappears, its checksum stops matching, or it turns out to be
misleading or harmful.

## What listing does not change

- Users can install your plugin from its address or a ZIP whether or not it is
  listed.
- A listing is not an endorsement, an audit or a scientific validation.
- EigenMol installs it disabled and shows the program it will run before the
  user enables it, exactly as for any other plugin.

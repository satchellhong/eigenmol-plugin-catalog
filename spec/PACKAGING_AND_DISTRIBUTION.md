> **Public copy.** Generated from the documentation bundled with EigenMol
> (`tools/plugins/export_public_spec.py`); edit the source, not this copy.
> These documents describe the plugin interface EigenMol implements today and
> are published so a plugin can be written without EigenMol's source. Their
> licence is not chosen yet; until it is, they are published for reading and
> for writing plugins against.

# Packaging and distributing a plugin

How to turn a plugin folder into something anyone can install from your GitHub
repository or your own server. Nothing in this document depends on a central
registry or on any plugin other than yours.

## The package

A package is a ZIP of the plugin folder, the one holding `plugin.json`. The
installer accepts any of these layouts:

```text
x-1.0.0.zip                     x-1.0.0.zip                  repo-main.zip  (GitHub "Download ZIP")
└── x-1.0.0/                    ├── plugin.json              └── repo-main/
    ├── plugin.json             ├── my_plugin.py                 ├── README.md
    ├── my_plugin.py            └── setup/install.sh             └── plugin/
    └── setup/install.sh                                             ├── plugin.json
                                                                     └── …
```

- The manifest may sit at the top, inside one wrapping folder, or up to three
  levels down.
- A package holding **several** plugins is accepted, and the user chooses one.
  A link can also name it, as `…/tree/main/FOLDER`.
- **Executable bits** are kept: zip on macOS or Linux, or use
  `pdk/package_plugin.py`, which writes them explicitly.
- **Symbolic links** are kept only when they point inside the package. An
  absolute link, or one that leaves the package, refuses the whole archive.
- An entry that would unpack outside the folder (`../x`) refuses the archive.
- The limits are 2 GiB downloaded, 400 000 files, and 32 GiB unpacked. A plugin
  package should be a few megabytes: its engine and environment belong in
  setup.
- `.git/`, `__pycache__/` and `.DS_Store` are never copied into an install.

**Do not ship** a built environment (`env/`), a downloaded engine (`bin/`),
caches, test outputs, credentials, or anything whose licence does not allow
you to redistribute it.

## Building it

```text
python3 docs/plugins/pdk/package_plugin.py PLUGIN_FOLDER --name my-plugin --out dist
```

The script:

1. validates the manifest: JSON, id, a version equal to your adapter's
   `PLUGIN_VERSION`, protocol, and every file it names present unless setup
   creates it;
2. writes `dist/my-plugin-<version>.zip`, with fixed timestamps so the same
   source gives the same bytes;
3. writes `dist/my-plugin-<version>.zip.sha256`;
4. refuses a package over 20 MB.

Then install what you built, exactly as a user will:

```text
eigenmol-plugin-check dist/my-plugin-1.0.0.zip --install --setup
```

A package is ready to publish only when that passes. A ZIP being produced is
not enough.

## Publishing on GitHub

1. Tag the version (`v1.0.0`) and create a **release**.
2. Attach the ZIP **and** its `.sha256` as release assets.
3. Users paste `https://github.com/you/repo`. EigenMol lists your releases,
   recommends the newest non-pre-release one, downloads the ZIP and checks it
   against GitHub's own digest of the asset or your `.sha256`.

| What the user pastes | What EigenMol offers |
| --- | --- |
| `https://github.com/you/repo` | each release's ZIP assets (recommended first); a release without a ZIP as its source archive; tags without releases; the default branch head, as a development version |
| `…/releases/tag/v1.0.0` | that release |
| `…/releases/download/v1.0.0/x.zip` | that file |
| `…/tree/BRANCH` or `…/tree/BRANCH/FOLDER` | that branch, pinned to its current commit; a development version |

A development version is always labelled as one and needs the user's explicit
confirmation. Do not ask users to install from a branch for normal use;
publish a release.

**Private repositories** are reachable only by someone whose GitHub token, in
`EIGENMOL_GITHUB_TOKEN`, can read them. Their releases are not public
downloads.

## Publishing on your own server

Serve the files over **HTTPS**:

```text
https://lab.example.org/plugins/my-plugin-1.0.0.zip
https://lab.example.org/plugins/my-plugin-1.0.0.zip.sha256
```

Users paste the ZIP's address. EigenMol reads the `.sha256` beside it when
there is one and refuses a mismatch. Plain HTTP is refused, and so is a
redirect to HTTP. Redirects are followed up to 8 times. A server that
answers with a web page instead of the file is reported as "did not return a
ZIP".

An address does not say whether a newer version exists, so EigenMol cannot
check one for updates. Tell your users how to find new releases. Give each
version its own filename, rather than replacing the bytes at one address.

## Versions

| Number | Meaning | Who changes it |
| --- | --- | --- |
| `version` in `plugin.json` | your plugin | you, for every release |
| `PLUGIN_VERSION` reported in the handshake's `sdk` | the same number | you; the packager refuses a mismatch |
| `provenance.engine_version` in results | the engine you wrap (for example AutoDock Vina 1.2.7) | read from the engine at run time |
| `spec_version` | the specification you wrote against | you, when you use a newer field |
| `protocol` | the wire protocol, `1` | EigenMol |

A plugin version and an engine version are different facts. Never use one for
the other.

## Updates

For a plugin installed from GitHub, **Check for update** in the manager:

- compares the latest release's tag with the installed tag or version, or, for
  a development install, the branch's current commit with the installed one;
- downloads nothing, and runs nothing;
- when an update exists, opens the install dialog on your repository. The user
  approves it there like a first install, and a setup runs only when they
  press **Set up…**.

The replaced version is kept, and **Restore** puts it back.

## The install record

For every install EigenMol writes `plugins/.installs/<id>.json`:

- the plugin id and version, protocol and spec version, and platforms;
- the kind of source, the repository, the release tag, the commit, the asset;
- the URL without its query string;
- the package's SHA-256 and whether it matched a published checksum;
- when it was installed and by which EigenMol;
- whether it was copied or connected in place;
- the outcome of the last setup and the last check.

A plugin installed by an older EigenMol has no record. It still works, and
reads as "source not recorded".

## Licences

Your package is code you distribute, so its licence is yours to choose and
state. An engine you download at setup keeps its own licence. Name it in your
README and in `setup.description`. Downloading at install time avoids
redistributing the engine, but it does not remove the user's obligations under
the engine's licence, and it does not let you hide where the engine came
from. Model weights often carry a different licence from code.

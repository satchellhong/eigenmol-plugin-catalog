> **Public copy.** Generated from the documentation bundled with EigenMol
> (`tools/plugins/export_public_spec.py`); edit the source, not this copy.
> These documents describe the plugin interface EigenMol implements today and
> are published so a plugin can be written without EigenMol's source. Their
> licence is not chosen yet; until it is, they are published for reading and
> for writing plugins against.

# Installing a plugin

EigenMol does not contain docking engines or AI models. You connect the ones you
want through **plugins**: small adapters, usually published by someone else,
that let EigenMol run a program and read its results.

You do **not** need to install Python, conda, pip, RDKit or any developer tool.
A plugin that needs them brings or builds its own copy inside its own folder,
when you approve its setup.

## Open the installer

**Plugins ▸ Install a plugin…** opens one dialog for every kind of source. At
the top is a **Plugin address** field; below it are **Choose a .zip…** and
**Choose a folder…**. A row of stages shows where the install is:

`Source › Download › Validate › Approve › Install › Set up › Check › Ready`

A stage is a word, never a percentage. A download whose size is unknown shows a
moving bar.

## The five sources

### 1. A GitHub repository

Paste `https://github.com/OWNER/REPOSITORY` and press **Look up**.

- EigenMol asks GitHub's API what the repository offers.
- A **release** that has a `.zip` attached is listed first and marked
  *recommended*. That is a version its author published, and its checksum is
  shown when GitHub or the author states one.
- A release without an attached ZIP is offered as its **source archive**, the
  archive GitHub generates for the release's tag.
- The default branch is always offered last, as a **development version**. It
  is pinned to the commit EigenMol read, so the install can be repeated. It
  is not a published release and may not work, so you have to tick a
  confirmation before EigenMol downloads it.
- A link to `…/tree/BRANCH`, `…/tree/BRANCH/FOLDER` or `…/releases/tag/TAG`
  offers that branch, folder or release.
- If the repository holds several plugins, you choose one after the download.

Neither Git nor GitHub's command-line tool is needed.

**Private repositories.** Without a token, GitHub answers "not found" for a
private repository, and EigenMol says so in those words. EigenMol can read a
private repository when a GitHub token is in the `EIGENMOL_GITHUB_TOKEN`
environment variable of the EigenMol process. The token is sent only to
`api.github.com` and is never stored or shown. Without a token, download the
ZIP yourself and use **Choose a .zip…**.

**Rate limits.** GitHub allows a limited number of anonymous API requests per
hour. When the limit is reached, EigenMol says when it resets. A token raises
the limit, and a release-ZIP link avoids most API calls.

### 2. A GitHub release ZIP

Paste a link of the form
`https://github.com/OWNER/REPO/releases/download/TAG/FILE.zip`.

That file is downloaded as published. When GitHub states a digest for it, or
the release has a `FILE.zip.sha256` beside it, the download must match or
nothing is installed.

A release asset is not the same as GitHub's *Code ▸ Download ZIP*:

- a **release asset** is what the author packaged;
- a **Download ZIP** is the repository's source at one moment.

Both install. The release asset is the one meant for users.

### 3. Any HTTPS ZIP

Paste an `https://` address on any server, for example
`https://research-lab.example.org/downloads/my-plugin.zip`.

- EigenMol downloads it over HTTPS. It refuses plain `http://` and does not
  follow a redirect to `http://`.
- It checks that the file is a ZIP; a web page saved under a `.zip` name is
  refused.
- If the server offers `my-plugin.zip.sha256`, the download must match it.

An address can serve different bytes tomorrow, so EigenMol records the hash of
what it installed.

### 4. A ZIP on this computer

**Choose a .zip…**. It is installed exactly like a download, without the
download.

### 5. A folder on this computer

**Choose a folder…**. By default the folder is **copied** into EigenMol's
plugins folder, so later changes to your folder do not affect the installed
plugin.

If you are the plugin's **author**, tick *Developer: connect this folder in
place instead of copying*. EigenMol then runs your folder as it is, and your
edits take effect on the next run. A setup writes into your folder.
Uninstalling removes only the connection, never your folder. Developer links
work on macOS and Linux.

## Before anything is installed

The dialog shows:

- the plugin's name, version, author, licence and source;
- the program it will run, and whether that program is outside the plugin's
  folder;
- the platforms it supports. A plugin for another operating system or another
  processor (for example `macos-x86_64` on an Apple-silicon Mac) is refused
  before installing, with the reason;
- whether its setup downloads, how much, and how much disk it will use;
- what it needs and whether that is already there;
- what it adds to EigenMol;
- for a download: the package's SHA-256 and whether it matched a published
  checksum. A matching checksum says the bytes are the ones the publisher
  listed. It does not say who the publisher is.

Press **Install**. The plugin is copied into EigenMol's plugins folder and
starts **disabled**. If a plugin with the same id is installed, the button
reads **Replace 0.1.0 with 0.2.0**. The replaced version is kept, so you can
put it back. Installing an older version over a newer one is allowed and the
button says so: **Replace 0.3.0 with older 0.1.0**.

### A copy EigenMol has no record of

A plugin folder copied into the plugins folder by hand, or installed by an
EigenMol build that predates install records, has no record of where it came
from. Its card says so, in place of **Check for update**, and offers
**Replace with a package…**, which opens this same dialog. Install the
published package over it — a folder, a `.zip` or a release — and:

- the old copy moves aside, with whatever it built (its `env/`), and
  **Restore 0.1.0…** puts it back exactly;
- the new copy starts disabled and builds its **own** environment when you
  press **Set up…**; the old copy's environment is not reused;
- from then on the card knows the source, and **Check for update** works for
  a GitHub install.

Measured on 2026-11-10 with a replica of a hand-copied AutoDock Vina 0.1.0
(no record, no setup or check declared, a `venv` on the system's Python):
replacing it with the 0.3.0 snapshot and pressing **Set up…** took 2 min 39 s
(152 s of it the declared setup's downloads), the check passed, and docking
seven drugs into 1ACJ gave 19 poses identical in every column to the
verified run. The 0.1.0 copy, run the same way, completed 3 of 7 and failed
4 with `mapping_failed`; it gave no wrong numbers, only failures.

## Set it up and check it

**Plugins ▸ Manage plugins…** lists every plugin with one status word:

| Status | What to do |
| --- | --- |
| needs setup | press **Set up…**; the dialog shows exactly what will run and download |
| setup failed | read the log under the card, then **Set up…** again; finished steps are skipped |
| needs settings | open **Settings** and choose the file or folder it asks for |
| missing dependency | the card names what is missing and how to fix it |
| not checked | enable it, then press **Check** |
| check failed | the check's own report says which part is not ready |
| ready | it can run |
| unsupported platform | it was built for another system |

1. **Set up…** (only for plugins that declare a setup). Everything it builds
   stays inside the plugin's folder, and nothing else on your computer
   changes. **Stop** stops it.
2. Turn the plugin's **switch** on. A plugin is a program on your computer,
   running with your privileges, so enable only plugins you trust.
3. **Check** starts the plugin, confirms it speaks the protocol and runs its own
   readiness check.

Installing the files, setting up the dependencies and being able to compute
are three separate results. A plugin is *ready* only after its setup and its
check passed. Being ready does not mean it can compute every molecule: an
engine may still refuse a particular input, and says why.

Each card also says where the plugin came from: the repository and release, or
the file. For a plugin installed from GitHub, **Check for update** asks the
repository. It downloads nothing; an available update is installed through the
same dialog, with the same approval. **Restore 0.1.0…** puts back the version an
upgrade replaced.

## Use it

| The plugin does | Where it appears |
| --- | --- |
| docking | **Dock…** in the toolbar and an object's menu; an **Engine** choice in **Screening** |
| structure prediction | an object's **More actions** menu; the predicted complex arrives as a new object |
| analysis or energy | the Inspector's **COMPUTE** section and the right-click menu |

A plugin whose results are test data says so on every control (*Generate test
poses…*), and Screening never picks it by default.

A docking score is the engine's own ranking value. EigenMol shows the engine
and the score type with every number and never presents a score as a binding
affinity.

## Remove it

**Manage plugins… ▸ Uninstall…** removes the plugin's folder, everything its
setup built, its settings and its install record. The ZIP or folder you
installed it from is not touched.

## Where things are

| | macOS and Linux | Windows |
| --- | --- | --- |
| installed plugins | `~/.aigenmol/plugins/` | `%USERPROFILE%\.aigenmol\plugins\` |
| install records | `…/plugins/.installs/` | same |
| a replaced version | `…/plugins/.previous/` | same |
| downloads in progress | `…/plugins/.downloads/` (removed after install) | same |

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) when something goes wrong.

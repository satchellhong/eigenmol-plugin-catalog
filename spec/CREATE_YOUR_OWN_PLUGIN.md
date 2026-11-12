> **Public copy.** Generated from the documentation bundled with EigenMol
> (`tools/plugins/export_public_spec.py`); edit the source, not this copy.
> These documents describe the plugin interface EigenMol implements today and
> are published so a plugin can be written without EigenMol's source. Their
> licence is not chosen yet; until it is, they are published for reading and
> for writing plugins against.

# Create your own plugin

This guide takes you from an empty folder to a plugin anyone can install from
your GitHub repository or your own server. It uses only this folder:

- the specification, [PLUGIN_SPECIFICATION.md](PLUGIN_SPECIFICATION.md);
- the starter template, [`templates/python-minimal/`](templates/python-minimal/);
- the packager, [`pdk/package_plugin.py`](pdk/package_plugin.py);
- the compatibility harness, `eigenmol-plugin-check` (or **Plugins ▸ Create your
  own plugin ▸ Test a plugin folder…** in the app).

No other plugin's source is needed. Python is used for the examples. A plugin
may be written in any language that can read and write JSON on stdin and
stdout: Rust, C++, Go, a shell script calling a binary, or a small client for a
remote service.

## 1. Create the repository

```text
my-eigenmol-plugin/
├── plugin/                ← the package: exactly what users install
│   ├── plugin.json
│   ├── my_plugin.py
│   └── setup/install.sh   ← only if you have dependencies (step 7)
├── tests/
├── README.md
└── .gitignore             ← env/, bin/, .tools/, dist/, __pycache__/
```

Keeping the package in `plugin/` keeps tests, documentation and CI out of what
users install. EigenMol finds the manifest inside a repository archive, so a
repository URL still installs.

Copy `templates/python-minimal/` into `plugin/` to start.

## 2. Write the manifest

`plugin.json` (spec §4):

```json
{
  "id": "org.yourlab.myplugin",
  "name": "My plugin",
  "version": "0.1.0",
  "spec_version": "1.2",
  "protocol": 1,
  "runtime": "process",
  "entrypoint": "/usr/bin/env",
  "args": ["python3", "my_plugin.py"],
  "description": "One sentence a user can judge.",
  "author": "Your name",
  "license": "The licence you chose",
  "source": "https://github.com/yourlab/my-eigenmol-plugin",
  "platforms": ["macos", "linux"],
  "capabilities": ["read_current_structure", "create_result"],
  "actions": [ … ]
}
```

- `id` is reverse-domain, lowercase, and **never changes**: EigenMol keys
  enablement, settings and install records on it.
- `version` is your plugin's version. It is not your engine's version.
- `platforms` names what you have tested: `macos`, `windows`, `linux`,
  optionally with a processor (`macos-arm64`, `linux-x86_64`). EigenMol refuses
  the install anywhere else, before copying a file.

## 3. Declare your actions

Each action says where it belongs and what it exchanges (spec §4, "Action
fields"):

| You want | `extension_point` | `inputs` | `results` |
| --- | --- | --- | --- |
| an analysis of the open structure | `analysis_action` | `["current_structure"]` | `table`, `atom_scalar`, `residue_scalar`, `metadata`, `overlay` |
| docking | `structure_generator` | `["current_structure", "ligand"]` | `pose_set` |
| an energy of a receptor and a ligand | `structure_generator` | `["current_structure", "ligand"]` | `energy_result` |
| a predicted complex | `structure_generator` | `["current_structure"]` | `structure` |

An action whose results are test data rather than a calculation **must**
declare `"synthetic": true`. EigenMol then labels it a test fixture everywhere.

## 4. Read the input

Your program reads framed JSON on stdin (spec §6). The template's
`read_message` and `write_message` are the whole transport; keep them.

- A structure action receives one snapshot (spec §8): `identity.object`, and
  `atoms` with chain, residue number, atom name, element, position and formal
  charge.
- A docking-shaped action receives `protein`, `ligand`, `site` and
  `parameters`.
- Answer **by name** (object handle, chain, residue number, atom name), never
  by an index of your own.

## 5. Connect your engine

Replace the template's `count_atoms` with your computation. For an external
program:

1. Write the program's input files into a temporary directory from the
   snapshot.
2. Run the program as a subprocess, with an argument list rather than a shell
   string.
3. Read its output.
4. Return results.

If the program is missing, return error `engine_missing`. If it ran and
failed, return `calculation_failed` with a sentence the user can act on.
Never fall back to made-up values.

## 6. Return typed results

Every result has a `type` and `provenance.method` (spec §9). Rules a validator
enforces:

- a number states its **unit** and, for scientific values, a **quantity key**
  in your own namespace (`org.yourlab.myplugin.*`);
- a docking score has a `score_type`, and a made-up value is unitless;
- `"unavailable": "reason"` is different from `0`, and absence is a third
  answer;
- every reference must resolve, or the whole response is refused.

## 7. Setup: install your dependencies automatically

If your plugin needs anything beyond what the platform guarantees (a Python
package, an engine binary, model weights), declare `requirements` and `setup`.
Users then press **Set up…** instead of reading instructions. This is the
difference between a plugin and a script.

[AUTOMATIC_DEPENDENCIES.md](AUTOMATIC_DEPENDENCIES.md) is the contract, with
patterns for:

- a private Python;
- a downloaded binary;
- model weights;
- no dependencies at all.

[`templates/python-with-setup/`](templates/python-with-setup/) is a working
starting point. A plugin with no dependencies declares no setup.

## 8. Health check

Declare `check` and print one JSON readiness object (spec §12). A good check
does what the calculation needs, on a tiny input: imports the libraries, runs
the engine's `--version`, loads a parameter file. A check that only looks for
files says "ready" for a broken install.

## 9. Test compatibility

```text
eigenmol-plugin-check plugin/                   # the folder as it is
eigenmol-plugin-check plugin/ --install         # through the real installer
eigenmol-plugin-check dist/x-0.1.0.zip --install --setup   # the package, setup included
```

The harness:

1. validates the manifest;
2. looks for every requirement;
3. starts the program and completes the handshake;
4. sends each analysis and docking action a request about a small committed
   structure;
5. validates every result with the installer's own validators.

`--install` copies into a throw-away plugins folder first. `--setup` also runs
your setup there; asking for it is your consent to run it. Your own EigenMol
installation is never touched. The same test is in the app under **Test a
plugin folder…**.

Passing the harness shows that the plugin is installable and speaks the
protocol. It does not show that your calculation is right. Check that with real
inputs and an independent reference.

## 10. Build the ZIP

```text
python3 pdk/package_plugin.py plugin --name my-eigenmol-plugin --out dist
```

This writes `dist/my-eigenmol-plugin-0.1.0.zip` and its `.sha256`. The archive
contains one folder, `my-eigenmol-plugin-0.1.0/`, holding your package. It
never includes `env/`, `bin/`, caches or anything over 20 MB. Install the ZIP
you built with `--install` before publishing it.

## 11. Publish a GitHub release

Create a release whose tag is your version (`v0.1.0`) and attach both the
`.zip` and the `.zip.sha256`. Users paste your repository URL. EigenMol
recommends the release, checks the ZIP against your `.sha256`, and records the
tag. A repository with no release still installs, but only as a development
version that users must confirm.

## 12. Publish on your own server

Serve the ZIP over **HTTPS**, with the `.sha256` beside it at the same address
plus `.sha256`. Users paste the ZIP's URL. Nothing about this route depends on
GitHub. See [PACKAGING_AND_DISTRIBUTION.md](PACKAGING_AND_DISTRIBUTION.md).

## 13. Versions

- Raise `version` for every release, in `plugin.json` and in the version your
  handshake reports.
- Keep your engine's version in `provenance.engine_version`, not in your plugin
  version.
- Keep `id` unchanged forever.

## 14. Updates and recovery

A user who installed from your GitHub repository can press **Check for update**.
EigenMol compares your latest release with what they have. Installing it goes
through the same inspection and consent. The version it replaces is kept, and
**Restore** puts it back if the new one does not work for them. Make your setup
re-runnable, so that a failed setup is fixed by running it again.

## Checklist

- [ ] `id` is yours and final; `version` matches what the handshake reports
- [ ] `platforms` lists only what you tested
- [ ] every action that returns test data is `"synthetic": true`
- [ ] results carry units, quantity keys and provenance; nothing is invented
- [ ] dependencies come from a declared, checksummed `setup`
- [ ] `check` exercises the real calculation path on a tiny input
- [ ] `eigenmol-plugin-check dist/<zip> --install --setup` passes on a clean machine
- [ ] the README names your engine, its licence, what setup downloads, and the platforms
- [ ] the release has the ZIP and its `.sha256`

> **Public copy.** Generated from the documentation bundled with EigenMol
> (`tools/plugins/export_public_spec.py`); edit the source, not this copy.
> These documents describe the plugin interface EigenMol implements today and
> are published so a plugin can be written without EigenMol's source. Their
> licence is not chosen yet; until it is, they are published for reading and
> for writing plugins against.

# EigenMol Plugin Specification

**Version 1.2** · wire protocol **1** · applies to EigenMol builds that report
`plugin_spec_version() == "1.2"`.

This is the contract between EigenMol and a program someone else wrote. A
developer who follows it can connect a docking engine, a structure-prediction
model or their own calculation to EigenMol **without reading EigenMol's source
and without EigenMol changing**. The compatibility test
(`eigenmol-plugin-check`, or *Plugins ▸ Create your own plugin ▸ Test a plugin
folder…* in the app) checks a plugin against exactly this document, using the
same validators the app uses.

A step-by-step tutorial is [`CREATE_YOUR_OWN_PLUGIN.md`](CREATE_YOUR_OWN_PLUGIN.md).
How a user installs a plugin is [`INSTALLING_PLUGINS.md`](INSTALLING_PLUGINS.md).

---

## Contents

1. [What a plugin is for](#1-what-a-plugin-is-for)
2. [Who does what](#2-who-does-what)
3. [The plugin folder](#3-the-plugin-folder)
4. [The manifest, `plugin.json`](#4-the-manifest-pluginjson)
5. [How EigenMol starts your program](#5-how-eigenmol-starts-your-program)
6. [The transport](#6-the-transport)
7. [The conversation](#7-the-conversation)
8. [Inputs: a structure, or a docking request](#8-inputs)
9. [Results](#9-results)
10. [Scores, quantities, units and provenance](#10-scores-quantities-units-and-provenance)
11. [Errors and what the user sees](#11-errors-and-what-the-user-sees)
12. [Setup, check, settings and requirements](#12-setup-check-settings-and-requirements)
13. [Platforms and dependencies](#13-platforms-and-dependencies)
14. [Versions and compatibility](#14-versions-and-compatibility)
15. [Packaging and distributing a plugin](#15-packaging-and-distributing-a-plugin)
16. [The trust model](#16-the-trust-model)
17. [Limits](#17-limits)
18. [Install records, status and updates](#18-install-records-status-and-updates-12)

Companion documents, part of this standard: [AUTOMATIC_DEPENDENCIES.md](AUTOMATIC_DEPENDENCIES.md),
[PACKAGING_AND_DISTRIBUTION.md](PACKAGING_AND_DISTRIBUTION.md),
[SECURITY_AND_TRUST.md](SECURITY_AND_TRUST.md), [TROUBLESHOOTING.md](TROUBLESHOOTING.md),
[AI_CODING_AGENTS.md](AI_CODING_AGENTS.md). Starter templates are in [`templates/`](templates/),
the packager in [`pdk/`](pdk/).

---

## 1. What a plugin is for

A plugin is an **external program** that EigenMol starts on the user's
machine, hands a molecular structure or a docking request to, and receives
**typed scientific results** from:

| a plugin can return | what EigenMol does with it |
| --- | --- |
| `pose_set` — poses of a ligand, with scores | the Pose Browser, the Screening table, the Native Interaction Analyzer, 3D evidence |
| `structure` — a new complex (a co-folding prediction, a refined model) | a new object, parsed by EigenMol's own parsers; ligand, pocket and interaction analysis work on it |
| `atom_scalar`, `residue_scalar` | colour-by, the Results panel, the Inspector |
| `table` | the Results panel, sortable, exportable |
| `energy_result` | a total, its terms and a per-residue decomposition |
| `overlay` | lines, arrows, markers and labels drawn by EigenMol's renderer |
| `metadata` | notes about a run, shown beside it |

**A plugin computes. EigenMol interprets and visualises.** A plugin never
draws, never touches the scene, never sees a GPU resource and never edits the
user's molecule. That is what lets one Native Interaction Analyzer, one
Screening table and one 3D viewer read every engine's output the same way.

Typical plugins: AutoDock Vina, Uni-Dock, DiffDock, a Boltz-family co-folding
model, an MM/GBSA workflow, a group's in-house scoring program. None of them is
built into EigenMol; each is a plugin.

## 2. Who does what

| the plugin | EigenMol |
| --- | --- |
| prepares inputs for its engine (PDBQT, protonation, charges, box padding) | publishes the structure exactly as the file stated it |
| runs the engine, on CPU or GPU | starts and stops the plugin's process, as one process group |
| converts the engine's output into this specification's result types | validates every result before anything is installed, all or nothing |
| names its scores, units and method | shows them with that name and never as an experimental affinity |
| brings or builds its own environment (Python, CUDA, weights) | runs nothing until the user enables the plugin |
| decides its own licence | does not manage licences, keys or payment |

EigenMol does **not** add hydrogens, perceive aromaticity, kekulize, assign
protonation or generate conformers for a plugin. If your engine needs any of
that, your plugin does it — and records what it did in the result's
parameters, because a step that changes the chemistry is part of what the
number means.

## 3. The plugin folder

The examples in this document use **MyDock**, an imaginary docking program,
so every field can be shown in one consistent example. Nothing here requires
reading any real plugin. A complete working plugin written from this document
alone is [`templates/python-minimal/`](templates/python-minimal/).

```text
org.example.mydock/            any folder name; the id is in the manifest
├── plugin.json                the manifest (required)
├── mydock_plugin.py           your program, or a launcher for it
├── engine/                    anything else you ship
├── setup/install.sh           optional: builds a private environment
└── check.py                   optional: reports readiness
```

Installed plugins live in `~/.aigenmol/plugins/` (one folder each). Users never
put them there by hand; *Plugins ▸ Install an existing plugin* copies a folder
or a `.zip` into place. An archive may nest the folder one or two levels deep
(GitHub's *Download ZIP* produces `name-main/`); the installer finds the one
`plugin.json`. An archive holding several plugins is refused with their
locations.

## 4. The manifest, `plugin.json`

JSON, UTF-8. Unknown keys are ignored, so a manifest written for a later
specification still loads.

```json
{
  "id": "org.example.mydock",
  "name": "MyDock",
  "version": "1.0.0",
  "spec_version": "1.1",
  "protocol": 1,
  "runtime": "process",
  "entrypoint": "mydock_plugin.py",
  "args": [],
  "description": "Docks ligands with MyDock.",
  "author": "Example Lab",
  "homepage": "https://example.org/mydock",
  "license": "Apache-2.0",
  "source": "https://github.com/example/eigenmol-mydock",
  "platforms": ["macos", "linux"],
  "capabilities": ["read_current_structure", "create_result"],
  "settings": [ … §12 … ],
  "requirements": [ … §12 … ],
  "setup": { … §12 … },
  "check": { … §12 … },
  "system": { "gpu": "optional", "memory_gb": 8, "notes": "…" },
  "actions": [
    {
      "id": "mydock_dock",
      "name": "Dock with MyDock",
      "extension_point": "structure_generator",
      "inputs": ["current_structure", "ligand"],
      "results": ["pose_set"],
      "timeout_seconds": 3600,
      "synthetic": false,
      "coordinate_dependent": true
    }
  ]
}
```

### Top-level fields

| field | required | rule |
| --- | --- | --- |
| `id` | yes | reverse-DNS, lowercase, `[a-z0-9._-]`, at least one dot, no leading, trailing or double dot, ≤ 128 characters. **Stable across versions**; it is the plugin's identity, not the folder name |
| `name` | yes | what the user reads |
| `version` | yes | three numbers, `1.0.0`; `-pre` and `+build` suffixes allowed |
| `protocol` | yes | the wire protocol you speak. This build speaks `1` |
| `runtime` | yes | `process`. (`python` is recognised and refused; a Python plugin is a `process` whose entrypoint is an interpreter — §13) |
| `entrypoint` | yes | the program EigenMol launches: a path **inside** the plugin folder, or an **absolute** path (shown to the user as outside the folder). A relative path that leaves the folder is refused |
| `args` | no | fixed arguments |
| `spec_version` | no | `"1.1"`. Absent means `1.0`. A newer major version is refused; a newer minor version is a warning |
| `description`, `author`, `homepage`, `license`, `source` | no | shown in the installer and the manager |
| `platforms` | no | `macos`, `windows`, `linux`. Absent means any. A plugin for another platform is refused at install with the reason |
| `capabilities` | no | disclosed to the user before anything runs. Known: `read_current_structure`, `read_current_selection`, `read_all_structures`, `create_result`, `create_overlay`, `create_structure`, `network`, `gpu`. **An unknown capability makes the manifest invalid** |
| `settings`, `requirements`, `setup`, `check`, `system` | no | §12 |
| `actions` | no | what the plugin can do |

### Action fields

| field | rule |
| --- | --- |
| `id` | unique within the plugin; arrives in `invoke` |
| `name` | the menu label |
| `extension_point` | where the action appears (table below). An unknown one disables **that action** with a reason; the rest of the plugin works |
| `inputs` | `current_structure`, `current_selection`, `picked_entity`, `ligand`. An unknown one disables the action |
| `results` | the types you may return (§9). An unknown one disables the action |
| `timeout_seconds` | per action; default 300, clamped to 24 h |
| `synthetic` | `true` when the action produces **test data rather than a calculation**. The app then says so on every control (*Generate test poses…*, not *Dock…*) and never defaults to it in a screening |
| `coordinate_dependent` | default `true`: the result read the geometry and is discarded if the coordinates change while you run. `false` for a property of the molecule |

### Where an action appears

| declaration | offered as |
| --- | --- |
| `structure_generator` + `pose_set` in results + `ligand` in inputs | **docking**: *Dock…* in the toolbar, the object menu, the context menu, and an engine choice in *Screening* |
| `structure_generator` + `structure` in results | **structure prediction**: *More actions* of the object; the returned complex arrives as a new object |
| `analysis_action`, `context_menu_action` | *More actions* and the viewport context menu, run on the selected object |
| other known extension points | listed by the manager; not placed in a menu by this build |

All three docking declarations are needed. A generator that returns poses for a
single structure is legitimate, and would fail if sent a two-object docking
request.

## 5. How EigenMol starts your program

- One process per invocation: start, handshake, invoke, stop. There is no
  long-lived server.
- **Working directory**: the plugin folder.
- **Command**: the resolved `entrypoint` and `args`. No shell is involved; no
  part of the manifest is interpreted as a command line.
- **Environment**: inherited (so `PATH` and library paths work), plus:

| variable | value |
| --- | --- |
| `AIGENMOL_PLUGIN_PROTOCOL` | `1` |
| `AIGENMOL_PLUGIN_HOST` | `EigenMol` |
| `EIGENMOL_PLUGIN_DIR` | the absolute plugin folder |
| `EIGENMOL_PLUGIN_ID` | the manifest id |
| `EIGENMOL_PLATFORM` | `macos`, `windows` or `linux` |
| `EIGENMOL_ARCH` | `arm64` or `x86_64` (1.2) |
| `EIGENMOL_SPEC_VERSION` | `1.2` |
| `EIGENMOL_SETTING_<KEY>` | each declared setting's value (key upper-cased), or its default |

- **Process group**: your process and anything it starts are one group (one job
  object on Windows). *Stop* signals the group, then terminates it after a
  grace period.
- One plugin process runs at a time across the application, screening jobs
  included.

## 6. The transport

stdin and stdout, one JSON object per message, each with a length header:

```text
Content-Length: 71\r\n
\r\n
{"protocol":1,"kind":"response","id":"req-1","result":{"results":[]}}
```

- **stdout carries protocol messages and nothing else.** One stray `print`
  is a protocol violation, reported to the user with your line quoted. Log to
  **stderr**; it is captured (up to 256 KiB) and shown as expandable detail.
- `Content-Length` is the byte length of the UTF-8 body. Unknown headers are
  ignored. The header block is at most 8 KiB.
- A message over **32 MiB** is refused before it is read.

## 7. The conversation

Every message has `protocol` (1) and `kind` (`request`, `response`, `event`).

### Handshake — within 10 seconds

```json
{ "protocol": 1, "kind": "request", "id": "hs-1", "method": "handshake",
  "params": { "host": "EigenMol", "host_version": "0.1.0",
              "protocol_versions": [1],
              "capabilities_granted": ["read_current_structure", "create_result"] } }
```

```json
{ "protocol": 1, "kind": "response", "id": "hs-1",
  "result": { "protocol": 1, "sdk": "mydock/1.0.0",
              "actions": ["mydock_dock"], "concurrent_requests": 1 } }
```

Answer immediately; load models later. Every action the manifest declares must
be in `actions`, or EigenMol refuses to invoke it (`unsupported_action`).

### Invoke

```json
{ "protocol": 1, "kind": "request", "id": "req-1", "method": "invoke",
  "params": { "action": "mydock_dock", "inputs": { … §8 … }, "parameters": null } }
```

Answer with the **same id**:

```json
{ "protocol": 1, "kind": "response", "id": "req-1",
  "result": { "results": [ { "type": "pose_set", … } ] } }
```

or with an error (§11):

```json
{ "protocol": 1, "kind": "response", "id": "req-1",
  "error": { "code": "engine_missing", "message": "MyDock is not installed.",
             "detail": "looked in /opt/mydock/bin" } }
```

### Progress — optional, recommended for anything slow

```json
{ "protocol": 1, "kind": "event", "id": "req-1", "event": "progress",
  "params": { "fraction": 0.4, "stage": "scoring pose 4 of 10" } }
```

### Cancel

```json
{ "protocol": 1, "kind": "request", "id": "cancel-1", "method": "cancel",
  "params": { "request": "req-1" } }
```

Stop and exit. EigenMol does not wait: it stops reading your results at once
and terminates the process group after 1.5 s. A cancelled request never changes
the scene.

### End of input

When stdin closes, exit.

## 8. Inputs

### A structure (every action without the `ligand` input)

`params.inputs` is an immutable snapshot:

```json
{
  "identity": { "object": "obj-1", "object_name": "1acj",
                "topology": "2f1a…", "coordinates": "9c3b…" },
  "atom_count": 4192, "residue_count": 616, "chains": ["A"],
  "atoms": [
    { "chain": "A", "residue_number": 84, "insertion": "A", "residue_name": "TRP",
      "atom": "NE1", "element": "N", "position": [2.1, 63.4, 66.8],
      "formal_charge": 0, "alt_loc": "A", "hetero": false }
  ],
  "bonds": [ { "a": 0, "b": 1, "order": "single", "stated": true } ],
  "selection": [12, 13, 14],
  "inline": true
}
```

| field | meaning |
| --- | --- |
| `identity.object` | the handle every reference you return must echo |
| `identity.topology`, `coordinates` | EigenMol's staleness fingerprints; do not interpret them |
| `atoms[].atom` | the atom name as the file wrote it — the key you answer with |
| `insertion`, `alt_loc`, `formal_charge`, `hetero` | present only when meaningful |
| `bonds[].a`, `.b` | positions in **this message's** `atoms`; never an identity you return |
| `bonds[].order` | `single`, `double`, `triple`, `aromatic` or `unknown`. PDB and mmCIF input usually has **no bond orders** |
| `bonds[].stated` | whether the file stated the bond; `false` means it was inferred from distance |
| `selection` | positions in `atoms` the user had selected |

### A docking request (an action with the `ligand` input)

```jsonc
{
  "protein": { /* a structure snapshot, as above */ },
  "ligand":  { /* a structure snapshot of only the ligand's atoms */ },
  "site": { "kind": "centre_and_box", "centre": [5.1, 66.2, 61.0], "size": [22, 22, 22] },
  "parameters": { "pose_count": 9, "seed": 42, "flexible_ligand": true,
                  "extra": [["exhaustiveness", "16"]] }
}
```

`site.kind` is one of:

| kind | fields |
| --- | --- |
| `ligand_neighbourhood` | `ligand` (a residue reference), `radius` (Å), `residues` (resolved by EigenMol) |
| `selected_residues` | `residues` |
| `current_selection` | `residues`, `atom_count` |
| `centre_and_box` | `centre`, `size` (full extents, Å) |
| `explicit_coordinates` | `points`, `note` |

**Match on the word.** If your engine supports only some kinds, refuse the
others with `unsupported_site` and a sentence; do not convert one into another,
because the padding you would invent is a scientific choice.

`parameters` fields are optional. `extra` is a list of `[key, value]` text
pairs the user set; EigenMol forwards them without reading them.

When the ligand is a residue inside the receptor's object (a PDB entry holding
both), the `protein` snapshot **omits the ligand's atoms**. Waters, ions,
cofactors and other ligands stay in it; whether your engine uses them is your
decision. A ligand with a **stated** covalent bond to the receptor is refused
before your program starts.

## 9. Results

References to atoms and residues use the names the input used, never an index:

```json
{ "object": "obj-1", "chain": "A", "residue": { "number": 84, "insertion": "A" }, "atom": "NE1" }
```

A reference that does not resolve refuses the whole response, with a count.
**Every result in a response is validated before any is installed**: one bad
result leaves the user's scene exactly as it was.

### `pose_set`

```json
{
  "type": "pose_set",
  "name": "MyDock poses",
  "protein": "obj-1",
  "ligand": "obj-2",
  "provenance": { "method": "MyDock rigid-receptor docking", "engine": "MyDock",
                  "engine_version": "2.3.1", "parameter_set": "exhaustiveness 16" },
  "parameters": [["seed", "42"], ["box_size", "22 x 22 x 22"]],
  "poses": [
    { "id": "pose-1", "name": "Pose 1", "rank": 1,
      "score": -9.8, "score_type": "MyDock score", "score_unit": "kcal/mol",
      "confidence": 0.82,
      "coordinates": [[1.0, 2.0, 3.0]] }
  ]
}
```

1. **One coordinate per atom of `ligand.atoms`, in that order.** EigenMol maps
   them onto its own topology by identity and refuses another count.
2. **A `score` needs a `score_type`.** A bare number reads as a measurement.
3. **Echo the object references** you were given (`protein`, `ligand`).
4. `parameters` is a **list of `[key, value]` text pairs**, in the order you
   want them shown. It is the engine's preparation record (atom typing, torsions,
   what was removed) and is shown beside the poses.
5. `confidence`, when present, is a fraction in [0, 1] and is kept **separate**
   from the score.

A set of one pose is an ordinary result.

### `structure`

What a co-folding or refinement model returns: a new complex.

```json
{
  "type": "structure",
  "name": "Predicted complex",
  "format": "pdb",
  "data": "ATOM      1  N   MET A   1 …\nEND\n",
  "provenance": { "method": "co-folding prediction", "engine": "MyFold", "engine_version": "1.0" }
}
```

`format` is `pdb`, `mmcif` or `sdf`. EigenMol parses `data` with **its own
parsers** — the ones that open a file — and adds each structure as a new object.
Nothing already open moves. The returned text is kept as a file under
`~/.aigenmol/generated/<plugin id>/` so sessions and projects save and reopen it
like any structure. `provenance.method` is required. A prediction's confidence
belongs in a `residue_scalar` or `atom_scalar` alongside it, with its own
quantity.

### `atom_scalar`, `residue_scalar`

```json
{
  "type": "residue_scalar",
  "name": "Per-residue score",
  "unit": "kcal/mol",
  "quantity": { "key": "org.example.mydock.residue_score", "label": "MyDock residue score" },
  "provenance": { "method": "MyDock per-residue decomposition" },
  "values": [
    { "object": "obj-1", "chain": "A", "residue": { "number": 84 }, "value": -1.2 },
    { "object": "obj-1", "chain": "A", "residue": { "number": 85 }, "unavailable": "no parameters" }
  ]
}
```

`atom_scalar` is the same with `"atom": "…"` in each value. Each value is
**either** `value` **or** `unavailable` with a reason.

### `table`

```json
{
  "type": "table", "name": "Per-pose terms",
  "provenance": { "method": "MyDock" },
  "columns": [
    { "name": "Residue", "kind": "text" },
    { "name": "Term", "kind": "number", "unit": "kcal/mol",
      "quantity": { "key": "org.example.mydock.term", "label": "Term" } },
    { "name": "Interface", "kind": "flag" }
  ],
  "rows": [
    { "cells": ["ASP84", -3.8, true],
      "residue": { "object": "obj-1", "chain": "A", "residue": { "number": 84 } } }
  ]
}
```

`kind` is `text`, `number` or `flag`. `null` is an empty cell, never a zero.

### `energy_result`

```json
{
  "type": "energy_result", "name": "Interaction estimate", "unit": "kcal/mol",
  "total": -42.3, "uncertainty": 1.1,
  "total_quantity": { "key": "org.example.estimate", "label": "Interaction estimate" },
  "residue_quantity": { "key": "org.example.per_residue", "label": "Per-residue term" },
  "provenance": { "method": "…", "engine": "…", "protocol": "one snapshot; entropy not evaluated" },
  "components": [ { "name": "van der Waals", "value": -32.1,
                    "quantity": { "key": "aigenmol.energy.vdw", "label": "van der Waals" } } ],
  "residues": [ { "object": "obj-1", "chain": "A", "residue": { "number": 84 }, "value": -3.8 } ]
}
```

EigenMol does not sum your components into a total.

### `overlay`

Six shapes — `line`, `dashed_line`, `point`, `marker`, `arrow`, `label` —
anchored to an atom (`{"kind": "atom", …reference…}`, follows the atom) or an
absolute point (`{"kind": "absolute", "point": [x, y, z]}`). Optional
`"scope": {"kind": "pose", "pose_set": 0, "pose_index": 2}` ties an overlay to
one pose of a `pose_set` in the same response (indices into your response).
Width 0.5–24 px, labels ≤ 64 characters, ≤ 2 000 overlays. Drawn by EigenMol,
attributed to your plugin.

### `metadata`

```json
{ "type": "metadata", "name": "Run settings", "provenance": { "method": "MyDock" },
  "entries": [ { "key": "exhaustiveness", "value": 8 }, { "key": "box", "value": "22 Å" } ] }
```

Notes, not measurements: values are shown as the text they say. ≤ 256 entries.

### Not accepted

`pose` (return a `pose_set`), `color_mapping`, `selection`, `scalar_field`,
`surface_request`, `residue_contribution` (use `energy_result`) and
`interaction_profile`. The last is refused permanently: an interaction profile
is what EigenMol's own analyzer concluded, and your findings must not appear as
its findings. Report interactions as a `table` or an `overlay`.

## 10. Scores, quantities, units and provenance

### A score is the engine's, and says so

A docking score is an engine-specific screening and ranking value. EigenMol
shows it with its `score_type`, its unit and its engine — `-9.80 kcal/mol ·
MyDock score` — and never as a Kd, Ki, IC50 or binding free energy. **Two
engines' scores are different quantities even in the same unit**: the
Screening table keeps one score context per receptor, engine, site and score
type, never ranks across contexts, and a score filter has to name the context
it is about.

A value you derived without computing anything (a test fixture) is
**unitless**: a reader believes a unit over the words beside it.

### Quantities

A numeric result states a `quantity` with a stable `key` (lowercase dotted
segments, your own namespace such as `org.example.mydock.*`; `aigenmol.*` is
reserved for keys EigenMol defines) and a human `label`. A label alone does not
create an identity.

### Units

Recognised: `""`/`unitless`, `A`/`angstrom`, `kcal/mol`, `fraction`, `%`,
`e`. Anything else is kept verbatim. Send the unit you computed in.

### Zero, unavailable and absent

| you send | it means |
| --- | --- |
| `"value": 0.0` | evaluated, and zero — a finding |
| `"unavailable": "reason"` | evaluated, could not answer — the reason is required |
| no entry | no claim |

### Provenance

`method` is required; `engine`, `engine_version`, `protocol`, `parameter_set`
and `parameters` (`[[key, value], …]`) are shown when present. Your engine name
is stored and displayed and **never branched on** by EigenMol. You cannot set
the producer: the plugin id and version EigenMol launched are recorded by the
host.

## 11. Errors and what the user sees

An error is `{"code", "message", "detail"?}`. `message` is the sentence the
user reads; put tracebacks in `detail` or stderr.

### Codes with an agreed meaning

| code | meaning | effect in a screening run |
| --- | --- | --- |
| `engine_missing` | the engine is not installed or not found | stops the run: no later job can succeed |
| `dependency_missing` | a library or model file is missing | stops the run |
| `version_mismatch` | the engine's version is not one this plugin supports | stops the run |
| `invalid_input` | this request cannot be computed (no ligand, empty site) | this job fails, the run continues |
| `unsupported_site` | the binding-site kind is not one the engine takes | this job fails |
| `calculation_failed` | the engine ran and did not finish | this job fails |
| anything else | your own code, shown as given | this job fails |

### What EigenMol reports on its own

`spawn_failed` (program missing or not executable), `handshake_timeout`,
`bad_handshake`, `unsupported_protocol`, `unsupported_action`,
`protocol_violation` (anything on stdout that is not a frame), `premature_end`
(exited before answering), `timeout`, `cancelled`, `correlation_error` (wrong
id), `malformed_response`. `spawn_failed`, `bad_handshake`,
`handshake_timeout` and `unsupported_action` also stop a screening run.

### States a user sees for a plugin

| state | meaning |
| --- | --- |
| **failed** | the manifest is invalid; the reason is shown; no switch |
| **disabled** | installed, valid, not allowed to run (every new install starts here) |
| **enabled** | allowed to run |
| readiness **ready** | every declared requirement is in place |
| readiness **needs setup** | a requirement is missing and a setup is declared |
| readiness **needs settings** | a setting must name something |
| readiness **not ready** | something is missing; each item says what to do |

## 12. Setup, check, settings and requirements

These four make a plugin installable by someone who does not manage
environments. All optional; all added in specification 1.1.

### `requirements` — what must exist, checked without running anything

```json
"requirements": [
  { "name": "Private Python with RDKit and Meeko", "path": "env/bin/python",
    "hint": "Run Set up." },
  { "name": "AutoDock Vina 1.2.7", "path": "bin/vina", "setting": "vina_executable",
    "hint": "Run Set up, or point Settings at a vina you already installed." }
]
```

`path` is relative to the plugin folder and must stay inside it. `setting`
names a setting whose value, when it is an existing file or folder, satisfies
the requirement instead. `platforms` limits it to some platforms.

### `settings` — what the user can tell the plugin

```json
"settings": [
  { "key": "vina_executable", "label": "AutoDock Vina program", "kind": "file",
    "required": false, "default": "",
    "description": "Leave empty to use the Vina that Set up downloads." }
]
```

`key` is `[a-z0-9_]`, `kind` is `file`, `directory` or `text`. Values are
stored per plugin by EigenMol and arrive as `EIGENMOL_SETTING_<KEY>` on every
launch, setup and check. A `file` or `directory` value must exist when it is
set.

### `setup` — building a private environment, on approval

```json
"setup": {
  "description": "Downloads micromamba and builds env/ with RDKit and Meeko.",
  "network": true, "download_mb": 260, "disk_mb": 1100, "timeout_seconds": 3600,
  "commands": {
    "macos": ["/bin/sh", "setup/install.sh"],
    "linux": ["/bin/sh", "setup/install.sh"],
    "windows": ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "setup\\install.ps1"]
  }
}
```

The user sees the description, the resolved command, whether it downloads, and
the sizes, and runs it with *Set up…*. It runs in the plugin folder with the
plugin's environment, as one process group (*Stop* works). Its output is shown
live and kept.

**Rules for a setup:**

- write **only inside the plugin folder** (`EIGENMOL_PLUGIN_DIR`) — never into
  the user's home, a system location, or another plugin's folder,
- do not require a Python, conda or compiler on the machine: bring a
  self-contained installer (for example micromamba, downloaded into
  `.tools/`) or a prebuilt binary,
- pin versions and verify what you download (a checksum),
- refuse an unsupported platform before downloading anything (exit code 3),
- be re-runnable: skip finished steps,
- exit non-zero with a sentence on stderr when something fails.

Uninstalling removes the folder, and with it everything the setup built.

`commands` keys are platform names (§13). A key with a processor, such as
`macos-arm64`, is used in preference to the plain `macos` on that machine
(1.2). The complete contract, with patterns for a private Python, an engine
binary, model weights and Windows, is in
[AUTOMATIC_DEPENDENCIES.md](AUTOMATIC_DEPENDENCIES.md).

### `check` — how ready the plugin is, in its own words

```json
"check": { "commands": { "macos": ["env/bin/python", "aigenmol_vina.py", "--check"] } }
```

Runs when the user presses *Check* (the plugin must be enabled). Print **one
JSON object** on stdout:

```json
{ "ready": true, "summary": "AutoDock Vina is ready to dock.",
  "items": [ { "name": "AutoDock Vina", "status": "ok", "detail": "1.2.7", "fix": "" } ] }
```

`status` is `ok`, `missing`, `warning` or `error`. Before running it, *Check*
also starts your program and completes the handshake, so a broken environment
is found before the first real job.

### `system`

```json
"system": { "gpu": "optional", "memory_gb": 16, "notes": "Downloads 4 GB of model weights during setup." }
```

`gpu` is `none`, `optional` or `required`. Shown before installation, so a user
can decide before downloading anything.

## 13. Platforms and dependencies

- Declare `platforms`. Each entry is an operating system, `macos`, `windows`
  or `linux`, optionally with a processor: `macos-arm64`, `macos-x86_64`,
  `linux-x86_64`, `linux-arm64`, `windows-x86_64`, `windows-arm64` (1.2). `macos`
  means every Mac; `macos-arm64` means Apple silicon only. The installer
  refuses a plugin whose list does not include this machine, before copying a
  file. An unknown name is a warning and matches nothing.
- **Your dependencies are yours.** EigenMol bundles no Python, no CUDA and no
  engine for a plugin, and never installs anything outside the plugin folder.
- A plugin needing Python declares `runtime: "process"` with its entrypoint at
  an interpreter: either one the setup builds inside the folder
  (`"entrypoint": "env/bin/python", "args": ["my_plugin.py"]`), or the system's
  (`"entrypoint": "/usr/bin/env", "args": ["python3", "my_plugin.py"]` — then
  declare it in `system.notes`).
- A compiled program is the simplest: `"entrypoint": "bin/mydock-plugin"` (and a
  `platforms` list matching the binaries you ship).
- Windows: an entrypoint ending in `.exe` inside the folder, or an absolute
  interpreter path. A `.py` file is not directly executable on Windows.
- Large downloads (model weights) belong in `setup`, with `download_mb` and
  `disk_mb` stated.

## 14. Versions and compatibility

| number | moves when | EigenMol's rule |
| --- | --- | --- |
| `protocol` | a message changes incompatibly | a build lists the protocols it speaks; the handshake picks the highest common one; an unknown one is refused naming both |
| `spec_version` major | the manifest changes incompatibly | refused, naming both |
| `spec_version` minor | an optional field is added | accepted; unknown fields are ignored, with a warning |
| plugin `version` | the author releases | installing a different version **replaces** the installed one on the user's confirmation, and the replacement is **disabled** until enabled again |

### What 1.2 added

All of it is optional, and a 1.1 manifest is a valid 1.2 manifest unchanged.

- Platform names with a processor (§13) in `platforms`, in `setup` and `check`
  `commands`, and in a requirement's `platforms`.
- `EIGENMOL_ARCH` in a plugin's environment (§5).
- Installation from a GitHub repository, a GitHub release asset or any HTTPS
  ZIP, besides a local ZIP or folder (§15), with an install record (§18).

1.2 added no message, input or result type, and protocol 1 is unchanged.

### Backward compatibility promises

- A manifest valid under 1.0 is valid under 1.1 and 1.2, unchanged. Every 1.1
  and 1.2 field is optional.
- A plugin speaking protocol 1 keeps working while EigenMol lists 1 among its
  protocols. Removing a protocol version is announced in this document one
  release ahead.
- An unknown extension point, input or result type disables one action, never
  the plugin, so a plugin written for a newer EigenMol degrades instead of
  breaking.
- New result types are additive. A result type moves from *not accepted* to
  accepted; an accepted type is not removed within a protocol version.
- The compatibility test is versioned with this document: it reports which
  specification and protocol it tested against.

## 15. Packaging and distributing a plugin

A plugin is distributed as a ZIP of its folder, or as a folder. A user installs
it from any of five sources, and **all five go through the same installer**:

| Source | Example | Notes |
| --- | --- | --- |
| GitHub repository | `https://github.com/OWNER/REPO` (also `…/tree/REF[/FOLDER]`, `…/releases/tag/TAG`) | releases with a ZIP asset are offered first; a release without one as its source archive; the default branch last, as a **development version** pinned to its commit and needing the user's confirmation |
| GitHub release asset | `https://github.com/OWNER/REPO/releases/download/TAG/FILE.zip` | checked against GitHub's digest of the asset or a `FILE.zip.sha256` asset in the same release |
| Any HTTPS ZIP | `https://host/path/FILE.zip` | checked against `FILE.zip.sha256` at the same address when it exists |
| Local ZIP | a `.zip` file | |
| Local folder | a folder holding `plugin.json` | copied; or, for its author, connected in place (*developer link*, macOS and Linux) |

Rules every source obeys:

- **HTTPS only.** Plain HTTP and redirects to HTTP are refused; at most 8
  redirects are followed. Plain HTTP to a loopback address is permitted only
  under the development setting `EIGENMOL_ALLOW_LOOPBACK_HTTP=1`.
- A download is at most 2 GiB and must be a ZIP. A package holds 400 000 files
  and 32 GiB unpacked at most. No entry or link may point outside the package.
- The manifest may be at the top of the archive or up to three folders down.
  A package with several manifests lets the user choose one.
- No registry is consulted and no host or owner is privileged.
- A GitHub token, when the user sets one in `EIGENMOL_GITHUB_TOKEN`, is sent
  only to `api.github.com`. A private repository is otherwise "not found", and
  is reported with that possibility named.

Publishing: build the ZIP with `pdk/package_plugin.py`; check it with
`eigenmol-plugin-check <zip> --install --setup`; attach the ZIP and its
`.sha256` to a GitHub release or serve them over HTTPS. In the README, state the
engine and its licence, what *Set up* downloads and how much, the platforms,
whether the results are calculations or test data, and that a docking score is
not an affinity.

The step-by-step guide is
[PACKAGING_AND_DISTRIBUTION.md](PACKAGING_AND_DISTRIBUTION.md).

Do not ship anything you are not allowed to redistribute. Running in a separate
process answers a linking question, not a redistribution question; an engine's
licence and its model weights' licence apply to your package.

## 16. The trust model

A plugin is a program running with the **user's privileges**. EigenMol gives
crash isolation and informed consent, **not a sandbox**:

- installing copies files and runs nothing; a new plugin is disabled,
- the manager shows the exact program that will run, and marks one outside the
  plugin folder,
- capabilities, network use, download size and GPU need are shown before
  installing,
- a setup runs only after the user approved it, with its command shown,
- opening a molecular file never starts a program,
- a replacement version is disabled until enabled again,
- an archive cannot write outside the folder it is unpacked into,
- uninstalling deletes only the plugin's own folder,
- downloads are HTTPS only, a published checksum is enforced, and a GitHub
  token is sent to `api.github.com` only and never stored,
- a replaced version is kept until the user discards or restores it.

Capabilities are disclosed, not enforced. A matching checksum says the bytes
are the ones the publisher listed, not who the publisher is. See
[SECURITY_AND_TRUST.md](SECURITY_AND_TRUST.md).

## 17. Limits

| | |
| --- | --- |
| message | 32 MiB |
| header block | 8 KiB |
| stderr kept | 256 KiB |
| handshake | 10 s |
| action timeout | `timeout_seconds`, default 300 s, max 24 h |
| cancel grace | 1.5 s, then the group is terminated |
| check timeout | 120 s (`timeout_seconds` up to 600 s) |
| setup timeout | `timeout_seconds`, default 2 h, max 12 h |
| package | 400 000 files, 32 GiB unpacked |
| download | 2 GiB; 8 redirects; 20 s to connect, 60 s without data |
| returned structure text | 24 MiB, 32 structures |
| overlays per install | 2 000 |
| metadata entries | 256 |

## 18. Install records, status and updates (1.2)

For every install, EigenMol writes `plugins/.installs/<id>.json`
(`format: "eigenmol-plugin-install"`, `schema_version: 1`):

- the plugin id, version, protocol, spec version and platforms;
- the source kind (`github_repository`, `github_release_asset`,
  `https_archive`, `local_archive`, `local_directory`), the repository, the
  reference kind (`release_asset`, `release_source_archive`, `tag`, `commit`,
  `branch`, `download`, `local_archive`, `local_directory`), the tag or branch,
  the commit, the asset, and whether it is a development version;
- the URL without its query string, the package's SHA-256, and whether it
  matched a published checksum;
- the time, the EigenMol version, copy or link, and the version it replaced;
- the outcome of the last setup and the last check.

A plugin has no say in its record. A plugin installed before records existed
has none and works unchanged.

One status word combines the record with the readiness the host can see:
`unsupported platform`, `invalid`, `needs setup`, `setup failed`, `needs
settings`, `missing dependency`, `check failed`, `not checked`, `ready`.
Enabled or disabled is a separate switch.

For a plugin installed from GitHub, an update check compares the newest release
with the installed tag or version, or the branch head with the installed
commit. It downloads nothing. An update installs through the same inspection
and consent as a first install. Replacing a plugin keeps the previous version
in `plugins/.previous/` until the user restores it, discards it or replaces the
plugin again. A plugin installed from a plain URL or a file has no update
channel, and the manager says so.


> **Public copy.** Generated from the documentation bundled with EigenMol
> (`tools/plugins/export_public_spec.py`); edit the source, not this copy.
> These documents describe the plugin interface EigenMol implements today and
> are published so a plugin can be written without EigenMol's source. Their
> licence is not chosen yet; until it is, they are published for reading and
> for writing plugins against.

# EigenMol plugins and the Plugin Development Kit

EigenMol connects external molecular computation through **plugins**. A plugin
is a small program that EigenMol starts as a separate process; it returns typed
results, and EigenMol shows them in the same Pose Browser, Screening table and
3D viewer it uses for everything else. Examples of what a plugin can connect:
a docking engine, a structure-prediction model, a force-field calculation, or
your own analysis.

**This folder is the complete standard.** Everything needed to design, build,
test, package and publish a plugin is here, and the EigenMol core repository is
where it is maintained. You do not need access to any other plugin's
repository. The official plugins are examples that use this standard; none of
them defines it.

## Reading order

| If you want to | Read |
| --- | --- |
| install a plugin | [INSTALLING_PLUGINS.md](INSTALLING_PLUGINS.md) |
| build your first plugin | [CREATE_YOUR_OWN_PLUGIN.md](CREATE_YOUR_OWN_PLUGIN.md), starting from [`templates/python-minimal/`](templates/python-minimal/) |
| know the exact contract | [PLUGIN_SPECIFICATION.md](PLUGIN_SPECIFICATION.md) (version 1.2, protocol 1) |
| make your plugin install its own engine | [AUTOMATIC_DEPENDENCIES.md](AUTOMATIC_DEPENDENCIES.md) |
| publish it on GitHub or your own server | [PACKAGING_AND_DISTRIBUTION.md](PACKAGING_AND_DISTRIBUTION.md) |
| understand what EigenMol does and does not protect | [SECURITY_AND_TRUST.md](SECURITY_AND_TRUST.md) |
| fix an install or a run | [TROUBLESHOOTING.md](TROUBLESHOOTING.md) |
| build a plugin with an AI coding agent | [AI_CODING_AGENTS.md](AI_CODING_AGENTS.md) and [`agent-prompts/`](agent-prompts/) |

## What the PDK contains

| Part | Where | What it is for |
| --- | --- | --- |
| Specification | `PLUGIN_SPECIFICATION.md` | manifest, process model, transport, messages, inputs, results, setup/check, platforms, versions, packaging, trust |
| Starter template | `templates/python-minimal/` | a complete plugin, written from the specification alone: manifest, protocol, typed input, typed results, errors, check |
| Setup template | `templates/python-with-setup/` | the same, plus a setup that builds a private Python environment with a pinned, checksummed installer |
| Packager | `pdk/package_plugin.py` | builds the release ZIP from a plugin folder and validates the manifest on the way (standard library only) |
| Compatibility harness | **Plugins ▸ Create your own plugin ▸ Test a plugin folder…** in the app | runs the installer and the compatibility test on a folder, a ZIP or a URL, optionally with setup |
| Agent kit | `AI_CODING_AGENTS.md`, `agent-prompts/*.md` | a workflow and copy-ready prompts that work from this specification only |

## Five ways to install, one installer

| Source | Example |
| --- | --- |
| GitHub repository | `https://github.com/someone/eigenmol-plugin-x` |
| GitHub release ZIP | `https://github.com/someone/x/releases/download/v1.0.0/x-1.0.0.zip` |
| Any HTTPS ZIP | `https://lab.example.org/downloads/x-1.0.0.zip` |
| ZIP file on this computer | `~/Downloads/x-1.0.0.zip` |
| Folder on this computer | `~/workspace/my-plugin/` (copied, or connected in place for development) |

Every source goes through the same validation, the same disabled start and the
same setup and check. No registry is consulted and no owner is privileged: an
official plugin and a third party's are installed by the same code.

## Plugins maintained by the EigenMol developer

These are examples of the standard. Their repositories are **private** at the
time of writing, so they are listed for reference, not as a dependency.

| Plugin id | Repository | What it shows |
| --- | --- | --- |
| `org.aigenmol.vina` | AutoDock Vina adapter (repository not public yet) | real docking; setup downloads an engine binary and builds a private Python with chemistry libraries |
| `org.aigenmol.mmgbsa` | OpenMM MM/GBSA adapter (repository not public yet) | a real force-field calculation; setup builds a private Python with a scientific library |
| `org.example.mydock` | MyDock example (repository not public yet) | a synthetic example with no dependency (also bundled in the app as *Save the example plugin…*) |

EigenMol's own protocol test fixture is part of its test suite, not a plugin to install.

These documents are bundled with the application and readable offline from the
**Plugins** menu. This public copy is generated from the same text.

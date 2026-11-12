> **Public copy.** Generated from the documentation bundled with EigenMol
> (`tools/plugins/export_public_spec.py`); edit the source, not this copy.
> These documents describe the plugin interface EigenMol implements today and
> are published so a plugin can be written without EigenMol's source. Their
> licence is not chosen yet; until it is, they are published for reading and
> for writing plugins against.

# Building a plugin with an AI coding agent

This page and the prompts in [`agent-prompts/`](agent-prompts/) let a coding
agent (Kiro, Codex, Claude Code or any other) build an EigenMol plugin that
**connects an existing scientific program**, rather than inventing one. They
are plain Markdown and depend only on this folder:

- the specification,
- the starter templates,
- the packager,
- the compatibility harness.

## The workflow

| # | Step | Done when |
| --- | --- | --- |
| 1 | The user names the program to connect and its official source | the official repository or download page and its documentation are identified |
| 2 | Read the program's official documentation and licence | inputs, outputs, versions, platforms and the licence are written down, with links |
| 3 | Analyse the real input and output | a real input file and the real output it produces have been inspected |
| 4 | Read `PLUGIN_SPECIFICATION.md` | the manifest fields, the input snapshot and the result types to be used are chosen |
| 5 | Design the manifest | `plugin.json` with id, version, platforms, actions, inputs, results |
| 6 | Implement the adapter | snapshot → program input → run → program output → typed results, starting from `templates/` |
| 7 | Automate the program's installation | a `setup` that downloads official, pinned, checksummed artefacts into the plugin folder (`AUTOMATIC_DEPENDENCIES.md`) |
| 8 | Connect setup and health check | `requirements`, `setup`, `check`; the check exercises the real path |
| 9 | Typed input/output | units, quantity keys, provenance, `unavailable` versus `0`, names rather than indices |
| 10 | Validate with real data | the real program ran on real input; the numbers were compared with an independent reference |
| 11 | Conformance | `eigenmol-plugin-check <folder> --install --setup` passes |
| 12 | Package | `pdk/package_plugin.py` builds the ZIP and `.sha256`; installing that ZIP passes the harness |
| 13 | Prepare the release | README, version, tag, and release with the ZIP and `.sha256` (never public without the owner's approval) |
| 14 | Report | what was verified, on which platform and with which data, and what was not |

## Rules the agent must follow

- **Work from official sources.** Use the program's own documentation, release
  page and licence. Do not guess an engine's options or output format; read
  them, or run the program and look.
- **Invent nothing.** Do not invent an API, a command-line flag, a file format,
  a protocol field or a result type. If the specification has no field for
  something, do not add one; report it.
- **Never replace a calculation with synthetic values.** A result is the
  engine's output or it is an error. A test fixture is declared
  `"synthetic": true` and is never presented as science.
- **Do not change the protocol.** Use protocol 1 and the result types of
  specification 1.2 exactly as written.
- **Automatic installation is part of done.** Instructions telling the user to
  install Python, conda or the engine by hand do not count as a plugin. Setup
  must do it, inside the plugin folder, with pinned versions and checksums.
- **Do not hand problems to the user.** If setup fails on the agent's
  machine, fix setup. Asking the user to repair their environment is not a fix.
- **Make it installable.** A folder that works only on the agent's machine is
  not finished. Build the ZIP, install it into a clean plugins folder with
  `--install --setup`, and run it there.
- **Verify cleanly.** Run the harness with a fresh `--root`, and with an
  environment that does not include the agent's own Python on `PATH`.
- **Respect licences.** Download engines and weights from their publishers at
  setup. Do not commit them. Name each licence in the README.
- **Report exactly.** Mark each item verified, implemented but not verified,
  blocked, or not implemented. A passing harness is not scientific validation.

## The prompts

| Prompt | Use it to |
| --- | --- |
| [01-create-new-plugin.md](agent-prompts/01-create-new-plugin.md) | start a plugin from the template |
| [02-wrap-existing-software.md](agent-prompts/02-wrap-existing-software.md) | connect a named program end to end |
| [03-add-automatic-dependencies.md](agent-prompts/03-add-automatic-dependencies.md) | add a setup that installs the engine |
| [04-implement-input-output.md](agent-prompts/04-implement-input-output.md) | map the input snapshot and the typed results |
| [05-add-health-check.md](agent-prompts/05-add-health-check.md) | write a check that exercises the real path |
| [06-run-conformance.md](agent-prompts/06-run-conformance.md) | run the harness and fix what it reports |
| [07-prepare-release.md](agent-prompts/07-prepare-release.md) | package, verify and draft a release |
| [08-troubleshoot-installation.md](agent-prompts/08-troubleshoot-installation.md) | diagnose a failed install or setup |

Each prompt has a placeholder block at the top. Fill it in and give the prompt
to the agent with this folder in its context.

## Where the tools come from

- `eigenmol-plugin-check` is a command-line form of the same test that ships with EigenMol builds that include it; the app's own test below is always available.
- The same test is in the app: **Plugins ▸ Create your own plugin ▸ Test a
  plugin folder…**.
- `pdk/package_plugin.py` needs only Python 3.

> **Public copy.** Generated from the documentation bundled with EigenMol
> (`tools/plugins/export_public_spec.py`); edit the source, not this copy.
> These documents describe the plugin interface EigenMol implements today and
> are published so a plugin can be written without EigenMol's source. Their
> licence is not chosen yet; until it is, they are published for reading and
> for writing plugins against.

# Troubleshooting plugins

Every failure is a sentence in the dialog or on the plugin's card. The
sentences below are what EigenMol says, with what they mean and what to do.

## Finding and downloading

| You see | Meaning | Do |
| --- | --- | --- |
| *… is not an https:// address* | plain HTTP, FTP or a file URL | use the `https://` address |
| *… is a GitHub address but not a repository, a release or a release file* | an issue, a pull request or a file view | use `https://github.com/OWNER/REPO`, a `…/tree/BRANCH` link or a release ZIP link |
| *… was not found. If it is a private repository …* | wrong address, or a private repository without a token | check the address; for a private repository set `EIGENMOL_GITHUB_TOKEN`, or download the ZIP and use **Choose a .zip…** |
| *GitHub refused the token …* | the token expired or cannot read the repository | create a new read-only token |
| *GitHub's request limit … resets in about N minute(s)* | anonymous API limit reached | wait, set a token, or use a release ZIP link |
| *The name … could not be found* | DNS failure | check the address and the network |
| *The server's identity could not be verified over HTTPS* | a certificate problem, or a network that intercepts TLS | try another network; EigenMol does not download from a server it cannot verify |
| *… took too long and was stopped* | no answer for 60 s | try again later |
| *The download stopped after N of M bytes* | the connection broke | try again; nothing was installed |
| *… did not return a ZIP archive (it began with `<!doctype`)* | the address is a web page | use the file's direct link |
| *… does not match the checksum its publisher listed* | the file changed or was corrupted | do not install it; tell the publisher |
| *The download is larger than 2048 MB …* | a package carrying an environment | ask the publisher for a package whose setup downloads the engine |
| *This repository has published no release …* | only the branch can be installed | confirm the development version, or ask the author for a release |

## Inspecting and installing

| You see | Meaning | Do |
| --- | --- | --- |
| *… is not an EigenMol plugin: it has no plugin.json* | a program's source, or the wrong folder | find the plugin folder; a program needs an adapter to become a plugin |
| *This holds N plugins …* | several manifests in one package | choose one of the listed folders |
| *this plugin declares macos-x86_64 and this machine is macos-arm64* | built for another system | use a build for your system |
| *The plugin's manifest has problems: …* | an invalid manifest | the plugin author must fix it; the field is named |
| *The archive could not be unpacked: … outside the folder* | a hostile or broken archive | do not use it |
| *… is already installed. Installing … replaces it* | same id installed | confirm **Replace**; the old version is kept |

## Setup, check and running

| Status or message | Meaning | Do |
| --- | --- | --- |
| **needs setup** | a declared requirement is missing | press **Set up…** |
| **setup failed** | the last setup exited with an error | read the log on the card; fix the cause (often the network) and press **Set up…** again; finished steps are skipped |
| **missing dependency** | a requirement is missing and nothing will provide it | follow the item's hint, or set it in **Settings** |
| **check failed** | the plugin's own check reported "not ready" | each item says what is missing |
| *did not start correctly* | the program could not start or speak the protocol | press **Check**; the log says why |
| a run fails with *engine is not installed* | setup did not finish, or a setting points nowhere | **Set up…** again, or fix **Settings** |
| a run fails naming a molecule | the engine cannot compute this input (for example a force field without parameters for a ligand) | that is a scientific limit of the engine, not an install problem |

Being ready means the plugin can run. It does not mean it can compute every
input.

## Recovering

- **An upgrade broke it.** Press **Restore N.N…** on the card. The restored
  version starts disabled.
- **Start over.** **Uninstall…**, then install again. Uninstalling removes
  everything the setup built.
- **Logs.** A setup's and a check's output is shown under the card and kept
  until the next run.

## For plugin authors

```text
eigenmol-plugin-check <folder | zip | url> --install --setup --keep
```

This runs the user's path in a throw-away plugins folder, keeps it for
inspection with `--keep`, and prints every stage: source, resolve, download,
install, setup, readiness, check, compatibility. `--list` shows what a URL
resolves to without downloading anything.

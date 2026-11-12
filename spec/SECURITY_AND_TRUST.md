> **Public copy.** Generated from the documentation bundled with EigenMol
> (`tools/plugins/export_public_spec.py`); edit the source, not this copy.
> These documents describe the plugin interface EigenMol implements today and
> are published so a plugin can be written without EigenMol's source. Their
> licence is not chosen yet; until it is, they are published for reading and
> for writing plugins against.

# Security and trust

A plugin is a program on your computer, and it runs with your privileges.
EigenMol makes that decision visible and keeps it yours. It does not make the
program safe, and this document is clear about which of the two each measure
does.

## What EigenMol guarantees

| Measure | What it means |
| --- | --- |
| Nothing runs on install | Inspecting and installing read and copy files. A program runs only when you press **Set up…**, **Check**, or an action, and only after you enabled the plugin (setup excepted, which asks on its own) |
| Disabled by default | Every new install, and every replacement, starts disabled. New code is not the code you approved |
| The program is shown | The exact executable is shown before you install or enable, and marked when it is outside the plugin folder |
| The setup is shown | The command, whether it downloads, how much, and how much disk it uses, before it runs |
| HTTPS only | Downloads use HTTPS with the Mozilla root certificates. Plain HTTP and redirects to HTTP are refused. The only exception is a loopback address under `EIGENMOL_ALLOW_LOOPBACK_HTTP=1`, for development |
| Checksums enforced | A checksum the publisher stated (GitHub's digest of a release asset, or a `.sha256` beside the file) must match, or nothing is installed |
| Safe unpacking | No archive entry may land outside its folder; no link may point outside the package; size and file-count limits apply |
| Platform checked first | A plugin for another OS or processor is refused before a file is copied |
| Existing install protected | A failed or refused install changes nothing. An upgrade keeps the previous version until you discard or restore it |
| Removal is contained | Uninstalling deletes only the plugin's folder inside the plugins directory, and only the link for a developer connection, never its target |
| Token kept narrow | A GitHub token from `EIGENMOL_GITHUB_TOKEN` is sent only to `api.github.com`, never to a redirect target or another host. It is never written to disk, to an install record or to a log |
| URLs shown without secrets | Addresses are shown and recorded without their query string, which is where signed download links carry credentials |

## What a checksum does and does not say

A matching checksum says **the bytes you received are the bytes the publisher
listed**. It does not say who the publisher is or whether their code is
benign: anyone who controls the repository controls both the file and its
checksum. Trust the source first; the checksum then protects the download.

## What EigenMol does not provide

- **No sandbox.** A plugin can read and write anything you can. Capabilities in
  the manifest are disclosed, not enforced.
- **No code review or signing.** No central party vets plugins, official ones
  included. "Official" names who maintains a plugin. It does not relax any
  check, and it is not a statement that the science is right.
- **No registry gate.** Anyone may publish a plugin, and you may install from
  any HTTPS address. That openness is deliberate, and the responsibility for
  choosing a source is yours.

## Recommendations

- Install from a source you would trust with a program on your computer.
- Prefer a **release** to a development branch. A release is what its author
  chose to publish.
- Read what the setup will download before approving it.
- For a private repository, use a token with read-only access to the
  repositories you need. Set it only in the environment of the EigenMol
  process, never in a file you share.
- Keep a plugin disabled when you are not using it.

## For plugin authors

- Never put a credential in a manifest, a package or a log. If your engine
  needs a key, declare a `setting` with `kind: "text"` and read it from
  `EIGENMOL_SETTING_<KEY>`. It is stored in the plugins folder's `state.json`
  on the user's machine, so say that in your README.
- Pin and verify every download your setup makes.
- Keep `stdout` for protocol messages only.
- Declare `"synthetic": true` for anything that is not a real calculation.

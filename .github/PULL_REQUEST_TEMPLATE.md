<!--
Thank you for listing a plugin. The steps are in docs/REGISTERING_A_PLUGIN.md.
A maintainer reviews every listing by hand; passing the checks does not merge it.
-->

## What this changes

- [ ] Adds a plugin
- [ ] Adds a version of a listed plugin
- [ ] Changes a listing (description, status, links)
- [ ] Removes a listing

Plugin id:

## About the plugin

What it computes, in one or two sentences, and what engine or method it uses:

Where its source code can be read:

## Checklist

- [ ] The package is public and downloads without signing in.
- [ ] `sha256` is the SHA-256 of that exact file, and the address is permanent
      (a GitHub release asset, not a branch archive).
- [ ] `id` and `version` are exactly what the package's `plugin.json` says.
- [ ] The plugin passes EigenMol's compatibility test
      (`Plugins ▸ Create your own plugin… ▸ Test a plugin folder…`).
- [ ] `network` says honestly whether its setup downloads anything and whether a
      run sends any of the user's data anywhere — and if so, `note` says what and where.
- [ ] `license` names the plugin's licence, and its dependencies may be
      used the way its setup installs them.
- [ ] I ran `python3 tools/catalog.py validate` and `python3 tools/catalog.py build`
      and committed the regenerated `index.json`.
- [ ] I publish this plugin, or I have the publisher's permission to list it.

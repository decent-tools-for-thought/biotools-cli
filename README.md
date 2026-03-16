# biotools-cli

`biotools-cli` is a read-only command line client for the [bio.tools](https://bio.tools) API.

It covers the informative endpoints from the bio.tools API reference:

- tool search and listing
- tool detail lookup
- used terms lookup
- registry stats
- domain listing
- domain detail lookup

It deliberately does not implement authenticated or write operations.

## Installation

```bash
python -m pip install -e .
```

Arch Linux package build without `pip`:

```bash
sudo pacman -S --needed base-devel python-build python-installer python-setuptools
makepkg -si
```

If you want to avoid `makepkg` attempting to install dependencies itself, install the makedepends first and then run:

```bash
makepkg -s
sudo pacman -U ./biotools-cli-0.1.0-1-any.pkg.tar.zst
```

## Usage

```bash
biotools --help
```

Common examples:

```bash
biotools tools --name signalp --sort name --order asc
biotools tools --operation "Sequence analysis" --input-data-type "Protein sequence"
biotools tools --all --q blast --per-page 100
biotools tool signalp
biotools tool signalp --format xml
biotools terms name
biotools stats
biotools domains
biotools domain proteomics
biotools filters
```

## Notes

- JSON responses are pretty-printed by default.
- Use `--compact` for single-line JSON output.
- Use `--exact KEY=VALUE` to force exact phrase matching for supported search parameters.
- Parameters that bio.tools requires to be quoted are quoted automatically by the CLI.
- The live `used-terms` API differs slightly from the published docs. The CLI accepts the documented names and maps them to the live-compatible endpoint names.
- Use `--param KEY=VALUE` to pass through future or undocumented query parameters.

## Arch Packaging Notes

- The repository includes a root `PKGBUILD` for local `makepkg` builds.
- The package builds directly from the checked-out source tree.
- It uses `python -m build` to create the wheel and `python -m installer` to stage files into the package root.
- No `pip` step is used anywhere in the Arch packaging flow.

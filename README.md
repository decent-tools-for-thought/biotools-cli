<div align="center">

# biotools-cli

[![Release](https://img.shields.io/github/v/release/decent-tools-for-thought/biotools-cli?sort=semver&color=0f766e)](https://github.com/decent-tools-for-thought/biotools-cli/releases)
![Python](https://img.shields.io/badge/python-3.11%2B-0ea5e9)
![License](https://img.shields.io/badge/license-MIT-14b8a6)

Read-only command-line client for the [bio.tools](https://bio.tools) API with explicit coverage of the informative public endpoints.

</div>

> [!IMPORTANT]
> This codebase is entirely AI-generated. It is useful to me, I hope it might be useful to others, and issues and contributions are welcome.

## Map
- [Install](#install)
- [Functionality](#functionality)
- [Quick Start](#quick-start)
- [Credits](#credits)

## Install
$$\color{#0EA5E9}Install \space \color{#14B8A6}Tool$$

```bash
python -m pip install .
biotools --help
```

## Functionality
$$\color{#0EA5E9}Browse \space \color{#14B8A6}Registry$$

- `biotools tools`: list and search tool records with the documented query filters.
- `biotools tool <id>`: fetch one tool by `biotoolsID`.
- `biotools terms <attribute>`: query the used-terms endpoints with compatibility aliases for the live API.
- `biotools stats`: fetch registry-wide statistics.
- `biotools domains` and `biotools domain <name>`: inspect domain records.
- `biotools filters`: print the supported tool filter flags and their API parameter names.

The CLI is intentionally read-only. It does not implement authenticated or write operations.

## Quick Start
$$\color{#0EA5E9}Try \space \color{#14B8A6}Lookup$$

```bash
biotools tools --name signalp --sort name --order asc
biotools tools --operation "Sequence analysis" --input-data-type "Protein sequence"
biotools tools --all --q blast --per-page 100
biotools tool signalp
biotools tool signalp --format xml
biotools terms function-name
biotools stats
biotools domains
biotools domain proteomics
biotools filters
```

Notes:

- JSON responses are pretty-printed by default; use `--compact` for single-line output.
- Use `--exact KEY=VALUE` to force exact phrase matching for supported search parameters.
- Query parameters that bio.tools requires to be quoted are quoted automatically.
- The live `used-terms` API differs slightly from the published docs; the CLI maps documented aliases to the live endpoint names.
- Use `--param KEY=VALUE` to pass through future or undocumented query parameters.

### Development

```bash
uv sync --group dev
uv run ruff format .
uv run ruff check .
uv run mypy
uv run pytest
uv build
```

### Arch Packaging

The repository includes a root `PKGBUILD` for local `makepkg` and eventual AUR publication.

```bash
sudo pacman -S --needed base-devel python-build python-installer python-setuptools
makepkg -si
```

The package builds directly from the checked-out source tree with `python -m build` and stages files with `python -m installer`. No `pip` step is used in the Arch packaging flow.

## Credits

This client is built for the [bio.tools](https://bio.tools) API and is not affiliated with bio.tools.

Credit goes to the bio.tools maintainers and ELIXIR community for the registry data, API, and documentation this tool depends on.

# Overview

`sphinx-ape` is a documentation plugin for the Sphinx framework.
The purpose of this plugin to share code for generating documentation across all ApeWorX repositories.

## Dependencies

- [python3](https://www.python.org/downloads) version 3.10 up to 3.14.

## Install

Install the package from GitHub:

```sh
pip install git+https://github.com/ApeWorX/sphinx-ape.git@main
```

**NOTE**: Also, you may clone and the package first and install locally.

Try `sphinx-ape --help` to check if it's installed.

## Quick Usage

To use this sphinx plugin, first generate the docs structure (ran from your project directory):

```sh
sphinx-ape init .
```

It will have generated a `docs/` folder with some necessary config file in it, along with a quick-start that links to your `README.md`.

Now, you can begin writing your Sphinx documentation.
There are three directories you can place documentation sources in:

1. `userguides/` - a directory containing how-to guides for how to use your package.
2. `commands/` - `.rst` files for the `sphinx-click` plugin for CLI-based references.
3. `methoddocs/` - Autodoc `.rst` files controlling your generated method documentation.

Once you have developed your documentation, ensure you have `sphinx-ape` installed.
For example, clone this repo and install it using `pip install <path/to/sphinx-ape>` or install from `pypi` by doing `pip intall sphinx-ape`.

After `sphinx-ape` is installed, build your projects' documentation by doing:

```sh
sphinx-ape build <path/to/project>
```

Most commonly, you will already be in your project's directory, so you will do:

```sh
sphinx-ape build .
```

Then, to view the documentation, run the `serve` command:

```sh
sphinx-ape serve <path/to/project>
# When in directory already
sphinx-ape serve .
```

To automatically open a browser at the same time as serving, use the `--open` flag:

```sh
sphinx-ape serve . --open
```

To run your doc-tests, use the `sphinx-ape test` command:

```sh
sphinx-ape test .
```

## Add docs to a plugin

Documentation is **opt-in** for ApeWorX plugins and packages. Many plugins already list `sphinx-ape` under `[dependency-groups] docs` but still need a `docs/` tree and a thin Docs workflow.

Recommended one-shot from the plugin repo root:

```sh
# 1. Ensure the docs group exists (or let --deps / --full add it)
# [dependency-groups]
# docs = ["sphinx-ape"]

uv sync --group docs
sphinx-ape init --full .
```

`sphinx-ape init --full` is equivalent to scaffolding `docs/` plus:

- `--ci` — write `.github/workflows/docs.yaml` if missing (never overwrites)
- `--deps` — ensure `pyproject.toml` `[dependency-groups] docs` includes `sphinx-ape`
- print a short GitHub Pages checklist

You can also pass the flags individually (`sphinx-ape init --ci --deps .`). Bare `sphinx-ape init` still only scaffolds `docs/` (backward compatible).

The generated workflow installs the package with `uv sync --group docs`, puts `.venv/bin` on `PATH`, then calls the shared composite action `ApeWorX/sphinx-ape@main`. The action expects `sphinx-ape` (and your package) to already be available on that PATH from the consumer venv — it does not install dependencies itself.

Pass `github-token: ${{ secrets.GITHUB_TOKEN }}` (the template does). That token is used to push to `gh-pages` and, once the changelog-from-Releases work lands, to authenticate GitHub API calls during the build.

### Rollout

Plugins opt in by running `sphinx-ape init --full` (or the flags above) in their own repo and opening a PR. There is no fleet-wide auto-rollout from this package.

## Auto-TOC Tree

The `sphinx-ape init` command creates an `index.rst` file.
This file represents the table of contents for the docs site.
Any files not included in the TOC are not included in the documentation.
`sphinx-ape` generates a simple default file with the contents:

```rst
.. dynamic-toc-tree::
```

To customize the files included in the TOC, specify each respective guide-set name (e.g. `userguides`).
Also use this feature to control the ordering of the guides; otherwise the default is to include all guides in the directory in alphabetized order.

```rst
.. dynamic-toc-tree::
    :userguides: guide0, guide1, final
```

You can also specify the guides in a list pattern:

```rst
.. dynamic-toc-tree::
    :userguides:
      - quickstart
      - guide0
      - guide1
      - final
```

## GitHub Action

This GitHub action is meant for building the documentation in both core Ape as well any Ape plugin.
The action may also work for regular Python packages with a documentation-strategy similar to Ape.

There are three GitHub events that trigger this action:

1. Push to 'main': we build into 'latest/'.
   The GitHub action will commit these changes to the 'gh-pages' branch.

2. Release: we copy 'latest/' into the release dir, as well as to 'stable/'.
   The GitHub action will commit these changes to the 'gh-pages' branch.

3. Pull requests or local development: We ensure a successful build.

Callers should use a **thin** workflow: checkout, `astral-sh/setup-uv`, `uv sync --group docs`, put `.venv/bin` on `PATH`, then `uses: ApeWorX/sphinx-ape@main` with `github-token: ${{ secrets.GITHUB_TOKEN }}`. See `sphinx-ape init --ci` for the standard template (aligned with plugins such as ape-foundry).

## GitHub Pages

To set up this action with GitHub pages for the release-workflow to work, first create a branch named `gh-pages` and push it to GitHub.
Then, delete everything besides a simple `README.md`, the `.gitignore` file, and the `LICENSE` file.
Once that is all pushed, verify on the Pages tab that a site was made for you.
Now, on merges to main and releases, this site should be updated (if you are using the action).

`sphinx-ape init --ci` / `--full` prints this checklist after writing the workflow.

To publish the docs locally, use the `publish` command:

```sh
sphinx-ape publish .
```

## Development

Please see the [contributing guide](CONTRIBUTING.md) to learn more how to contribute to this project.
Comments, questions, criticisms and pull requests are welcomed.

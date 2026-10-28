"""Helpers for opting a package into sphinx-ape documentation CI and deps."""

from __future__ import annotations

import re
from importlib import resources
from pathlib import Path

import click
import tomli

DOCS_GROUP_SNIPPET = """\
[dependency-groups]
docs = [
    "sphinx-ape",
]
"""

PAGES_CHECKLIST = """\
GitHub Pages checklist (one-time per repo):
  1. Create an orphan `gh-pages` branch with README.md, LICENSE, and .gitignore only, then push it.
  2. In repo Settings → Pages, set the source to the `gh-pages` branch (or confirm Actions can write to it).
  3. After the first successful Docs workflow on `main` (or a release), verify the site updates.
See README → "GitHub Pages" / "Add docs to a plugin" for details.
"""


def load_docs_workflow_template() -> str:
    """Return the standardized thin docs.yaml workflow template."""
    package = resources.files("sphinx_ape")
    return (package / "_templates" / "docs.yaml").read_text(encoding="utf-8")


def ensure_docs_workflow(
    base_path: Path,
    workflow_path: Path | None = None,
) -> Path | None:
    """
    Write ``.github/workflows/docs.yaml`` if it is missing.

    Returns:
        The path written, or ``None`` if the file already existed.
    """
    path = workflow_path or (base_path / ".github" / "workflows" / "docs.yaml")
    if path.is_file():
        click.echo(f"Workflow already exists at {path}; leaving it unchanged.")
        return None

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(load_docs_workflow_template(), encoding="utf-8")
    click.echo(f"Wrote docs workflow: {path}")
    return path


def _docs_group_has_sphinx_ape(docs_deps: list) -> bool:
    for item in docs_deps:
        if not isinstance(item, str):
            continue
        name = item.split(";", 1)[0].strip()
        for sep in (">=", "==", "~=", "!=", "<=", "<", ">"):
            if sep in name:
                name = name.split(sep, 1)[0].strip()
                break
        if name == "sphinx-ape":
            return True
    return False


def ensure_docs_dependency_group(base_path: Path) -> bool:
    """
    Ensure ``pyproject.toml`` has a ``docs`` dependency-group including ``sphinx-ape``.

    Returns:
        ``True`` if the file was modified, ``False`` otherwise.
    """
    pyproject = base_path / "pyproject.toml"
    if not pyproject.is_file():
        click.echo(
            "WARNING: No pyproject.toml found; add a docs dependency-group manually:\n"
            f"{DOCS_GROUP_SNIPPET}",
            err=True,
        )
        return False

    text = pyproject.read_text(encoding="utf-8")
    try:
        data = tomli.loads(text)
    except tomli.TOMLDecodeError as err:
        click.echo(
            f"WARNING: Could not parse pyproject.toml ({err}); add manually:\n{DOCS_GROUP_SNIPPET}",
            err=True,
        )
        return False

    groups = data.get("dependency-groups") or {}
    docs_deps = groups.get("docs")
    if isinstance(docs_deps, list) and _docs_group_has_sphinx_ape(docs_deps):
        click.echo("pyproject.toml already lists sphinx-ape under [dependency-groups] docs.")
        return False

    new_text: str | None = None
    if isinstance(docs_deps, list):
        new_text = _append_sphinx_ape_to_docs_list(text)
    elif "dependency-groups" in data:
        new_text = _insert_docs_group(text)
    else:
        suffix = "" if text.endswith("\n") else "\n"
        new_text = f"{text}{suffix}\n{DOCS_GROUP_SNIPPET}"

    if new_text is None:
        click.echo(
            "WARNING: Could not safely edit pyproject.toml; add this snippet:\n"
            f"{DOCS_GROUP_SNIPPET}",
            err=True,
        )
        return False

    try:
        tomli.loads(new_text)
    except tomli.TOMLDecodeError as err:
        click.echo(
            f"WARNING: Refusing to write invalid TOML ({err}); add manually:\n{DOCS_GROUP_SNIPPET}",
            err=True,
        )
        return False

    pyproject.write_text(new_text, encoding="utf-8")
    click.echo(f"Updated docs dependency-group in {pyproject}")
    return True


def _append_sphinx_ape_to_docs_list(text: str) -> str | None:
    """Insert ``\"sphinx-ape\",`` into an existing ``docs = [...]`` list."""
    # Single-line: docs = [] or docs = ["other"]
    single = re.search(r"^docs\s*=\s*\[(.*?)\]\s*$", text, re.MULTILINE)
    if single and "\n" not in single.group(0):
        inner = single.group(1).strip()
        if not inner:
            replacement = 'docs = [\n    "sphinx-ape",\n]'
        else:
            # Keep single-line style with a trailing entry.
            if inner.endswith(","):
                inner = inner + ' "sphinx-ape",'
            else:
                inner = inner + ', "sphinx-ape"'
            replacement = f"docs = [{inner}]"
        start, end = single.span()
        return text[:start] + replacement + text[end:]

    # Multiline docs = [ ... ]
    pattern = re.compile(
        r"(^docs\s*=\s*\[)(.*?)(^[ \t]*\])",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        return None

    body = match.group(2)
    indent_match = re.search(r"\n([ \t]+)\"", body)
    indent = indent_match.group(1) if indent_match else "    "
    insertion = f'\n{indent}"sphinx-ape",'
    stripped = body.rstrip()
    if stripped.endswith(","):
        new_body = stripped + insertion + "\n"
    elif stripped.strip():
        new_body = stripped + "," + insertion + "\n"
    else:
        new_body = insertion + "\n"

    # Rebuild: prefix through `docs = [` + new_body + closing `]` + remainder.
    close_start = match.start(3)
    return text[: match.end(1)] + new_body + text[close_start:]


def _insert_docs_group(text: str) -> str | None:
    """Insert a docs = [...] entry under an existing [dependency-groups] table."""
    match = re.search(r"^\[dependency-groups\]\s*$", text, re.MULTILINE)
    if not match:
        return None

    insert_at = match.end()
    block = '\ndocs = [\n    "sphinx-ape",\n]\n'
    return text[:insert_at] + block + text[insert_at:]


def print_pages_checklist() -> None:
    """Print the one-time GitHub Pages setup checklist."""
    click.echo(PAGES_CHECKLIST)

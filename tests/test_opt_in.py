from pathlib import Path

import tomli

from sphinx_ape.opt_in import (
    ensure_docs_dependency_group,
    ensure_docs_workflow,
    load_docs_workflow_template,
)


def test_load_docs_workflow_template():
    text = load_docs_workflow_template()
    assert "name: Docs" in text
    assert "concurrency:" in text
    assert "uv sync --group docs" in text
    assert "uses: ApeWorX/sphinx-ape@main" in text
    assert "github-token: ${{ secrets.GITHUB_TOKEN }}" in text
    assert 'python-version: "3.10"' in text


def test_ensure_docs_workflow_writes_when_missing(temp_path):
    written = ensure_docs_workflow(temp_path)
    assert written is not None
    assert written.is_file()
    assert "ApeWorX/sphinx-ape@main" in written.read_text()


def test_ensure_docs_workflow_does_not_overwrite(temp_path):
    path = temp_path / ".github" / "workflows" / "docs.yaml"
    path.parent.mkdir(parents=True)
    path.write_text("name: Existing\n", encoding="utf-8")

    result = ensure_docs_workflow(temp_path)
    assert result is None
    assert path.read_text(encoding="utf-8") == "name: Existing\n"


def test_ensure_docs_workflow_custom_path(temp_path):
    custom = temp_path / "ci" / "docs.yaml"
    written = ensure_docs_workflow(temp_path, workflow_path=custom)
    assert written == custom
    assert custom.is_file()


def test_ensure_docs_deps_no_pyproject(temp_path):
    assert ensure_docs_dependency_group(temp_path) is False


def test_ensure_docs_deps_adds_group_when_missing(temp_path):
    pyproject = temp_path / "pyproject.toml"
    pyproject.write_text(
        '[project]\nname = "demo"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )
    assert ensure_docs_dependency_group(temp_path) is True
    data = tomli.loads(pyproject.read_text(encoding="utf-8"))
    assert "sphinx-ape" in data["dependency-groups"]["docs"]


def test_ensure_docs_deps_inserts_into_existing_groups(temp_path):
    pyproject = temp_path / "pyproject.toml"
    pyproject.write_text(
        '[project]\nname = "demo"\n\n[dependency-groups]\ntest = ["pytest"]\n',
        encoding="utf-8",
    )
    assert ensure_docs_dependency_group(temp_path) is True
    data = tomli.loads(pyproject.read_text(encoding="utf-8"))
    assert data["dependency-groups"]["test"] == ["pytest"]
    assert "sphinx-ape" in data["dependency-groups"]["docs"]


def test_ensure_docs_deps_appends_to_existing_docs_list(temp_path):
    pyproject = temp_path / "pyproject.toml"
    pyproject.write_text(
        '[project]\nname = "demo"\n\n[dependency-groups]\ndocs = [\n    "other-doc-tool",\n]\n',
        encoding="utf-8",
    )
    assert ensure_docs_dependency_group(temp_path) is True
    data = tomli.loads(pyproject.read_text(encoding="utf-8"))
    assert data["dependency-groups"]["docs"] == ["other-doc-tool", "sphinx-ape"]


def test_ensure_docs_deps_noop_when_already_present(temp_path):
    original = '[project]\nname = "demo"\n\n[dependency-groups]\ndocs = [\n    "sphinx-ape",\n]\n'
    pyproject = temp_path / "pyproject.toml"
    pyproject.write_text(original, encoding="utf-8")
    assert ensure_docs_dependency_group(temp_path) is False
    assert pyproject.read_text(encoding="utf-8") == original


def test_action_yml_github_token_default_and_env():
    root = Path(__file__).resolve().parents[1]
    text = (root / "action.yml").read_text(encoding="utf-8")
    assert "default: '3.10'" not in text.split("github-token:")[1].split("python-version:")[0]
    # Prefer explicit checks around the github-token block.
    assert "default: ${{ github.token }}" in text
    assert "GITHUB_TOKEN: ${{ inputs.github-token }}" in text
    # Build Docs step must set the env (appears before Doctesting).
    build_idx = text.index("name: Build Docs")
    doctest_idx = text.index("name: Doctesting")
    build_block = text[build_idx:doctest_idx]
    assert "GITHUB_TOKEN: ${{ inputs.github-token }}" in build_block

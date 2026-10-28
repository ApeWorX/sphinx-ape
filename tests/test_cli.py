from pathlib import Path

import pytest
from click.testing import CliRunner

from sphinx_ape._cli import cli as root_cli


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def cli():
    return root_cli


@pytest.fixture(autouse=True)
def mock_builder(mocker):
    patch = mocker.patch("sphinx_ape._cli._create_builder")
    builder = mocker.MagicMock()
    patch.return_value = builder
    return builder


def test_build(runner, cli):
    result = runner.invoke(cli, ("build", "."))
    assert result.exit_code == 0
    assert "Building 'sphinx-ape' 'LATEST'" in result.output


def test_build_docs_folder_not_exists(runner, cli, mock_builder):
    mock_builder.docs_path = Path("thisdoesnotexist")
    result = runner.invoke(cli, ("build", "."))
    assert result.exit_code != 0
    assert "docs/ folder missing. Try running:\n\tsphinx-ape init" in result.output


def test_build_from_pr(runner, cli):
    result = runner.invoke(cli, ("build", ".", "--mode", "pull_request"))
    assert result.exit_code == 0
    assert "Building 'sphinx-ape' 'LATEST'" in result.output


def test_publish(runner, cli):
    result = runner.invoke(cli, ("publish", ".", "--skip-push", "--repo", "ApeWorX/sphinx-ape"))
    assert result.exit_code == 0


def test_init_default_no_ci(runner, cli, mock_builder, temp_path, monkeypatch):
    monkeypatch.chdir(temp_path)
    result = runner.invoke(cli, ("init", str(temp_path)))
    assert result.exit_code == 0
    mock_builder.init.assert_called_once()
    workflow = temp_path / ".github" / "workflows" / "docs.yaml"
    assert not workflow.exists()
    assert "GitHub Pages checklist" not in result.output


def test_init_ci_writes_workflow(runner, cli, mock_builder, temp_path, monkeypatch):
    monkeypatch.chdir(temp_path)
    result = runner.invoke(cli, ("init", str(temp_path), "--ci"))
    assert result.exit_code == 0
    mock_builder.init.assert_called_once()
    workflow = temp_path / ".github" / "workflows" / "docs.yaml"
    assert workflow.is_file()
    assert "ApeWorX/sphinx-ape@main" in workflow.read_text()
    assert "GitHub Pages checklist" in result.output


def test_init_full_writes_workflow_and_deps(runner, cli, mock_builder, temp_path, monkeypatch):
    monkeypatch.chdir(temp_path)
    (temp_path / "pyproject.toml").write_text(
        '[project]\nname = "demo"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )
    result = runner.invoke(cli, ("init", str(temp_path), "--full"))
    assert result.exit_code == 0
    assert (temp_path / ".github" / "workflows" / "docs.yaml").is_file()
    data = __import__("tomli").loads((temp_path / "pyproject.toml").read_text(encoding="utf-8"))
    assert "sphinx-ape" in data["dependency-groups"]["docs"]
    assert "GitHub Pages checklist" in result.output

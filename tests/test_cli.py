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

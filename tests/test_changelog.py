import json
from types import SimpleNamespace
from typing import Any

import pytest

from sphinx_ape.sphinx_ext import changelog
from sphinx_ape.sphinx_ext.changelog import (
    GENERATED_MARKER,
    generate_changelog,
    get_repository,
    render_changelog,
    render_release,
)

RELEASES: list[dict[str, Any]] = [
    {
        "tag_name": "v0.1.0",
        "html_url": "https://github.com/ApeWorX/ape-foo/releases/tag/v0.1.0",
        "published_at": "2024-01-01T00:00:00Z",
        "body": "## Changes\n\n- feat: initial release @dev (#1)\n",
    },
    {
        "tag_name": "v0.2.0",
        "html_url": "https://github.com/ApeWorX/ape-foo/releases/tag/v0.2.0",
        "published_at": "2024-02-01T00:00:00Z",
        "body": (
            "## Changes\n\n- fix(core): a bug @dev (#3)\n- feat!: breaking thing @dev (#2)\n"
            "- Merge something odd @dev (#4)\n\nSpecial thanks to: @dev\n"
        ),
    },
    {"tag_name": "v0.3.0", "draft": True, "body": "- feat: unreleased (#5)"},
]


@pytest.fixture
def app(temp_path):
    config = SimpleNamespace(sphinx_ape_changelog=True, sphinx_ape_changelog_repo=None)
    return SimpleNamespace(srcdir=str(temp_path), config=config)


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for key in ("GITHUB_REPOSITORY", "GITHUB_TOKEN", "SPHINX_APE_OFFLINE"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.delenv("SPHINX_APE_CHANGELOG_JSON", raising=False)


def test_render_release_groups_by_type():
    lines = render_release(RELEASES[1], "ApeWorX/ape-foo")
    text = "\n".join(lines)
    assert text.index("### Features") < text.index("### Bug Fixes") < text.index("### Other")
    assert (
        "- **BREAKING** breaking thing @dev ([#2](https://github.com/ApeWorX/ape-foo/pull/2))"
        in text
    )
    assert "- a bug @dev" in text
    assert "Merge something odd" in text
    assert "Special thanks" not in text
    assert lines[0].endswith("- 2024-02-01")


def test_render_changelog_sorted_and_skips_drafts():
    text = render_changelog(RELEASES, "ApeWorX/ape-foo")
    assert text.startswith(GENERATED_MARKER)
    assert text.index("v0.2.0") < text.index("v0.1.0")
    assert "v0.3.0" not in text


def test_generated_output_is_mdformat_clean():
    mdformat = pytest.importorskip("mdformat")
    from mdformat.plugins import PARSER_EXTENSIONS

    tricky = {
        "tag_name": "v0.0.1",
        "published_at": "2023-12-01T00:00:00Z",
        "body": (
            "* feat: use `foo_bar` and <Tag>   spacing @a (#10)\n"
            "- fix!: snake_case_name & stuff_ @b (#11)\n"
            "* Bump thing from 1 to 2 @dependabot (#12)\n"
        ),
    }
    outputs = [
        render_changelog([*RELEASES, tricky], "ApeWorX/ape-foo"),
        render_changelog(None, "ApeWorX/ape-foo"),
        render_changelog([], None),
    ]
    assert "**BREAKING**" in outputs[0]
    assert "(https://github.com/ApeWorX/ape-foo/pull/2)" in outputs[0]
    assert "See [GitHub Releases]" in outputs[1]
    for text in outputs:
        assert mdformat.text(text, extensions=PARSER_EXTENSIONS.keys()) == text


def test_render_changelog_placeholder():
    text = render_changelog(None, "ApeWorX/ape-foo")
    assert "https://github.com/ApeWorX/ape-foo/releases" in text


def test_get_repository_precedence(app, monkeypatch):
    monkeypatch.setenv("GITHUB_REPOSITORY", "ApeWorX/from-env")
    assert get_repository(app) == "ApeWorX/from-env"
    app.config.sphinx_ape_changelog_repo = "ApeWorX/from-config"
    assert get_repository(app) == "ApeWorX/from-config"


def test_get_repository_from_git_remote(app, mocker):
    mocker.patch(
        "sphinx_ape.sphinx_ext.changelog.subprocess.check_output",
        return_value="git@github.com:ApeWorX/ape-foo.git\n",
    )
    assert get_repository(app) == "ApeWorX/ape-foo"


def test_generate_fetches(app, temp_path, mocker, monkeypatch):
    monkeypatch.setenv("GITHUB_REPOSITORY", "ApeWorX/ape-foo")
    fetch = mocker.patch.object(changelog, "fetch_releases", return_value=RELEASES)
    generate_changelog(app)
    fetch.assert_called_once_with("ApeWorX/ape-foo")
    assert "v0.2.0" in (temp_path / "changelog.md").read_text()
    assert not (temp_path / "_build").exists()  # No cache is written.

    # Fetch failure falls back to the placeholder.
    fetch.side_effect = OSError("offline")
    generate_changelog(app)
    assert "See [GitHub Releases]" in (temp_path / "changelog.md").read_text()


def test_generate_offline(app, temp_path, mocker, monkeypatch):
    monkeypatch.setenv("GITHUB_REPOSITORY", "ApeWorX/ape-foo")
    monkeypatch.setenv("SPHINX_APE_OFFLINE", "1")
    fetch = mocker.patch.object(changelog, "fetch_releases")
    generate_changelog(app)
    fetch.assert_not_called()
    assert "See [GitHub Releases]" in (temp_path / "changelog.md").read_text()


def test_generate_from_json_file(app, temp_path, monkeypatch):
    path = temp_path / "releases.json"
    path.write_text(json.dumps(RELEASES))
    monkeypatch.setenv("SPHINX_APE_CHANGELOG_JSON", str(path))
    monkeypatch.setenv("GITHUB_REPOSITORY", "ApeWorX/ape-foo")
    generate_changelog(app)
    assert "v0.1.0" in (temp_path / "changelog.md").read_text()


def test_generate_keeps_handwritten(app, temp_path, mocker):
    (temp_path / "changelog.md").write_text("# My changelog\n")
    fetch = mocker.patch.object(changelog, "fetch_releases")
    generate_changelog(app)
    fetch.assert_not_called()
    assert (temp_path / "changelog.md").read_text() == "# My changelog\n"


def test_generate_disabled(app, temp_path):
    app.config.sphinx_ape_changelog = False
    generate_changelog(app)
    assert not (temp_path / "changelog.md").exists()

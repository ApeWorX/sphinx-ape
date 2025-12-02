from pathlib import Path

import pytest

from sphinx_ape.build import REDIRECT_HTML, BuildMode, DocumentationBuilder


class TestBuildMode:
    @pytest.mark.parametrize("val", ("latest", 0, "pull_request", "buildmode.latest"))
    def test_init_latest(self, val):
        mode = BuildMode.init(val)
        assert mode is BuildMode.LATEST

    @pytest.mark.parametrize("val", ("merge_to_main", 1, "push", "buildmode.merge_to_main"))
    def test_init_merge_to_main(self, val):
        mode = BuildMode.init(val)
        assert mode is BuildMode.MERGE_TO_MAIN, val

    @pytest.mark.parametrize("val", ("release", 2, "buildmode.release"))
    def test_init_release(self, val):
        mode = BuildMode.init(val)
        assert mode is BuildMode.RELEASE


def assert_build_path(path: Path, expected: str):
    assert path.name == expected  # Tag, latest, or stable
    assert path.parent.name == "sphinx-ape"  # Project name, happens to be this lib
    assert path.parent.parent.name == "_build"  # Sphinx-ism
    assert path.parent.parent.parent.name == "docs"  # Sphinx-ism


class TestDocumentationBuilder:
    @pytest.fixture
    def mock_sphinx(self, mocker):
        def run_mock_sphinx(path, *args, **kwargs):
            path.mkdir(parents=True)
            buildfile = path / "build.txt"
            buildfile.touch()

        mock = mocker.patch("sphinx_ape.build.sphinx_build")
        mock.side_effect = run_mock_sphinx
        return mock

    @pytest.fixture(autouse=True)
    def mock_git(self, mocker):
        return mocker.patch("sphinx_ape.build.git")

    @pytest.mark.parametrize(
        "quickstart_name,quickstart_title",
        [
            ("quickstart", "Overview"),
            ("overview", "Overview"),
            ("quickstart", "Quickstart"),
            ("overview", "Quickstart"),
        ],
    )
    def test_userguide_names(self, temp_path, quickstart_name, quickstart_title):
        builder = DocumentationBuilder(mode=BuildMode.LATEST, base_path=temp_path)
        builder.init(include_quickstart=False)
        builder.userguides_path.mkdir(parents=True, exist_ok=True)
        guide1 = builder.userguides_path / "guide1.md"
        guide1.write_text("# Guide\n\nThis is a guide\n")
        overview = builder.userguides_path / f"{quickstart_name}.md"
        overview.write_text(f"# {quickstart_title}\n\nThis is a quickstart")

        actual = builder.userguide_names
        # NOTE: Quickstart always comes first!
        expected = [quickstart_name, "guide1"]
        assert actual == expected

    def test_build_latest(self, temp_path):
        builder = DocumentationBuilder(mode=BuildMode.LATEST, base_path=temp_path)
        builder.init()  # so there is something to build.
        builder.build()
        assert builder.latest_path.is_dir()

        # Ensure re-direct exists and points to latest/.
        assert builder.index_html_file.is_file()
        expected_content = REDIRECT_HTML.format("latest/userguides/quickstart.html")
        assert builder.index_html_file.read_text() == expected_content

        # Ensure static content exists.
        assert (builder.latest_path / "_static").is_dir()
        assert (builder.latest_path / "_static" / "logo_green.svg").is_file()

    def test_build_release(self, mock_sphinx, mock_git, temp_path):
        tag = "v1.0.0"
        mock_git.return_value = tag
        builder = DocumentationBuilder(mode=BuildMode.RELEASE, base_path=temp_path)
        builder.build()
        call_path = mock_sphinx.call_args[0][0]
        assert_build_path(call_path, tag)
        # Latest and Stable should also have been created!
        assert_build_path(call_path.parent / "latest", "latest")
        assert_build_path(call_path.parent / "stable", "stable")
        # Ensure re-direct exists and points to stable/.
        assert builder.index_html_file.is_file()
        expected_content = REDIRECT_HTML.format("stable/")
        assert builder.index_html_file.read_text() == expected_content

    @pytest.mark.parametrize("sub_tag", ("alpha", "beta"))
    def test_build_alpha_release(self, sub_tag, mock_sphinx, mock_git, temp_path):
        """
        We don't build version releases when using alpha or beta, but we
        still update "stable" and "latest".
        """
        tag = f"v1.0.0{sub_tag}"
        mock_git.return_value = tag
        builder = DocumentationBuilder(mode=BuildMode.RELEASE, base_path=temp_path)
        builder.build()
        call_path = mock_sphinx.call_args[0][0]
        assert_build_path(call_path, "stable")
        # Latest should also have been created!
        assert_build_path(call_path.parent / "latest", "latest")

    def test_publish_merge_to_main(self, temp_path, mock_git):
        tag = "v1.0.0"
        mock_git.return_value = tag
        builder = DocumentationBuilder(mode=BuildMode.MERGE_TO_MAIN, base_path=temp_path)
        gh_pages_path = temp_path / "gh-pages"
        nojekyll_file = gh_pages_path / ".nojekyll"
        stable_dir = gh_pages_path / "stable"
        latest_dir = gh_pages_path / "latest"
        tag_dir = gh_pages_path / tag
        index_file = gh_pages_path / builder.index_html_file.name
        static_dir = latest_dir / "_static"

        # Create a random file in _static to show it doesn't matter.
        static_dir.mkdir(exist_ok=True, parents=True)
        random_file = static_dir / "randomfile.txt"
        random_file.write_text("this should be fine.")

        # Ensure built first.
        builder.init()
        builder.build()
        builder.publish(repository="ApeWorX/sphinx-ape", push=False)

        assert gh_pages_path.is_dir()
        assert nojekyll_file.is_file()
        assert latest_dir.is_dir()
        assert index_file.is_file()
        # Not tag-release should have gotten created on merge-to-main.
        assert not tag_dir.is_dir()
        # Stable only gets built on releases.
        assert not stable_dir.is_dir()
        # Ensure static content exists.
        assert static_dir.is_dir(), "Missing 'latest/_static'"
        logo = static_dir / "logo_green.svg"
        assert logo.is_file(), "Missing logo: 'latest/_static/logo_green.svg'"
        assert not random_file.is_file()

    def test_publish_release(self, temp_path, mock_git):
        tag = "v1.0.0"
        mock_git.return_value = tag
        builder = DocumentationBuilder(mode=BuildMode.RELEASE, base_path=temp_path)
        builder.init()
        # Ensure built first.
        builder.build()
        builder.publish(repository="ApeWorX/sphinx-ape", push=False)
        gh_pages_path = temp_path / "gh-pages"
        nojekyll_file = gh_pages_path / ".nojekyll"
        stable_dir = gh_pages_path / "stable"
        latest_dir = gh_pages_path / "latest"
        tag_dir = gh_pages_path / tag
        index_file = gh_pages_path / builder.index_html_file.name
        assert gh_pages_path.is_dir()
        assert nojekyll_file.is_file()
        assert stable_dir.is_dir()
        assert latest_dir.is_dir()
        assert tag_dir.is_dir()
        assert index_file.is_file()
        # Ensure static content exists.
        for directory in (latest_dir, stable_dir, tag_dir):
            static_dir = directory / "_static"
            assert static_dir.is_dir(), f"Missing static: {directory.name}"
            logo = static_dir / "logo_green.svg"
            assert logo.is_file(), f"Missing logo: {directory.name}"

    @pytest.mark.parametrize(
        "guide_ls",
        [
            ("quickstart, guide0, guide1, final"),
            ("\n        - quickstart\n        - guide0\n        - guide1\n        - final"),
        ],
    )
    def test_build_custom_toc_tree(self, temp_path, guide_ls):
        builder = DocumentationBuilder(mode=BuildMode.LATEST, base_path=temp_path)
        readme = temp_path / "README.md"
        readme.write_text("# Overview\n\nThis is an overview.")
        builder.init()  # so there is something to build.
        guide0 = builder.userguides_path / "guide0.md"
        guide0.write_text("# Guide 0\n\nWelcome")
        guide1 = builder.userguides_path / "guide1.md"
        guide1.write_text("# Guide 1\n\nWelcome")
        final = builder.userguides_path / "final.md"
        final.write_text("# Final\n\nWelcome")
        custom_toc = f".. dynamic-toc-tree::\n    :userguides: {guide_ls}\n"
        builder.index_docs_file.unlink()
        builder.index_docs_file.write_text(custom_toc)

        builder.build()

        # Show it only included what was configured.
        built_userguides = builder.latest_path / "userguides"
        actual = {x.name for x in built_userguides.iterdir()}
        expected = {"quickstart.html", "final.html", "guide1.html", "guide0.html"}
        assert actual == expected

        # Prove the order was maintained.
        index_content = (builder.latest_path / "index.html").read_text()
        form = (
            '<li class="toctree-l1"><a class="reference internal" '
            'href="userguides/{0}.html">{1}</a></li>'
        )
        expected_ls = [
            form.format("quickstart", "Overview"),
            form.format("guide0", "Guide 0"),
            form.format("guide1", "Guide 1"),
            form.format("final", "Final"),
        ]
        expected_order = "\n".join(expected_ls)
        assert expected_order in index_content

    def test_build_handles_plugins(self, temp_path):
        """
        When using plugin-prefix, you can separate out the plugin python
        docs from the core python docs (such as what the Ape framework does).
        """
        builder = DocumentationBuilder(mode=BuildMode.LATEST, base_path=temp_path)
        builder.init()  # so there is something to build.
        custom_toc = ".. dynamic-toc-tree::\n    :plugin-prefix: ape_\n"
        builder.index_docs_file.unlink()
        builder.index_docs_file.write_text(custom_toc)
        builder.methoddocs_path.mkdir(exist_ok=True, parents=True)
        plugin_doc = builder.methoddocs_path / "ape_plugin.md"
        plugin_doc.write_text(
            "# Plugin]\n\n```{eval_rst}\n.. automodule:: ape_plugin\n    :members:```"
        )
        core_doc = builder.methoddocs_path / "api.md"
        core_doc.write_text("# API]\n\n```{eval_rst}\n.. automodule:: api.api\n    :members:```")

        builder.build()

        built_methoddocs_path = builder.latest_path / "methoddocs"
        built_methoddocs = {f.name for f in built_methoddocs_path.iterdir()}

        # Show both docs got created.
        assert "ape_plugin.html" in built_methoddocs
        assert "api.html" in built_methoddocs

        # Show the plugin and core docs are separated in the TOC.
        index_content = (builder.latest_path / "index.html").read_text()
        assert "Plugin Python Reference" in index_content
        assert "Core Python Reference" in index_content

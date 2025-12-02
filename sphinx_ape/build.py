import os
import shutil
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

from sphinx_ape._base import Documentation
from sphinx_ape._utils import extract_source_url, git, replace_tree, sphinx_build
from sphinx_ape.exceptions import BuildError, PublishError

if TYPE_CHECKING:
    from sphinx_ape.types import TOCTreeSpec

REDIRECT_HTML = """
<!DOCTYPE html>
<meta charset="utf-8">
<title>Redirecting...</title>
<meta http-equiv="refresh" content="0; URL=./{}">
"""


class BuildMode(Enum):
    LATEST = 0
    """Build and then push to 'latest/'"""

    MERGE_TO_MAIN = 1
    """Build and then push to 'stable/'"""

    RELEASE = 2
    """Build and then push to 'stable/', 'latest/', and the version's release tag folder"""

    @classmethod
    def init(cls, identifier: "BuildMode | str | None" = None) -> "BuildMode":
        if identifier is None:
            # Default.
            return BuildMode.LATEST

        elif isinstance(identifier, BuildMode):
            return identifier

        elif isinstance(identifier, int):
            return BuildMode(identifier)

        elif isinstance(identifier, str):
            if "." in identifier:
                # Click being weird, value like "buildmode.release".
                identifier = identifier.split(".")[-1].upper()

            identifier = identifier.lower()
            if identifier == "release":
                return BuildMode.RELEASE
            elif identifier in ("push", "merge_to_main"):
                return BuildMode.MERGE_TO_MAIN
            else:
                return BuildMode.LATEST

        # Unexpected.
        raise TypeError(identifier)


class DocumentationBuilder(Documentation):
    """
    Builds either "latest", or "stable" / "release"
    documentation.
    """

    def __init__(
        self,
        mode: BuildMode | None = None,
        base_path: Path | None = None,
        name: str | None = None,
        pages_branch_name: str | None = None,
        toc_tree_spec: "TOCTreeSpec | None" = None,
    ) -> None:
        self.mode = BuildMode.LATEST if mode is None else mode
        super().__init__(base_path, name, toc_tree_spec=toc_tree_spec)
        self._pages_branch_name = pages_branch_name or "gh-pages"

    def build(self):
        """
        Build the documentation.

        Example:
            >>> builder = DocumentationBuilder(
            ...     mode=BuildMode.LATEST, base_path=Path.cwd(), name="sphinx-ape"
            ... )
            >>> builder.build()

        Raises:
            :class:`~sphinx_ape.exceptions.ApeDocsBuildError`: When
              building fails.
        """

        if self.mode in (BuildMode.LATEST, BuildMode.MERGE_TO_MAIN):
            # TRIGGER: Push to 'main' branch. Only builds latest.
            #   And on PRs / local.
            self._sphinx_build(self.latest_path)

        elif self.mode is BuildMode.RELEASE:
            # TRIGGER: Release on GitHub
            self._build_release()

        else:
            # Unknown 'mode'.
            raise BuildError(f"Unsupported build-mode: {self.mode}")

        self._setup_redirect()

    def clean(self):
        """
        Clean build directories.
        """
        shutil.rmtree(self.root_build_path, ignore_errors=True)

    def publish(self, repository: str | None = None, push: bool = True):
        """
        Publish the documentation to GitHub pages.
        Meant to be run in CI/CD on releases.

        Args:
            repository (str | None): The repository name. Defaults to GitHub env-var
              or extraction from setup file.
            push (bool): Set to ``False`` to skip git add, commit, and push.

        Raises:
            :class:`~sphinx_ape.exceptions.ApeDocsPublishError`: When
              publishing fails.
        """
        try:
            self._publish(repository=repository, push=push)
        except Exception as err:
            raise PublishError(str(err)) from err

    def _publish(self, repository: str | None = None, push: bool = True):
        if repository:
            repo_url = f"https://github.com/{repository}"
        else:
            repo_url = extract_source_url()

        gh_pages_path = self.base_path / "gh-pages"
        git(
            "clone",
            repo_url,
            "--branch",
            self._pages_branch_name,
            "--single-branch",
            self._pages_branch_name,
        )
        try:
            # Any built docs get added; the docs that got built are based on
            # the mode parameter.
            for path in self.build_path.iterdir():
                if path.is_dir() and not path.name.startswith(".") and path.name != "doctest":
                    dst_path = gh_pages_path / path.name
                    if dst_path.is_dir():
                        shutil.rmtree(dst_path)

                    shutil.copytree(path, dst_path)

                elif (path.name == "index.html") and path.is_file():
                    gh_pages_path.mkdir(exist_ok=True)
                    (gh_pages_path / "index.html").write_text(path.read_text())

            no_jykell_file = gh_pages_path / ".nojekyll"
            no_jykell_file.touch(exist_ok=True)

            if push:
                here = os.getcwd()
                try:
                    os.chdir(str(gh_pages_path))
                    # NOTE: CI/CD does not push here but instead uses the
                    #  push-action w/ a login.
                    git("add", ".")
                    git("commit", "-m", "Update documentation", "-a")
                    git("push", "origin", "gh-pages")
                finally:
                    os.chdir(here)

        finally:
            if push:
                # Only delete if we are done pushing.
                # Else, leave so the GH action can push.
                shutil.rmtree(gh_pages_path, ignore_errors=True)

    def _build_release(self):
        if not (tag := git("describe", "--tag")):
            raise BuildError("Unable to find release tag.")

        if "beta" in tag or "alpha" in tag:
            # Avoid creating release directory for beta
            # or alpha releases. Only update "stable" and "latest".
            self._sphinx_build(self.stable_path)
            replace_tree(self.stable_path, self.latest_path)

        else:
            # Use the tag to create a new release folder.
            build_dir = self.build_path / tag
            self._sphinx_build(build_dir)

            if not build_dir.is_dir():
                return

            # Clean-up unnecessary extra 'fonts/' directories to save space.
            # There should still be one in 'latest/'
            for font_dirs in build_dir.glob("**/fonts"):
                if font_dirs.is_dir():
                    shutil.rmtree(font_dirs)

            # Replace 'stable' and 'latest' with this version.
            for path in (self.stable_path, self.latest_path):
                replace_tree(build_dir, path)

    def _setup_redirect(self):
        self.build_path.mkdir(exist_ok=True, parents=True)
        redirect = "stable/" if self.stable_path.is_dir() else "latest/"

        # When there is a quickstart, redirect to that instead of the toctree root.
        if quickstart := self.quickstart_name:
            redirect = f"{redirect}userguides/{quickstart}.html"

        # We replace it to handle the case when stable has joined the chat.
        self.index_html_file.unlink(missing_ok=True)
        self.index_html_file.write_text(REDIRECT_HTML.format(redirect))

    def _sphinx_build(self, dst_path: Path):
        shutil.rmtree(dst_path, ignore_errors=True)
        sphinx_build(dst_path, self.docs_path)

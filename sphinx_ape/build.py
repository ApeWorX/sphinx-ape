import shutil
from enum import Enum
from functools import cached_property
from pathlib import Path
from typing import Optional, Union

from sphinx_ape.exceptions import ApeDocsBuildError
from sphinx_ape.utils import get_package_name, git, replace_tree, sphinx_build

REDIRECT_HTML = """
<!DOCTYPE html>
<meta charset="utf-8">
<title>Redirecting...</title>
<meta http-equiv="refresh" content="0; URL=./{}/">
"""


class BuildMode(Enum):
    LATEST = 0
    """Build and then push to 'latest/'"""

    RELEASE = 1
    """Build and then push to 'stable/', 'latest/', and the version's release tag folder"""

    @classmethod
    def init(cls, identifier: Optional[Union[str, "BuildMode"]] = None) -> "BuildMode":
        if identifier is None:
            # Default.
            return BuildMode.LATEST

        elif isinstance(identifier, BuildMode):
            return identifier

        elif isinstance(identifier, int):
            return BuildMode(identifier)

        elif isinstance(identifier, str):
            # GitHub event name.
            return BuildMode.RELEASE if identifier.lower() == "release" else BuildMode.LATEST

        # Unexpected.
        raise TypeError(identifier)


class DocumentationBuilder:
    """
    Builds either "latest", or "stable" / "release"
    documentation.
    """

    def __init__(
        self, mode: BuildMode, base_path: Optional[Path] = None, name: Optional[str] = None
    ) -> None:
        self.mode = mode
        self._base_path = base_path or Path.cwd()
        self._name = name or get_package_name()

    @cached_property
    def docs_path(self) -> Path:
        path = self._base_path / "docs"
        if not path.is_dir():
            raise ApeDocsBuildError("No `docs/` folder found.")

        return path

    @property
    def build_path(self) -> Path:
        return self.docs_path / "_build" / self._name

    @property
    def latest_path(self) -> Path:
        return self.build_path / "latest"

    @property
    def stable_path(self) -> Path:
        return self.build_path / "stable"

    def build(self):
        if self.mode is BuildMode.LATEST:
            # TRIGGER: Push to 'main' branch. Only builds latest.
            self._sphinx_build(self.latest_path)

        elif self.mode is BuildMode.RELEASE:
            # TRIGGER: Release on GitHub
            self.build_release()

        else:
            # Unknown 'mode'.
            raise ApeDocsBuildError(f"Unsupported build-mode: {self.mode}")

        self._setup_redirect()

    def build_release(self):
        if not (tag := git("describe", "--tag")):
            raise ApeDocsBuildError("Unable to find release tag.")

        if "beta" in tag or "alpha" in tag:
            # Avoid creating release directory for beta
            # or alpha releases. Only update "stable" and "latest".
            self._sphinx_build(self.stable_path)
            replace_tree(self.stable_path, self.latest_path)

        else:
            # Use the tag to create a new release folder.
            build_dir = self.build_path / tag
            self._sphinx_build(build_dir)

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

        # In the case for local dev (or a new docs-site), the 'stable/'
        # path will not exist yet, so use 'latest/' instead.
        redirect = "stable" if self.stable_path.is_dir() else "latest"

        index_file = self.build_path / "index.html"
        index_file.unlink(missing_ok=True)
        index_file.write_text(REDIRECT_HTML.format(redirect))

    def _sphinx_build(self, dst_path):
        sphinx_build(dst_path, self.docs_path)
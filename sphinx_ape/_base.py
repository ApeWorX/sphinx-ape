from functools import cached_property
from pathlib import Path

from sphinx_ape._utils import get_package_name
from sphinx_ape.types import TOCTreeSpec


class Documentation:
    """
    The base-documentation class for working with a sphinx-ape project.
    """

    def __init__(
        self,
        base_path: Path | None = None,
        name: str | None = None,
        toc_tree_spec: TOCTreeSpec | None = None,
    ) -> None:
        self.base_path = base_path or Path.cwd()
        self._name = name or get_package_name()
        self._toc_tree_spec = toc_tree_spec or TOCTreeSpec()

    @property
    def docs_path(self) -> Path:
        """
        The root documentation folder.
        """
        return self.base_path / "docs"

    @property
    def root_build_path(self) -> Path:
        return self.docs_path / "_build"

    @property
    def build_path(self) -> Path:
        """
        The build location.
        """
        return self.root_build_path / self._name

    @property
    def latest_path(self) -> Path:
        """
        The build location for ``latest/``.
        """
        return self.build_path / "latest"

    @property
    def stable_path(self) -> Path:
        """
        The build location for ``stable/``.
        """
        return self.build_path / "stable"

    @property
    def userguides_path(self) -> Path:
        """
        The path to the userguides.
        """
        return self.docs_path / "userguides"

    @property
    def commands_path(self) -> Path:
        """
        The path to the generated CLI documentation.
        """
        return self.docs_path / "commands"

    @property
    def methoddocs_path(self) -> Path:
        """
        The path to the autodoc generated documentation.
        """
        return self.docs_path / "methoddocs"

    @property
    def conf_file(self) -> Path:
        """
        The path to sphinx's ``conf.py`` file.
        """
        return self.docs_path / "conf.py"

    @property
    def index_html_file(self) -> Path:
        """
        The path to the index HTML file.
        """
        return self.build_path / "index.html"

    @property
    def index_docs_file(self) -> Path:
        """
        The path to the root docs index file.
        """
        return self.docs_path / "index.rst"

    def init(self, include_quickstart: bool = True):
        """
        Initialize documentation structure.

        Args:
            include_quickstart (bool): Set to ``False`` to ignore
              creating the quickstart guide. Defaults to ``True``.
        """
        if not self.docs_path.is_dir():
            self.docs_path.mkdir()

        if include_quickstart:
            self._ensure_quickstart_exists()

        self._ensure_conf_exists()
        self._ensure_index_exists()

    def _ensure_conf_exists(self):
        if self.conf_file.is_file():
            return

        content = 'extensions = ["sphinx_ape"]\n'
        self.conf_file.write_text(content)

    def _ensure_index_exists(self):
        index_file = self.index_docs_file
        if index_file.is_file():
            return

        content = ".. dynamic-toc-tree::\n"
        index_file.write_text(content)

    def _ensure_quickstart_exists(self):
        quickstart_path = self.userguides_path / "quickstart.md"
        if quickstart_path.is_file():
            # Already exists.
            return

        self.userguides_path.mkdir(exist_ok=True)
        quickstart_path.write_text("```{include} ../../README.md\n```\n")

    @cached_property
    def quickstart_name(self) -> str | None:
        """
        The name of the quickstart guide, if it exists.
        """
        guides = self._get_filenames(self.userguides_path)
        for guide in guides:
            if guide == "quickstart":
                return guide
            elif guide == "overview":
                return guide

        return None

    @property
    def userguide_names(self) -> list[str]:
        """
        An ordered list of all userguides.
        """
        guides = self._get_filenames(self.userguides_path)
        if not (quickstart := self.quickstart_name):
            # Guides has no quickstart.
            return guides

        return [quickstart, *[g for g in guides if g != quickstart]]

    @property
    def cli_reference_names(self) -> list[str]:
        """
        An ordered list of all CLI references.
        """
        return self._get_filenames(self.commands_path)

    @property
    def methoddoc_names(self) -> list[str]:
        """
        An ordered list of all method references.
        """
        return self._get_filenames(self.methoddocs_path)

    def _get_filenames(self, path: Path) -> list[str]:
        if not path.is_dir():
            return []

        filenames = {p.stem for p in path.iterdir() if _is_doc(p)}
        if spec := self._toc_tree_spec.get(path.name):
            # Adhere to configured order and filtering.
            return [f for f in spec if f in filenames]

        # Default to a sorted order.
        return sorted(filenames)


def _is_doc(path: Path) -> bool:
    return path.suffix in (".md", ".rst")

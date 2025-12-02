from pathlib import Path

from docutils.parsers.rst import directives
from sphinx.util.docutils import SphinxDirective

from sphinx_ape.build import DocumentationBuilder
from sphinx_ape.exceptions import BuildError
from sphinx_ape.types import TOCTreeSpec


class DynamicTocTree(SphinxDirective):
    """
    Dynamically create the TOC-tree so users don't
    need to create and maintain index.html files.
    """

    option_spec = {
        "title": directives.unchanged,
        "plugin-prefix": directives.unchanged,
        "userguides": directives.unchanged,
        "commands": directives.unchanged,
        "methoddocs": directives.unchanged,
    }

    @property
    def _base_path(self) -> Path:
        env = self.state.document.settings.env
        return Path(env.srcdir)

    @property
    def title(self) -> str:
        if res := self.options.get("title"):
            # User configured the title.
            return res.strip()

        # Deduced: "Ape-Docs" or "Ape-Vyper-Docs", etc.
        name = self._base_path.parent.name
        name_parts = [n.capitalize() for n in name.split("-")]
        capped_name = "-".join(name_parts)
        return f"{capped_name}-Docs"

    @property
    def plugin_prefix(self) -> str | None:
        return self.options.get("plugin-prefix", "").strip()

    @property
    def _title_rst(self) -> str:
        title = self.title
        bar = "=" * len(title)
        return f"{title}\n{bar}"

    @property
    def toc_tree_spec(self) -> TOCTreeSpec:
        return TOCTreeSpec(
            userguides=_parse_spec(self.options.get("userguides")),
            methoddocs=_parse_spec(self.options.get("methoddocs")),
            commands=_parse_spec(self.options.get("commands")),
        )

    @property
    def builder(self) -> DocumentationBuilder:
        return DocumentationBuilder(
            base_path=self._base_path.parent,
            toc_tree_spec=self.toc_tree_spec,
        )

    def run(self):
        userguides = self._get_userguides()
        cli_docs = self._get_cli_references()
        methoddocs = self._get_methoddocs()

        if plugin_prefix := self.plugin_prefix:
            plugin_methoddocs = [d for d in methoddocs if Path(d).stem.startswith(plugin_prefix)]
        else:
            plugin_methoddocs = []

        methoddocs = [d for d in methoddocs if d not in plugin_methoddocs]
        sections = {"User Guides": userguides, "CLI Reference": cli_docs}
        if plugin_methoddocs:
            # Core (or alike).
            sections["Core Python Reference"] = methoddocs  # Put _before_ plugins!
            sections["Plugin Python Reference"] = plugin_methoddocs
        else:
            # Plugin or regular package.
            sections["Python Reference"] = methoddocs

        # Ensure TOC is not empty (no docs?).
        if not sections or not any(len(x) for x in sections.values()):
            raise BuildError("Empty TOC.")

        toc_trees = []
        for caption, entries in sections.items():
            if len(entries) < 1:
                continue

            toc_tree = f".. toctree::\n   :caption: {caption}\n   :maxdepth: 1\n\n"
            for entry in entries:
                toc_tree += f"   {entry}\n"

            toc_trees.append(toc_tree)

        toc_tree_rst = "\n".join(toc_trees)
        restructured_text = self._title_rst
        if toc_tree_rst:
            restructured_text = f"{restructured_text}\n\n{toc_tree_rst}"

        return self.parse_text_to_nodes(restructured_text)

    def _get_userguides(self) -> list[str]:
        return [f"userguides/{n}" for n in self.builder.userguide_names]

    def _get_cli_references(self) -> list[str]:
        return [f"commands/{n}" for n in self.builder.cli_reference_names]

    def _get_methoddocs(self) -> list[str]:
        return [f"methoddocs/{n}" for n in self.builder.methoddoc_names]


def _parse_spec(value) -> list[str]:
    if value is None:
        return []

    return [n.strip(" -\n\t,") for n in value.split(" ") if n.strip(" -\n\t")]

extensions = [
    "sphinx_ape",
    "sphinx_github_changelog",
]

doctest_global_setup = """
from sphinx_ape.build import BuildMode, DocumentationBuilder
from pathlib import Path
"""

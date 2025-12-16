import os
import sys
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING

from sphinx.util import logging

from sphinx_ape._utils import get_package_name
from sphinx_ape.sphinx_ext.directives import DynamicTocTree

if TYPE_CHECKING:
    from sphinx.application import Sphinx

logger = logging.getLogger(__name__)


def setup(app: "Sphinx"):
    """Set default values for various Sphinx configurations."""

    # For building and serving multiple projects at once,
    # we situate ourselves in the parent directory.
    sys.path.insert(0, os.path.abspath(".."))

    # Configure project and other one-off items.
    package_name = get_package_name()
    app.config.project = package_name
    app.config.copyright = f"{date.today().year}, ApeWorX LTD"
    app.config.author = "ApeWorX Team"

    app.config.exclude_patterns = list(
        set(app.config.exclude_patterns).union({"_build", ".DS_Store"})
    )
    app.config.source_suffix = [".rst", ".md"]
    app.config.master_doc = "index"

    # Automatically add required extensions.
    default_extensions = {
        "myst_parser",
        "sphinx_click",
        "sphinx.ext.autodoc",
        "sphinx.ext.autosummary",
        "sphinx.ext.doctest",
        "sphinx.ext.napoleon",
        "sphinx_rtd_theme",
        "sphinx_plausible",
    }

    # Ensure these have been loaded before continuing.
    for ext in default_extensions:
        app.setup_extension(ext)

    app.config.extensions = list(set(app.config.extensions).union(default_extensions))

    # Plausible config.
    if not getattr(app.config, "plausible_domain", None):
        app.config.plausible_domain = "docs.apeworx.io"

    # Configure the HTML workings.
    static_dir = Path(__file__).parent.parent / "_static"

    app.config.html_theme = "shibuya"
    app.config.html_favicon = str(static_dir / "favicon.ico")
    app.config.html_baseurl = package_name
    app.config.html_static_path = [str(static_dir)]
    app.config.html_theme_options = {
        "light_logo": "_static/logo_grey.svg",
        "dark_logo": "_static/logo_green.svg",
        "accent_color": "lime",
    }

    # All MyST config.
    app.config.myst_all_links_external = True

    # Any config starting with "auto".
    app.config.autosummary_generate = True
    exclude_members = (
        # Object.
        "__weakref__",
        "__metaclass__",
        "__init__",
        "__format__",
        "__new__",
        "__dir__",
        # Pydantic.
        "model_config",
        "model_fields",
        "model_post_init",
        "model_computed_fields",
        "__class_vars__",
        "__private_attributes__",
        "__pydantic_complete__",
        "__pydantic_core_schema__",
        "__pydantic_custom_init__",
        "__pydantic_decorators__",
        "__pydantic_generic_metadata__",
        "__pydantic_parent_namespace__",
        "__pydantic_post_init__",
        "__pydantic_serializer__",
        "__pydantic_validator__",
        # EthPydanticTypes.
        "__ape_extra_attributes__",
    )
    app.config.autodoc_default_options = {"exclude-members": ", ".join(exclude_members)}

    # Add the directive enabling the dynamic-TOC.
    app.add_directive("dynamic-toc-tree", DynamicTocTree)

    # Output data needed for the rest of the build.
    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }

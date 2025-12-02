import ast
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

import tomli

from sphinx_ape.exceptions import BuildError

# Avoid needing to have common Ape packages re-configure this.
PACKAGE_ALIASES = {
    "eth-ape": "ape",
}


def git(*args):
    return subprocess.check_output(["git", *args]).decode("ascii").strip()


def new_dir(path: Path) -> Path:
    if path.is_dir():
        shutil.rmtree(path)

    path.mkdir(parents=True)
    return path


def sphinx_build(dst_path: Path, source_dir: Path | str) -> Path:
    path = new_dir(dst_path)
    try:
        subprocess.check_call(["sphinx-build", str(source_dir), str(path)])
    except subprocess.SubprocessError as err:
        raise BuildError(f"Command 'sphinx-build docs {path}' failed.") from err

    return path


def get_source_url(directory: Path | None = None) -> str:
    if env_var := os.getenv("GITHUB_REPO"):
        return f"https://github.com/{env_var}"

    return extract_source_url(directory=directory)


def extract_source_url(directory: Path | None = None) -> str:
    directory = directory or Path.cwd()
    url = None
    if (directory / "setup.py").is_file():
        url = _extract_github_url_from_setup_py(directory / "setup.py")
    if url is None:
        raise BuildError("No package source URL found.")

    return url


def _extract_github_url_from_setup_py(file_path: Path) -> str | None:
    # Check `project_urls`
    project_urls: dict = _extract_key_from_setup_py("project_urls", file_path) or {}  # type: ignore
    if url := project_urls.get("Source"):
        return url

    # Try url
    url = _extract_key_from_setup_py("url", file_path)
    if url and url.startswith("https://github.com"):
        return url

    return None


def _extract_name_from_setup_py(file_path: Path) -> str | None:
    return _extract_key_from_setup_py("name", file_path)


def _extract_key_from_setup_py(key: str, file_path: Path) -> Any | None:
    if not (setup_content := file_path.read_text()):
        return None
    elif not (parsed_content := ast.parse(setup_content)):
        return None

    # Walk through the AST to find the setup() call and extract the desired information
    for node in ast.walk(parsed_content):
        if (
            not isinstance(node, ast.Call)
            or not hasattr(node.func, "id")
            or node.func.id != "setup"
        ):
            continue

        for keyword in node.keywords:
            if keyword.arg != key:
                continue

            return ast.literal_eval(keyword.value)

    return None


def _extract_name_from_pyproject_toml(file_path: Path) -> str | None:
    """Extract package name from pyproject.toml."""
    with open(file_path, "rb") as file:
        pyproject = tomli.load(file)

    if "tool" in pyproject and "poetry" in pyproject["tool"]:
        return pyproject["tool"]["poetry"].get("name")

    elif "project" in pyproject:
        return pyproject["project"].get("name")

    return None


def get_package_name() -> str:
    if env_var := os.getenv("GITHUB_REPO"):
        return env_var

    # Figure it out.
    return extract_package_name()


def extract_package_name(directory: Path | None = None) -> str:
    """Detect and extract the package name from the project files."""
    directory = directory or Path.cwd()
    pkg_name = None
    if (directory / "setup.py").is_file():
        pkg_name = _extract_name_from_setup_py(directory / "setup.py")
    if pkg_name is None and (directory / "pyproject.toml").is_file():
        pkg_name = _extract_name_from_pyproject_toml(directory / "pyproject.toml")
    if pkg_name is None:
        path = f"{directory}".replace(f"{Path.home()}", "$HOME")
        raise BuildError(f"No package name found at '{path}'.")

    return PACKAGE_ALIASES.get(pkg_name, pkg_name)


def replace_tree(base_path: Path, dst_path: Path):
    shutil.rmtree(dst_path, ignore_errors=True)
    shutil.copytree(base_path, dst_path)

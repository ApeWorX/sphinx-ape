#!/usr/bin/env python
from setuptools import find_packages, setup

extras_require = {
    "test": [
        "pytest>=8.3.2,<9",
        "pytest-mock>=3.14.0,<4",
    ],
    "lint": [
        "black>=24.10.0,<25",  # Auto-formatter and linter
        "mypy>=1.13.0,<2",  # Static type analyzer
        "types-setuptools",  # Needed for mypy type shed
        "docutils-stubs",  # Needed for mypy type shed
        "flake8>=7.1.1,<8",  # Style linter
        "flake8-breakpoint>=1.1.0,<2",  # Detect breakpoints left in code
        "flake8-print>=5.0.0,<6",  # Detect print statements left in code
        "flake8-pydantic",  # For detecting issues with Pydantic models
        "flake8-type-checking",  # Detect imports to move in/out of type-checking blocks
        "isort>=5.13.2,<6",  # Import sorting linter
        "mdformat>=0.7.19",  # Auto-formatter for markdown
        "mdformat-gfm>=0.3.5",  # Needed for formatting GitHub-flavored markdown
        "mdformat-frontmatter>=0.4.1",  # Needed for frontmatters-style headers in issue templates
        "mdformat-pyproject>=0.0.2",  # Allows configuring in pyproject.toml
    ],
    "release": [  # `release` GitHub Action job uses this
        "setuptools>=75.6.0",  # Installation tool
        "wheel",  # Packaging tool
        "twine",  # Package upload tool
    ],
    "dev": [
        "commitizen",  # Manage commits and publishing releases
        "pre-commit",  # Ensure that linters are run prior to committing
        "pytest-watch",  # `ptw` test watcher/runner
        "IPython",  # Console for interacting
        "ipdb",  # Debugger (Must use `export PYTHONBREAKPOINT=ipdb.set_trace`)
    ],
}

# NOTE: `pip install -e .[dev]` to install package
extras_require["dev"] = (
    extras_require["lint"]
    + extras_require["release"]
    + extras_require["test"]
    + extras_require["dev"]
)

with open("./README.md") as readme:
    long_description = readme.read()


setup(
    name="sphinx-ape",
    use_scm_version=True,
    setup_requires=["setuptools_scm"],
    description="sphinx-ape: Build Sphinx Documentation for ApeWorX plugins",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="ApeWorX Ltd.",
    author_email="admin@apeworx.io",
    url="https://github.com/ApeWorX/sphinx-ape",
    include_package_data=True,
    install_requires=[
        "click>=8.1.7,<9",  # Script controller framework
        "tomli>=1.2.3,<3",  # For parsing pyproject.toml file
        "shibuya",  # Sphinx theme
        "pygments>=2.17.0,<3",  # Needed for the Vyper lexer
        "myst-parser>=4.0.0,<5",  # Parse markdown docs
        "sphinx-click>=6.0.0,<7",  # For documenting CLI
        "Sphinx>=8.1.3,<9",  # Documentation generator
        "sphinx_rtd_theme>=3.0.1,<4",  # Readthedocs.org theme
        "sphinxcontrib-napoleon>=0.7,<0.8",  # Allow Google-style documentation
        "sphinx-plausible>=0.1.2,<0.2",  # For analytics
    ],
    entry_points={
        "console_scripts": [
            "sphinx-ape=sphinx_ape._cli:cli",
        ],
    },
    python_requires=">=3.10,<4",
    extras_require=extras_require,
    py_modules=["sphinx_ape"],
    license="Apache-2.0",
    zip_safe=False,
    keywords="ethereum",
    packages=find_packages(exclude=["tests", "tests.*"]),
    package_data={"sphinx_ape": ["py.typed", "_static/*"]},
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Operating System :: MacOS",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
)

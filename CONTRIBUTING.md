# Development

To get started with working on the codebase, use the following steps prepare your local environment:

```bash
# clone the github repo and navigate into the folder
git clone https://github.com/ApeWorX/sphinx-ape.git
cd sphinx-ape

# create and load a virtual environment
python3 -m venv venv
source venv/bin/activate

# install sphinx-ape into the virtual environment
python setup.py install

# install the developer dependencies (-e is interactive mode)
pip install -e . --group dev
```

## Pre-Commit Hooks

We use [`pre-commit`](https://pre-commit.com/) hooks to simplify linting and ensure consistent formatting among contributors.
Use of `pre-commit` is not a requirement, but is highly recommended.

Install `pre-commit` locally from the root folder:

```bash
pip install pre-commit
pre-commit install
```

Committing will now automatically run the local hooks and ensure that your commit passes all lint checks.

## Running the docs locally

The documentation for this package is built using the tools from this package.
Follow the README.md to learn how to install and use this tool.
Then, from the root of this repository, run:

```bash
sphinx-ape build .
```

Then, to view the results, run:

```bash
sphinx-ape serve . --open
```

## Pull Requests

Pull requests are welcomed! Please adhere to the following:

- Ensure your pull request passes our linting checks
- Include test cases for any new functionality
- Include any relevant documentation updates

It's a good idea to make pull requests early on.
A pull request represents the start of a discussion, and doesn't necessarily need to be the final, finished submission.

If you are opening a work-in-progress pull request to verify that it passes CI tests, please consider
[marking it as a draft](https://help.github.com/en/github/collaborating-with-issues-and-pull-requests/about-pull-requests#draft-pull-requests).

Join the ApeWorX [Discord](https://discord.gg/apeworx) if you have any questions.

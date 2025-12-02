import subprocess
from pathlib import Path

from sphinx_ape._base import Documentation
from sphinx_ape.exceptions import BuildError, TestError


class DocumentationTester(Documentation):
    """
    Small wrapper around sphinx-build's doctest command.
    """

    @property
    def doctest_folder(self) -> Path:
        """
        The path to doctest's build folder.
        """
        return self.build_path.parent / "doctest"

    @property
    def doctest_output_file(self) -> Path:
        """
        The path to doctest's output file.
        """
        return self.doctest_folder / "output.txt"

    def test(self):
        """
        Run the sphinx-build doctest command.

        Raises:
            :class:`~sphinx_ape.exceptions.ApeDocsTestError`
        """
        self._run_tests()
        output = self.doctest_output_file.read_text() if self.doctest_output_file.is_file() else ""
        if "Test passed" in output or "0 tests" in output:
            # Either no failures or no tests ran.
            return

        # Failures.
        raise TestError(output)

    def _run_tests(self):
        try:
            subprocess.run(
                ["sphinx-build", "-b", "doctest", "docs", str(self.doctest_folder)], check=True
            )
        except subprocess.CalledProcessError as err:
            raise BuildError(str(err)) from err

class TOCTreeSpec(dict[str, list[str]]):
    """
    Specify the structure of the auto-generated TOC-tree
    by specifying names of guides via the keys ``"userguides"``,
    ``"commands"``, and ``"methoddocs"``. The TOC-tree
    will lay out the contents in that order and exclude
    any missing guides. It's meant to be a workaround when
    the default behavior is inadequate.
    """

    def __init__(
        self,
        userguides: list[str] | None = None,
        commands: list[str] | None = None,
        methoddocs: list[str] | None = None,
        **kwargs,
    ):
        super().__init__(
            {
                "userguides": userguides or [],
                "commands": commands or [],
                "methoddocs": methoddocs or [],
                **kwargs,
            }
        )

"""Error types for ripgrep SDK."""


class RipgrepError(Exception):
    """Base exception for ripgrep SDK errors."""

    def __init__(self, message: str, exit_code: int = 2):
        super().__init__(message)
        self.exit_code = exit_code


class PatternError(RipgrepError):
    """Invalid regex pattern."""

    def __init__(self, message: str):
        super().__init__(f"Invalid pattern: {message}", exit_code=2)


class PathError(RipgrepError):
    """Invalid or inaccessible path."""

    def __init__(self, path: str, message: str):
        super().__init__(f"Path error for '{path}': {message}", exit_code=2)
        self.path = path


class BinaryNotFoundError(RipgrepError):
    """ripgrep binary not found."""

    def __init__(self, binary: str = "rg"):
        super().__init__(
            f"ripgrep binary '{binary}' not found. "
            "Please install ripgrep: https://github.com/BurntSushi/ripgrep#installation",
            exit_code=127
        )
        self.binary = binary


class NoMatchesError(RipgrepError):
    """No matches found (exit code 1).

    This is not typically raised as an exception since no matches
    is a valid search result. It's provided for cases where the
    caller wants to treat no matches as an error.
    """

    def __init__(self):
        super().__init__("No matches found", exit_code=1)

"""
ripgrep-sdk: High-performance Python SDK for ripgrep.

This SDK provides both synchronous and asynchronous interfaces to ripgrep,
with streaming support and proper type annotations.

Example:
    >>> from ripgrep_sdk import Ripgrep
    >>> rg = Ripgrep()
    >>> for match in rg.search("TODO", "."):
    ...     print(f"{match.path}:{match.line_number}: {match.line_content}")
"""

from .types import Match, MatchLocation, SearchStats, FileType, OutputMode
from .client import Ripgrep, AsyncRipgrep
from .errors import RipgrepError, PatternError, PathError, BinaryNotFoundError

__version__ = "0.1.0"
__all__ = [
    "Ripgrep",
    "AsyncRipgrep",
    "Match",
    "MatchLocation",
    "SearchStats",
    "FileType",
    "OutputMode",
    "RipgrepError",
    "PatternError",
    "PathError",
    "BinaryNotFoundError",
]

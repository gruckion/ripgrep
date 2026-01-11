"""Type definitions for ripgrep SDK."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional, Union


class FileType(Enum):
    """Supported file types for filtering."""
    RUST = "rust"
    PYTHON = "py"
    JAVASCRIPT = "js"
    TYPESCRIPT = "ts"
    GO = "go"
    JAVA = "java"
    C = "c"
    CPP = "cpp"
    CSHARP = "cs"
    HTML = "html"
    CSS = "css"
    JSON = "json"
    YAML = "yaml"
    TOML = "toml"
    MARKDOWN = "md"
    TXT = "txt"
    XML = "xml"
    SQL = "sql"
    SHELL = "sh"
    RUBY = "ruby"
    PHP = "php"


class OutputMode(Enum):
    """Output mode for search results."""
    MATCHES = "matches"  # Full match information
    FILES = "files"      # Only file paths
    COUNT = "count"      # Match counts per file


@dataclass(frozen=True, slots=True)
class MatchLocation:
    """Location of a submatch within a line."""
    start: int
    end: int
    text: str

    def __repr__(self) -> str:
        return f"MatchLocation({self.start}:{self.end}, {self.text!r})"


@dataclass(slots=True)
class Match:
    """A single match result from ripgrep.

    Attributes:
        path: Path to the file containing the match
        line_number: 1-based line number
        line_content: Full content of the matching line
        byte_offset: Absolute byte offset in file (optional)
        submatches: List of match locations within the line
    """
    path: Path
    line_number: int
    line_content: str
    byte_offset: Optional[int] = None
    submatches: List[MatchLocation] = field(default_factory=list)

    @classmethod
    def from_json(cls, data: dict) -> "Match":
        """Parse Match from ripgrep --json output."""
        d = data["data"]
        path_text = d["path"]["text"]
        lines_text = d["lines"]["text"]

        submatches = []
        for sm in d.get("submatches", []):
            submatches.append(MatchLocation(
                start=sm["start"],
                end=sm["end"],
                text=sm["match"]["text"]
            ))

        return cls(
            path=Path(path_text),
            line_number=d["line_number"],
            line_content=lines_text.rstrip("\n\r"),
            byte_offset=d.get("absolute_offset"),
            submatches=submatches,
        )

    @property
    def match_text(self) -> str:
        """Return the first match text, or empty string if none."""
        if self.submatches:
            return self.submatches[0].text
        return ""

    def __repr__(self) -> str:
        return (
            f"Match(path={self.path!r}, line={self.line_number}, "
            f"match={self.match_text!r})"
        )


@dataclass(slots=True)
class SearchStats:
    """Statistics from a search operation."""
    elapsed_secs: float
    searches: int
    searches_with_match: int
    bytes_searched: int
    bytes_printed: int
    matched_lines: int
    matches: int

    @classmethod
    def from_json(cls, data: dict) -> "SearchStats":
        """Parse SearchStats from ripgrep --json summary."""
        d = data["data"]["stats"]
        return cls(
            elapsed_secs=d["elapsed"]["secs"] + d["elapsed"]["nanos"] / 1e9,
            searches=d["searches"],
            searches_with_match=d["searches_with_match"],
            bytes_searched=d["bytes_searched"],
            bytes_printed=d["bytes_printed"],
            matched_lines=d["matched_lines"],
            matches=d["matches"],
        )


@dataclass(slots=True)
class FileMatch:
    """A file path result (from -l mode)."""
    path: Path

    @classmethod
    def from_json(cls, data: dict) -> "FileMatch":
        """Parse FileMatch from ripgrep --json output."""
        return cls(path=Path(data["data"]["path"]["text"]))


@dataclass(slots=True)
class CountMatch:
    """A count result (from -c mode)."""
    path: Path
    count: int

    @classmethod
    def from_line(cls, line: str) -> "CountMatch":
        """Parse CountMatch from path:count format."""
        # Handle paths with colons by splitting from the right
        parts = line.rsplit(":", 1)
        return cls(path=Path(parts[0]), count=int(parts[1]))


# Type alias for path-like arguments
PathLike = Union[str, Path]

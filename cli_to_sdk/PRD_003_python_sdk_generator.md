# PRD-003: Python SDK Generator

## Product Requirements Document

**Version**: 1.0
**Date**: 2025-01-11
**Author**: Research Phase
**Status**: Prototype Complete, Production Design Ready
**Parent**: PRD-001 CLI→SDK System

---

## 1. Executive Summary

### 1.1 Purpose

Generate production-quality Python SDKs from CIDL specifications. The generator transforms a machine-readable CLI definition into a fully-typed, documented, Pythonic library that wraps the CLI tool.

### 1.2 Prototype Status

A working Tier A (subprocess) SDK for ripgrep has been implemented:

```
cli_to_sdk/ripgrep_sdk/
├── __init__.py       # Package exports
├── client.py         # Ripgrep, AsyncRipgrep classes
├── types.py          # Match, MatchLocation, SearchStats dataclasses
└── errors.py         # RipgrepError hierarchy
```

### 1.3 Key Research Findings

#### 1.3.1 Subprocess is Fast Enough

| Approach | Latency | Notes |
|----------|---------|-------|
| Direct `rg` subprocess | ~27ms | Baseline |
| ripgrep_sdk (Tier A) | ~49ms | +22ms Python overhead |
| ripgrep-python (PyO3) | ~64-119ms | Surprisingly slower |

**Conclusion**: Tier A (subprocess) is the right starting point. Native bindings are premature optimization.

#### 1.3.2 Python Integration Patterns

| Pattern | Use Case | Complexity |
|---------|----------|------------|
| Synchronous streaming | Interactive CLI tools | Low |
| Async streaming | High-concurrency apps | Medium |
| Batch operations | Bulk processing | Low |
| Connection pooling | Daemon mode (Tier B) | Medium |

---

## 2. Requirements

### 2.1 Functional Requirements

#### 2.1.1 SDK Structure Generation

**Must Generate**:
```
{tool}_sdk/
├── __init__.py           # Public API exports
├── py.typed              # PEP 561 marker
├── client.py             # Main client class(es)
├── types.py              # Dataclasses for responses
├── errors.py             # Exception hierarchy
└── _internal/
    ├── __init__.py
    ├── args.py           # Argument building
    └── parser.py         # Output parsing
```

**Should Generate**:
```
├── async_client.py       # Async variant (if complex)
├── enums.py              # Enum types from choices
└── _compat.py            # Python version compatibility
```

#### 2.1.2 Client API Generation

**From CIDL Option**:
```yaml
- name: ignore-case
  short: i
  type: switch
  description: "Search case-insensitively"
  category: "Search"
```

**Generate Python**:
```python
def search(
    self,
    pattern: str,
    path: Union[str, Path, List[Union[str, Path]]] = ".",
    *,
    ignore_case: bool = False,  # from --ignore-case/-i
    # ... other options
) -> Iterator[Match]:
    """Search for pattern in path.

    Args:
        pattern: A regular expression used for searching.
        path: Files or directories to search.
        ignore_case: Search case-insensitively.

    Yields:
        Match objects for each match found.

    Raises:
        PatternError: If the regex pattern is invalid.
        PathError: If a path doesn't exist.
    """
```

#### 2.1.3 Type Generation

**From CIDL Exit Codes**:
```yaml
exit_codes:
  - code: 0
    name: match_found
  - code: 1
    name: no_match
  - code: 2
    name: error
```

**Generate Exceptions**:
```python
class RipgrepError(Exception):
    """Base exception for ripgrep errors."""
    exit_code: int
    stderr: str

class NoMatchError(RipgrepError):
    """No matches were found (exit code 1)."""
    exit_code = 1

class SearchError(RipgrepError):
    """An error occurred during search (exit code 2)."""
    exit_code = 2
```

**From CIDL Output Schema**:
```yaml
output:
  schemas:
    json:
      messages:
        - type: match
          schema:
            properties:
              path: ...
              lines: ...
              line_number: integer
```

**Generate Dataclasses**:
```python
@dataclass
class Match:
    """A single match result."""
    path: Optional[Path]
    lines: str
    line_number: Optional[int]
    absolute_offset: int
    submatches: List[SubMatch]

    @classmethod
    def from_json(cls, data: dict) -> "Match":
        """Parse from JSON message."""
        ...
```

#### 2.1.4 Enum Generation

**From CIDL**:
```yaml
- name: color
  type: enum
  choices: [never, auto, always, ansi]
  default: auto
```

**Generate**:
```python
class ColorChoice(str, Enum):
    """When to use color in output."""
    NEVER = "never"
    AUTO = "auto"
    ALWAYS = "always"
    ANSI = "ansi"

# In client method signature:
def search(
    self,
    pattern: str,
    *,
    color: Union[ColorChoice, Literal["never", "auto", "always", "ansi"]] = ColorChoice.AUTO,
) -> Iterator[Match]:
```

### 2.2 Non-Functional Requirements

| Requirement | Target | Rationale |
|-------------|--------|-----------|
| Python version | 3.9+ | Modern typing, dataclasses |
| Type coverage | 100% | Full mypy/pyright support |
| Docstring coverage | 100% | IDE help, documentation |
| Import time | <100ms | Fast script startup |
| Memory overhead | <10MB | Reasonable footprint |
| Test coverage | >90% | Production quality |

### 2.3 Compatibility Requirements

| Library | Support |
|---------|---------|
| mypy | Full (strict mode) |
| pyright | Full |
| pylance | Full |
| pytest | Test discovery |
| asyncio | Native async client |
| trio | Should work (untested) |

---

## 3. Architecture

### 3.1 Generator Pipeline

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────┐
│   CIDL   │────▶│   Parser     │────▶│  Templates   │────▶│  Output  │
│   File   │     │              │     │  (Jinja2)    │     │  Files   │
└──────────┘     └──────────────┘     └──────────────┘     └──────────┘
                        │
                        ▼
                 ┌──────────────┐
                 │   IR Model   │
                 │  (Pydantic)  │
                 └──────────────┘
```

### 3.2 Internal Representation

```python
@dataclass
class SDKModel:
    """Internal representation for code generation."""
    package_name: str
    cli_name: str
    version: str

    client_class: str        # "Ripgrep"
    async_client_class: str  # "AsyncRipgrep"

    methods: List[MethodModel]
    types: List[TypeModel]
    enums: List[EnumModel]
    errors: List[ErrorModel]

@dataclass
class MethodModel:
    name: str                # Python method name
    cli_command: str         # CLI command/subcommand
    description: str
    parameters: List[ParameterModel]
    return_type: str
    is_streaming: bool
    is_async: bool

@dataclass
class ParameterModel:
    name: str                # Python parameter name
    cli_name: str            # --option-name
    cli_short: Optional[str] # -o
    python_type: str         # "bool", "int", "str", etc.
    default: Optional[Any]
    description: str
    is_required: bool
    is_multiple: bool
```

### 3.3 Name Transformation Rules

| CIDL Name | Python Name | Rule |
|-----------|-------------|------|
| `ignore-case` | `ignore_case` | Kebab to snake |
| `type` | `file_type` | Reserved word handling |
| `glob` | `glob_pattern` | Clarity (disambiguate) |
| `PATH` | `path` | Lowercase positional |
| `--no-foo` | (handled internally) | Negation via bool |

### 3.4 Argument Building

```python
class ArgumentBuilder:
    """Builds CLI arguments from method parameters."""

    def __init__(self, binary: str = "rg"):
        self.args = [binary]

    def add_flag(self, name: str, value: bool) -> "ArgumentBuilder":
        """Add boolean flag (--name or --no-name)."""
        if value:
            self.args.append(f"--{name}")
        return self

    def add_option(self, name: str, value: Any) -> "ArgumentBuilder":
        """Add option with value (--name=value)."""
        if value is not None:
            self.args.append(f"--{name}={value}")
        return self

    def add_multi(self, name: str, values: List[Any]) -> "ArgumentBuilder":
        """Add multiple values (--name=v1 --name=v2)."""
        for v in values:
            self.args.append(f"--{name}={v}")
        return self

    def add_positional(self, value: Any) -> "ArgumentBuilder":
        """Add positional argument."""
        self.args.append(str(value))
        return self

    def build(self) -> List[str]:
        return self.args
```

---

## 4. Integration Tiers

### 4.1 Tier A: Subprocess (Implemented)

```python
class Ripgrep:
    """Synchronous ripgrep client using subprocess."""

    def __init__(self, binary: str = "rg"):
        self._binary = binary
        self._validate_binary()

    def search(
        self,
        pattern: str,
        path: Union[PathLike, List[PathLike]] = ".",
        *,
        ignore_case: bool = False,
        json_output: bool = True,  # Always use JSON for structured parsing
    ) -> Iterator[Match]:
        args = self._build_args(pattern, path, ignore_case=ignore_case)

        with subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ) as proc:
            for line in proc.stdout:
                if line.strip():
                    yield Match.from_json(json.loads(line))

            proc.wait()
            if proc.returncode == 2:
                raise SearchError(proc.stderr.read().decode())
```

**Characteristics**:
- ~5ms process spawn overhead
- ~7ms ripgrep startup
- Streaming output via pipe
- No shared state between calls

### 4.2 Tier B: Daemon (Planned)

```python
class RipgrepDaemon:
    """Persistent ripgrep process for low-latency repeated searches."""

    def __init__(self, binary: str = "rg"):
        self._proc = None
        self._binary = binary

    async def __aenter__(self):
        self._proc = await asyncio.create_subprocess_exec(
            self._binary, "--daemon",  # Hypothetical flag
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
        )
        return self

    async def search(self, pattern: str, path: str) -> AsyncIterator[Match]:
        # Send request via stdin, read response via stdout
        request = json.dumps({"pattern": pattern, "path": path})
        self._proc.stdin.write(request.encode() + b"\n")
        await self._proc.stdin.drain()

        async for line in self._proc.stdout:
            msg = json.loads(line)
            if msg["type"] == "end":
                break
            yield Match.from_json(msg)
```

**Characteristics**:
- ~1ms per search (amortized)
- Connection pooling
- Requires CLI support for daemon mode

### 4.3 Tier C: Shared Library (Future)

```python
# If ripgrep exposed a C ABI
import ctypes

class RipgrepFFI:
    """Direct FFI to ripgrep shared library."""

    def __init__(self, lib_path: str = "libripgrep.so"):
        self._lib = ctypes.CDLL(lib_path)
        self._lib.rg_search.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
        self._lib.rg_search.restype = ctypes.POINTER(RgResult)

    def search(self, pattern: str, path: str) -> Iterator[Match]:
        result = self._lib.rg_search(
            pattern.encode(),
            path.encode(),
        )
        # ... parse result
```

**Note**: Requires ripgrep to expose C ABI, which it currently doesn't.

---

## 5. Generated Code Examples

### 5.1 __init__.py

```python
"""ripgrep SDK - High-performance text search from Python.

Example:
    >>> from ripgrep_sdk import Ripgrep
    >>> rg = Ripgrep()
    >>> for match in rg.search("TODO", "src/"):
    ...     print(f"{match.path}:{match.line_number}: {match.lines}")
"""

from .client import Ripgrep, AsyncRipgrep
from .types import Match, MatchLocation, SubMatch, SearchStats
from .errors import (
    RipgrepError,
    NoMatchError,
    SearchError,
    PatternError,
    PathError,
    BinaryNotFoundError,
)
from .enums import ColorChoice, SortBy

__version__ = "0.1.0"
__all__ = [
    "Ripgrep",
    "AsyncRipgrep",
    "Match",
    "MatchLocation",
    "SubMatch",
    "SearchStats",
    "RipgrepError",
    "NoMatchError",
    "SearchError",
    "PatternError",
    "PathError",
    "BinaryNotFoundError",
    "ColorChoice",
    "SortBy",
]
```

### 5.2 client.py (Generated)

```python
"""Ripgrep client implementation."""

from __future__ import annotations

import json
import subprocess
import shutil
from pathlib import Path
from typing import Iterator, List, Optional, Union, Literal, overload

from .types import Match, SearchStats
from .errors import RipgrepError, NoMatchError, SearchError, BinaryNotFoundError
from .enums import ColorChoice, SortBy

PathLike = Union[str, Path]


class Ripgrep:
    """Synchronous ripgrep client.

    Example:
        >>> rg = Ripgrep()
        >>> for match in rg.search("pattern", "path/"):
        ...     print(match)

    Args:
        binary: Path to the ripgrep binary. Defaults to "rg".

    Raises:
        BinaryNotFoundError: If the ripgrep binary is not found.
    """

    def __init__(self, binary: str = "rg") -> None:
        self._binary = binary
        if not shutil.which(binary):
            raise BinaryNotFoundError(f"ripgrep binary not found: {binary}")

    def search(
        self,
        pattern: str,
        path: Union[PathLike, List[PathLike]] = ".",
        *,
        # Search options
        ignore_case: bool = False,
        smart_case: bool = False,
        case_sensitive: bool = False,
        fixed_strings: bool = False,
        word_regexp: bool = False,
        line_regexp: bool = False,
        multiline: bool = False,
        # Filter options
        file_type: Optional[Union[str, List[str]]] = None,
        type_not: Optional[Union[str, List[str]]] = None,
        glob_pattern: Optional[Union[str, List[str]]] = None,
        hidden: bool = False,
        no_ignore: bool = False,
        max_depth: Optional[int] = None,
        max_filesize: Optional[str] = None,
        # Output options
        context: int = 0,
        before_context: Optional[int] = None,
        after_context: Optional[int] = None,
        max_count: Optional[int] = None,
        # Advanced
        encoding: Optional[str] = None,
        threads: Optional[int] = None,
    ) -> Iterator[Match]:
        """Search for pattern in path(s).

        Args:
            pattern: A regular expression used for searching.
            path: File or directory to search. Directories are searched recursively.
            ignore_case: Search case-insensitively.
            smart_case: Search case-insensitively if pattern is all lowercase.
            case_sensitive: Search case sensitively (default).
            fixed_strings: Treat pattern as literal string, not regex.
            word_regexp: Match only at word boundaries.
            line_regexp: Match only entire lines.
            multiline: Allow patterns to match across lines.
            file_type: Only search files of these types (e.g., "py", "js").
            type_not: Exclude files of these types.
            glob_pattern: Include/exclude files matching glob.
            hidden: Search hidden files and directories.
            no_ignore: Don't respect ignore files.
            max_depth: Maximum directory depth to descend.
            max_filesize: Ignore files larger than this (e.g., "1M").
            context: Lines of context around matches.
            before_context: Lines before each match.
            after_context: Lines after each match.
            max_count: Maximum matches per file.
            encoding: Text encoding (e.g., "utf-8", "latin-1").
            threads: Approximate number of threads to use.

        Yields:
            Match objects for each match found.

        Raises:
            PatternError: If the regex pattern is invalid.
            PathError: If a path doesn't exist.
            SearchError: If an error occurs during search.

        Example:
            >>> rg = Ripgrep()
            >>> matches = list(rg.search("TODO", "src/", file_type="py"))
            >>> print(f"Found {len(matches)} TODOs in Python files")
        """
        args = self._build_args(
            pattern, path,
            ignore_case=ignore_case,
            smart_case=smart_case,
            case_sensitive=case_sensitive,
            fixed_strings=fixed_strings,
            word_regexp=word_regexp,
            line_regexp=line_regexp,
            multiline=multiline,
            file_type=file_type,
            type_not=type_not,
            glob_pattern=glob_pattern,
            hidden=hidden,
            no_ignore=no_ignore,
            max_depth=max_depth,
            max_filesize=max_filesize,
            context=context,
            before_context=before_context,
            after_context=after_context,
            max_count=max_count,
            encoding=encoding,
            threads=threads,
        )

        yield from self._execute_streaming(args)

    def count(
        self,
        pattern: str,
        path: Union[PathLike, List[PathLike]] = ".",
        *,
        # ... same options as search
    ) -> dict[Path, int]:
        """Count matches per file.

        Returns:
            Dictionary mapping file paths to match counts.
        """
        # Implementation with --count flag
        ...

    def files(
        self,
        path: Union[PathLike, List[PathLike]] = ".",
        *,
        file_type: Optional[Union[str, List[str]]] = None,
        glob_pattern: Optional[Union[str, List[str]]] = None,
        hidden: bool = False,
    ) -> Iterator[Path]:
        """List files that would be searched.

        Yields:
            Path objects for each file.
        """
        # Implementation with --files flag
        ...

    def _build_args(self, pattern: str, path: ..., **kwargs) -> List[str]:
        """Build command line arguments."""
        args = [self._binary, "--json"]  # Always JSON for parsing

        # Add options
        if kwargs.get("ignore_case"):
            args.append("--ignore-case")
        if kwargs.get("smart_case"):
            args.append("--smart-case")
        # ... etc

        # Add positional args
        args.append(pattern)
        if isinstance(path, list):
            args.extend(str(p) for p in path)
        else:
            args.append(str(path))

        return args

    def _execute_streaming(self, args: List[str]) -> Iterator[Match]:
        """Execute and stream results."""
        with subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ) as proc:
            for line in proc.stdout:
                if not line.strip():
                    continue
                msg = json.loads(line)
                if msg["type"] == "match":
                    yield Match.from_json(msg["data"])

            proc.wait()
            self._handle_exit_code(proc.returncode, proc.stderr.read())

    def _handle_exit_code(self, code: int, stderr: bytes) -> None:
        """Handle process exit code."""
        if code == 0:
            return  # Success with matches
        elif code == 1:
            return  # Success, no matches (not an error for iterator)
        elif code == 2:
            error_msg = stderr.decode().strip()
            if "regex" in error_msg.lower():
                raise PatternError(error_msg)
            elif "no such file" in error_msg.lower():
                raise PathError(error_msg)
            else:
                raise SearchError(error_msg)
        else:
            raise RipgrepError(f"Unexpected exit code: {code}")
```

### 5.3 types.py (Generated)

```python
"""Data types for ripgrep results."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class SubMatch:
    """A submatch within a line."""

    match: str
    """The matched text."""

    start: int
    """Start byte offset within the line."""

    end: int
    """End byte offset within the line."""

    @classmethod
    def from_json(cls, data: dict) -> SubMatch:
        return cls(
            match=data["match"]["text"],
            start=data["start"],
            end=data["end"],
        )


@dataclass
class Match:
    """A single match result.

    Attributes:
        path: The file path where the match was found.
        lines: The matching line(s) content.
        line_number: The 1-based line number.
        absolute_offset: Byte offset from start of file.
        submatches: Individual matches within the line.
    """

    path: Optional[Path]
    """Path to the file containing the match."""

    lines: str
    """The content of the matching line(s)."""

    line_number: Optional[int]
    """1-based line number of the match."""

    absolute_offset: int
    """Byte offset from the start of the file."""

    submatches: List[SubMatch] = field(default_factory=list)
    """Individual pattern matches within the line."""

    @classmethod
    def from_json(cls, data: dict) -> Match:
        """Parse a Match from ripgrep JSON output.

        Args:
            data: The "data" field from a JSON message of type "match".

        Returns:
            A Match instance.
        """
        path_data = data.get("path")
        path = Path(path_data["text"]) if path_data else None

        lines_data = data.get("lines", {})
        lines = lines_data.get("text", "")

        return cls(
            path=path,
            lines=lines,
            line_number=data.get("line_number"),
            absolute_offset=data.get("absolute_offset", 0),
            submatches=[SubMatch.from_json(sm) for sm in data.get("submatches", [])],
        )

    def __str__(self) -> str:
        """Format as path:line:content."""
        parts = []
        if self.path:
            parts.append(str(self.path))
        if self.line_number:
            parts.append(str(self.line_number))
        parts.append(self.lines.rstrip())
        return ":".join(parts)


@dataclass
class SearchStats:
    """Statistics from a search operation."""

    elapsed_secs: float
    """Total elapsed time in seconds."""

    searches: int
    """Number of files searched."""

    searches_with_match: int
    """Number of files with at least one match."""

    bytes_searched: int
    """Total bytes searched."""

    bytes_printed: int
    """Total bytes printed."""

    matched_lines: int
    """Total lines with matches."""

    matches: int
    """Total individual matches."""

    @classmethod
    def from_json(cls, data: dict) -> SearchStats:
        elapsed = data.get("elapsed", {})
        return cls(
            elapsed_secs=elapsed.get("secs", 0) + elapsed.get("nanos", 0) / 1e9,
            searches=data.get("searches", 0),
            searches_with_match=data.get("searches_with_match", 0),
            bytes_searched=data.get("bytes_searched", 0),
            bytes_printed=data.get("bytes_printed", 0),
            matched_lines=data.get("matched_lines", 0),
            matches=data.get("matches", 0),
        )
```

---

## 6. Testing Strategy

### 6.1 Unit Tests

```python
# test_client.py
import pytest
from ripgrep_sdk import Ripgrep, Match, PatternError

def test_search_basic(tmp_path):
    """Test basic search functionality."""
    (tmp_path / "test.txt").write_text("hello world\nfoo bar\nhello again")

    rg = Ripgrep()
    matches = list(rg.search("hello", tmp_path))

    assert len(matches) == 2
    assert matches[0].line_number == 1
    assert matches[1].line_number == 3

def test_search_ignore_case(tmp_path):
    """Test case-insensitive search."""
    (tmp_path / "test.txt").write_text("Hello World")

    rg = Ripgrep()

    # Case sensitive (default)
    matches = list(rg.search("hello", tmp_path))
    assert len(matches) == 0

    # Case insensitive
    matches = list(rg.search("hello", tmp_path, ignore_case=True))
    assert len(matches) == 1

def test_invalid_pattern():
    """Test that invalid regex raises PatternError."""
    rg = Ripgrep()

    with pytest.raises(PatternError):
        list(rg.search("[invalid", "."))

def test_binary_not_found():
    """Test that missing binary raises BinaryNotFoundError."""
    from ripgrep_sdk import BinaryNotFoundError

    with pytest.raises(BinaryNotFoundError):
        Ripgrep(binary="nonexistent-rg")
```

### 6.2 Integration Tests

```python
# test_integration.py
def test_real_codebase_search():
    """Search actual codebase to verify realistic behavior."""
    rg = Ripgrep()

    # Search for Python imports in current project
    matches = list(rg.search("^import ", ".", file_type="py"))

    assert len(matches) > 0
    for match in matches:
        assert match.lines.startswith("import ")
```

### 6.3 Property Tests

```python
# test_properties.py
from hypothesis import given, strategies as st

@given(st.text(min_size=1))
def test_fixed_strings_matches_literal(pattern):
    """Fixed strings should match the literal pattern."""
    # Create temp file with exact pattern
    # Search with fixed_strings=True
    # Verify match
```

---

## 7. Success Metrics

| Metric | Target |
|--------|--------|
| Type check pass (mypy strict) | 100% |
| Test coverage | >90% |
| API surface matches CIDL | 100% |
| Documentation coverage | 100% |
| PyPI package size | <100KB |
| Import time | <100ms |

---

## 8. Roadmap

### Phase 1: Core Generator
- [x] Manual prototype (ripgrep_sdk)
- [ ] Jinja2 templates
- [ ] CIDL parser
- [ ] Code generation pipeline

### Phase 2: Polish
- [ ] Async client generation
- [ ] Comprehensive test generation
- [ ] Documentation generation
- [ ] Type stub generation

### Phase 3: Advanced
- [ ] Tier B daemon support
- [ ] Batch operation optimization
- [ ] Progress callbacks
- [ ] Cancellation support

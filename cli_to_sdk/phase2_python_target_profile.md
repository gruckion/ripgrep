# Phase 2: Target Runtime Profile - Python

## 1. Basic Information

| Field | Value |
|-------|-------|
| **Language** | Python |
| **Target Versions** | 3.9+ (ideally 3.11+ for performance) |
| **Runtime** | CPython |
| **Package Format** | wheels (sdist fallback) |
| **Distribution** | PyPI |

---

## 2. Integration Mechanisms

### 2.1 Subprocess (Tier A)

| Aspect | Details |
|--------|---------|
| **Module** | `subprocess` |
| **Recommended API** | `subprocess.run()` or `subprocess.Popen()` |
| **Async Support** | `asyncio.create_subprocess_exec()` |
| **Streaming** | `Popen` with `stdout=PIPE`, iterate lines |

#### Performance Characteristics

```python
# Measured overhead (from earlier benchmarks)
# Process spawn: ~4-5ms average
# rg invocation: ~10ms minimum (includes startup)
```

#### Code Pattern

```python
import subprocess
import json
from typing import Iterator

def search_subprocess(pattern: str, path: str) -> Iterator[dict]:
    """Tier A: Subprocess with streaming JSON."""
    proc = subprocess.Popen(
        ['rg', '--json', pattern, path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    for line in proc.stdout:
        data = json.loads(line)
        if data['type'] == 'match':
            yield data

    proc.wait()
    if proc.returncode == 2:
        raise RuntimeError(proc.stderr.read())
```

### 2.2 FFI Options (Tier C/D)

#### Option 1: PyO3 (Rust → Python)

| Aspect | Details |
|--------|---------|
| **Maturity** | Excellent |
| **Performance** | Near-native |
| **Build Tool** | maturin |
| **Distribution** | wheels |

```rust
// Example PyO3 binding
use pyo3::prelude::*;

#[pyfunction]
fn search(pattern: &str, path: &str) -> PyResult<Vec<Match>> {
    // Use grep crate directly
}

#[pymodule]
fn ripgrep_py(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(search, m)?)?;
    Ok(())
}
```

#### Option 2: CFFI (C ABI → Python)

| Aspect | Details |
|--------|---------|
| **Maturity** | Excellent |
| **Performance** | Good |
| **Requirement** | C ABI wrapper |
| **Distribution** | wheels with shared library |

```python
from cffi import FFI

ffi = FFI()
ffi.cdef("""
    typedef struct {
        const char* path;
        uint64_t line_number;
        const char* line;
        size_t match_start;
        size_t match_end;
    } RgMatch;

    int rg_search(
        const char* pattern,
        const char* path,
        void (*callback)(const RgMatch*, void*),
        void* user_data
    );
""")

lib = ffi.dlopen("libripgrep.so")
```

#### Option 3: ctypes (C ABI → Python, no build)

| Aspect | Details |
|--------|---------|
| **Maturity** | Built-in |
| **Performance** | Good |
| **Requirement** | C ABI wrapper |
| **Distribution** | Ship .so/.dll alongside |

### 2.3 Comparison Matrix

| Mechanism | Setup Effort | Performance | Distribution | Maintenance |
|-----------|--------------|-------------|--------------|-------------|
| subprocess | None | Baseline | None | Low |
| PyO3 | Medium | Excellent | Wheels | Medium |
| CFFI | Medium | Good | Wheels + lib | Medium |
| ctypes | Low | Good | Ship lib | Low |

---

## 3. Streaming Primitives

### 3.1 Synchronous Streaming

```python
from typing import Iterator, Generator

# Generator-based streaming
def search(pattern: str, path: str) -> Generator[Match, None, None]:
    for match in _internal_search(pattern, path):
        yield match

# Usage
for match in search("TODO", "."):
    print(match)
```

### 3.2 Asynchronous Streaming

```python
import asyncio
from typing import AsyncIterator

async def search_async(pattern: str, path: str) -> AsyncIterator[Match]:
    proc = await asyncio.create_subprocess_exec(
        'rg', '--json', pattern, path,
        stdout=asyncio.subprocess.PIPE
    )

    async for line in proc.stdout:
        data = json.loads(line)
        if data['type'] == 'match':
            yield Match.from_json(data)

# Usage
async for match in search_async("TODO", "."):
    print(match)
```

### 3.3 Async Generator with Backpressure

```python
import asyncio
from collections import deque

class BufferedAsyncSearch:
    def __init__(self, pattern: str, path: str, buffer_size: int = 100):
        self.pattern = pattern
        self.path = path
        self.buffer_size = buffer_size
        self._buffer = deque(maxlen=buffer_size)
        self._done = False

    async def __aiter__(self):
        proc = await asyncio.create_subprocess_exec(
            'rg', '--json', self.pattern, self.path,
            stdout=asyncio.subprocess.PIPE
        )

        async for line in proc.stdout:
            while len(self._buffer) >= self.buffer_size:
                await asyncio.sleep(0.001)  # Backpressure

            data = json.loads(line)
            if data['type'] == 'match':
                yield Match.from_json(data)
```

---

## 4. Cancellation Mechanisms

### 4.1 Subprocess Cancellation

```python
import subprocess
import signal
from contextlib import contextmanager

@contextmanager
def cancellable_search(pattern: str, path: str):
    proc = subprocess.Popen(
        ['rg', '--json', pattern, path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    try:
        yield proc
    except GeneratorExit:
        proc.terminate()
        proc.wait(timeout=1)
    except:
        proc.kill()
        raise
    finally:
        if proc.poll() is None:
            proc.kill()
```

### 4.2 Async Cancellation

```python
import asyncio

async def search_with_timeout(pattern: str, path: str, timeout: float):
    proc = await asyncio.create_subprocess_exec(
        'rg', '--json', pattern, path,
        stdout=asyncio.subprocess.PIPE
    )

    try:
        async with asyncio.timeout(timeout):
            async for line in proc.stdout:
                yield json.loads(line)
    except asyncio.TimeoutError:
        proc.terminate()
        raise
    finally:
        if proc.returncode is None:
            proc.kill()
```

### 4.3 Context Manager Pattern

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class SearchContext:
    pattern: str
    path: str
    _proc: Optional[subprocess.Popen] = None

    def __enter__(self):
        self._proc = subprocess.Popen(
            ['rg', '--json', self.pattern, self.path],
            stdout=subprocess.PIPE
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._proc:
            self._proc.terminate()
            self._proc.wait()

    def __iter__(self):
        for line in self._proc.stdout:
            yield json.loads(line)

# Usage
with SearchContext("TODO", ".") as search:
    for match in search:
        if should_stop():
            break  # Context manager handles cleanup
```

---

## 5. Type System Integration

### 5.1 Type Definitions

```python
from dataclasses import dataclass
from typing import Optional, List
from pathlib import Path

@dataclass
class MatchLocation:
    """Location of a match within a line."""
    start: int
    end: int
    text: str

@dataclass
class Match:
    """A single match result from ripgrep."""
    path: Path
    line_number: int
    line_content: str
    matches: List[MatchLocation]
    byte_offset: Optional[int] = None

    @classmethod
    def from_json(cls, data: dict) -> 'Match':
        """Parse from ripgrep --json output."""
        d = data['data']
        return cls(
            path=Path(d['path']['text']),
            line_number=d['line_number'],
            line_content=d['lines']['text'].rstrip('\n'),
            matches=[
                MatchLocation(
                    start=m['start'],
                    end=m['end'],
                    text=m['match']['text']
                )
                for m in d['submatches']
            ],
            byte_offset=d.get('absolute_offset')
        )
```

### 5.2 Protocol/ABC Definitions

```python
from typing import Protocol, Iterator, AsyncIterator
from abc import ABC, abstractmethod

class SearchResult(Protocol):
    """Protocol for search results."""
    path: Path
    line_number: int
    line_content: str

class Searcher(ABC):
    """Abstract base for search implementations."""

    @abstractmethod
    def search(self, pattern: str, path: str) -> Iterator[SearchResult]:
        """Synchronous search."""
        ...

    @abstractmethod
    async def search_async(self, pattern: str, path: str) -> AsyncIterator[SearchResult]:
        """Asynchronous search."""
        ...
```

### 5.3 Type Stub File (.pyi)

```python
# ripgrep.pyi
from typing import Iterator, AsyncIterator, Optional, List, overload
from pathlib import Path

class Match:
    path: Path
    line_number: int
    line_content: str
    matches: List[MatchLocation]
    byte_offset: Optional[int]

class Grep:
    def __init__(self, binary_path: str = "rg") -> None: ...

    @overload
    def search(
        self,
        pattern: str,
        path: str = ".",
        *,
        ignore_case: bool = False,
        context: int = 0,
    ) -> Iterator[Match]: ...

    @overload
    def search(
        self,
        pattern: str,
        path: str = ".",
        *,
        files_only: bool = True,
    ) -> Iterator[Path]: ...

    async def search_async(
        self,
        pattern: str,
        path: str = ".",
        **kwargs
    ) -> AsyncIterator[Match]: ...
```

---

## 6. Packaging and Distribution

### 6.1 Pure Python Package (Tier A)

```toml
# pyproject.toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "ripgrep-py"
version = "0.1.0"
requires-python = ">=3.9"
dependencies = []

[project.optional-dependencies]
async = ["anyio>=4.0"]
```

### 6.2 Native Extension Package (Tier C/D)

```toml
# pyproject.toml for PyO3
[build-system]
requires = ["maturin>=1.0,<2.0"]
build-backend = "maturin"

[project]
name = "ripgrep-native"
requires-python = ">=3.9"
classifiers = [
    "Programming Language :: Rust",
    "Programming Language :: Python :: Implementation :: CPython",
]

[tool.maturin]
features = ["pyo3/extension-module"]
```

### 6.3 Platform Matrix

| Platform | Architecture | Support Level |
|----------|--------------|---------------|
| Linux | x86_64 | Primary |
| Linux | aarch64 | Primary |
| macOS | x86_64 | Primary |
| macOS | arm64 | Primary |
| Windows | x86_64 | Primary |
| Linux | armv7 | Secondary |
| Linux | i686 | Secondary |

---

## 7. Performance Pitfalls

### 7.1 Common Mistakes

| Pitfall | Impact | Solution |
|---------|--------|----------|
| Creating Python objects per match | High overhead | Batch processing, lazy evaluation |
| Buffering entire output | Memory explosion | Stream processing |
| Synchronous in async context | Blocking event loop | Use `asyncio.subprocess` |
| String encoding/decoding | CPU overhead | Use bytes where possible |
| GIL contention | Parallelism blocked | Release GIL in FFI, use multiprocessing |

### 7.2 Optimization Strategies

```python
# BAD: Creates many objects
def search_bad(pattern, path):
    result = subprocess.run(['rg', '--json', pattern, path], capture_output=True)
    matches = []
    for line in result.stdout.decode().splitlines():
        data = json.loads(line)
        if data['type'] == 'match':
            matches.append(Match.from_json(data))  # Object per match
    return matches

# GOOD: Streaming, minimal objects
def search_good(pattern, path):
    proc = subprocess.Popen(['rg', '--json', pattern, path], stdout=subprocess.PIPE)
    for line in proc.stdout:  # Streaming
        data = json.loads(line)
        if data['type'] == 'match':
            yield data  # Yield dict, caller decides on object creation
```

### 7.3 Memory-Efficient Patterns

```python
import mmap
from typing import Iterator

def search_large_output(pattern: str, path: str) -> Iterator[dict]:
    """Handle large outputs without memory explosion."""
    proc = subprocess.Popen(
        ['rg', '--json', pattern, path],
        stdout=subprocess.PIPE,
        bufsize=1  # Line buffered
    )

    # Process one line at a time
    for line in proc.stdout:
        if line:  # Skip empty lines
            yield json.loads(line)

    proc.wait()
```

---

## 8. Security Considerations

### 8.1 Command Injection Prevention

```python
import shlex
from pathlib import Path

def safe_search(pattern: str, path: str) -> Iterator[dict]:
    """Prevent command injection."""
    # Validate path
    resolved = Path(path).resolve()
    if not resolved.exists():
        raise ValueError(f"Path does not exist: {path}")

    # Use list form (no shell=True)
    cmd = ['rg', '--json', '--', pattern, str(resolved)]

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=False)
    # ...
```

### 8.2 Path Traversal Prevention

```python
def validate_path(path: str, allowed_root: str = ".") -> Path:
    """Ensure path is within allowed directory."""
    root = Path(allowed_root).resolve()
    target = (root / path).resolve()

    if not str(target).startswith(str(root)):
        raise ValueError(f"Path escapes root: {path}")

    return target
```

---

## 9. Target Runtime Profile Summary

```yaml
language: python
versions: ">=3.9"
runtime: cpython

subprocess:
  module: subprocess
  sync_api: subprocess.run, Popen
  async_api: asyncio.create_subprocess_exec
  streaming: Popen with PIPE iteration
  overhead: ~5ms spawn, ~10ms rg startup

ffi_options:
  recommended: pyo3
  alternatives:
    - cffi
    - ctypes
  build_tool: maturin

streaming:
  sync: generators (yield)
  async: async generators (async for)
  backpressure: manual with buffer limits

cancellation:
  subprocess: proc.terminate() / proc.kill()
  async: asyncio.Task.cancel()
  pattern: context managers

types:
  dataclasses: true
  protocols: true
  type_stubs: recommended

packaging:
  pure_python: pyproject.toml + hatch/setuptools
  native: maturin
  distribution: PyPI wheels
  platforms:
    - linux-x86_64
    - linux-aarch64
    - macos-x86_64
    - macos-arm64
    - windows-x86_64

performance_pitfalls:
  - per_match_object_creation
  - full_output_buffering
  - sync_in_async_context
  - unnecessary_encoding
  - gil_contention

security:
  - no_shell_true
  - validate_paths
  - use_list_args
```

---

*Phase 2 Complete. Proceed to Phase 3: Tier Adapter Specifications.*

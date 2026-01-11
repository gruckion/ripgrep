# Phase 3: Tier Adapter Specifications

## Overview

This document defines the four standardized integration tiers for CLI→SDK generation. Each tier represents a different trade-off between performance, complexity, and portability.

---

## Tier A: Subprocess Adapter

### Description

The simplest integration tier. Each SDK call spawns the CLI as a subprocess, passes arguments, captures output, and parses results.

### Architecture

```
┌─────────────────┐         ┌─────────────────┐
│   Python SDK    │ spawn   │    rg binary    │
│                 │────────▶│                 │
│  search(...)    │         │  --json mode    │
│                 │◀────────│                 │
│  parse JSON     │ stdout  │                 │
└─────────────────┘         └─────────────────┘
```

### Specification

```yaml
tier: A
name: subprocess
overhead:
  cold_start: 5-20ms (process spawn + CLI startup)
  warm: N/A (no warm state)
  per_call: 5-20ms

interface:
  input: command-line arguments
  output: stdout (structured) + stderr (errors) + exit code
  protocol: operating system process API

requirements:
  - CLI binary in PATH or specified location
  - Structured output mode (--json preferred)
  - Deterministic exit codes

capabilities:
  streaming: yes (stdout pipe iteration)
  cancellation: yes (SIGTERM/SIGKILL)
  concurrency: yes (multiple processes)
  state_sharing: no
```

### Implementation Pattern

```python
class TierAAdapter:
    """Subprocess-based CLI adapter."""

    def __init__(self, binary: str = "rg"):
        self.binary = binary

    def execute(
        self,
        args: List[str],
        stdin: Optional[bytes] = None,
        timeout: Optional[float] = None
    ) -> Iterator[dict]:
        """Execute CLI and stream parsed results."""
        cmd = [self.binary, "--json"] + args

        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE if stdin else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        try:
            if stdin:
                proc.stdin.write(stdin)
                proc.stdin.close()

            for line in proc.stdout:
                yield json.loads(line)

            proc.wait(timeout=timeout)

            if proc.returncode == 2:
                raise CLIError(proc.stderr.read().decode())

        except:
            proc.kill()
            raise
```

### When to Use

- Quick integration with any CLI
- Low call frequency (< 100 calls/second)
- Portability is critical
- No control over CLI source

---

## Tier B: Daemon Adapter

### Description

A persistent background process that stays running between calls. The SDK communicates with the daemon via IPC (stdin/stdout, Unix sockets, or TCP).

### Architecture

```
┌─────────────────┐                  ┌─────────────────┐
│   Python SDK    │     request      │  Daemon Process │
│                 │─────────────────▶│                 │
│  RPC client     │                  │  grep crate     │
│                 │◀─────────────────│  (loaded once)  │
│  parse response │     response     │                 │
└─────────────────┘                  └─────────────────┘
                         │
                         │ persistent
                         ▼
              ┌─────────────────────┐
              │   Cached State      │
              │ - compiled regex    │
              │ - ignore patterns   │
              │ - file type defs    │
              └─────────────────────┘
```

### Specification

```yaml
tier: B
name: daemon
overhead:
  cold_start: 50-200ms (daemon startup)
  warm: 0.1-5ms (IPC round-trip)
  per_call: 0.1-5ms (after warm)

interface:
  input: structured messages (JSON/MessagePack/Protobuf)
  output: structured messages
  protocol: custom RPC over stdio/socket

requirements:
  - Daemon binary or wrapper around library
  - Message framing protocol
  - Lifecycle management

capabilities:
  streaming: yes (chunked responses)
  cancellation: yes (cancel message or connection close)
  concurrency: yes (multiplexed or connection pool)
  state_sharing: yes (regex cache, config)
```

### Protocol Design

#### Message Format (JSON-RPC style)

```json
// Request
{
  "id": 1,
  "method": "search",
  "params": {
    "pattern": "TODO",
    "path": ".",
    "options": {
      "ignore_case": true,
      "context": 2
    }
  }
}

// Response (streaming)
{"id": 1, "type": "match", "data": {...}}
{"id": 1, "type": "match", "data": {...}}
{"id": 1, "type": "done", "stats": {...}}

// Error
{"id": 1, "type": "error", "message": "Invalid regex"}
```

#### Binary Protocol (for performance)

```
┌────────────────────────────────────────────┐
│ Header (8 bytes)                           │
│ ┌──────────┬──────────┬──────────────────┐ │
│ │ Magic(2) │ Type(1)  │ Length(4)  │Fl(1)│ │
│ │ 0x52 0x47│ 0x01=req │ big-endian │flags│ │
│ └──────────┴──────────┴──────────────────┘ │
├────────────────────────────────────────────┤
│ Payload (MessagePack encoded)              │
│ {...}                                      │
└────────────────────────────────────────────┘
```

### Implementation Pattern

```python
class TierBAdapter:
    """Daemon-based CLI adapter with connection pooling."""

    def __init__(self, socket_path: str = "/tmp/rg-daemon.sock"):
        self.socket_path = socket_path
        self._connection: Optional[socket.socket] = None
        self._request_id = 0

    def _ensure_daemon(self):
        """Start daemon if not running."""
        if not Path(self.socket_path).exists():
            subprocess.Popen(
                ['rg-daemon', '--socket', self.socket_path],
                start_new_session=True
            )
            time.sleep(0.1)  # Wait for startup

    def _connect(self) -> socket.socket:
        if self._connection is None:
            self._ensure_daemon()
            self._connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self._connection.connect(self.socket_path)
        return self._connection

    def execute(self, method: str, params: dict) -> Iterator[dict]:
        """Execute RPC call and stream results."""
        conn = self._connect()
        self._request_id += 1

        request = {
            "id": self._request_id,
            "method": method,
            "params": params
        }

        # Send request
        data = json.dumps(request).encode() + b'\n'
        conn.sendall(data)

        # Stream responses
        buffer = b''
        while True:
            chunk = conn.recv(4096)
            buffer += chunk

            while b'\n' in buffer:
                line, buffer = buffer.split(b'\n', 1)
                response = json.loads(line)

                if response.get('type') == 'done':
                    return
                elif response.get('type') == 'error':
                    raise CLIError(response['message'])
                else:
                    yield response
```

### Daemon Implementation (Rust)

```rust
// Simplified daemon implementation using grep crate
use grep::regex::RegexMatcher;
use grep::searcher::Searcher;
use std::io::{BufRead, BufReader, Write};
use std::os::unix::net::UnixListener;

fn handle_request(request: Request) -> impl Iterator<Item = Response> {
    let matcher = RegexMatcher::new(&request.pattern).unwrap();
    let mut searcher = Searcher::new();

    // Use cached matcher if pattern unchanged
    // ...

    searcher.search_path(&matcher, &request.path, MySink::new())
}

fn main() {
    let listener = UnixListener::bind("/tmp/rg-daemon.sock").unwrap();

    for stream in listener.incoming() {
        let mut stream = stream.unwrap();
        let reader = BufReader::new(&stream);

        for line in reader.lines() {
            let request: Request = serde_json::from_str(&line.unwrap()).unwrap();

            for response in handle_request(request) {
                writeln!(stream, "{}", serde_json::to_string(&response).unwrap());
            }
        }
    }
}
```

### When to Use

- High call frequency (> 100 calls/second)
- Need to cache compiled state (regex, config)
- Can tolerate daemon lifecycle management
- Want warm performance without FFI complexity

---

## Tier C: Shared Library Adapter

### Description

The CLI functionality is compiled as a shared library (.so/.dylib/.dll) with a C-compatible ABI. The SDK loads this library and calls functions directly.

### Architecture

```
┌─────────────────┐                    ┌─────────────────┐
│   Python SDK    │  FFI call          │  libripgrep.so  │
│                 │───────────────────▶│                 │
│  cffi/ctypes    │                    │  C ABI wrapper  │
│                 │◀───────────────────│  grep crate     │
│  convert types  │  return/callback   │                 │
└─────────────────┘                    └─────────────────┘
```

### Specification

```yaml
tier: C
name: shared_library
overhead:
  cold_start: 10-50ms (library load + initialization)
  warm: 1-100µs (function call)
  per_call: 1-100µs

interface:
  input: C types (pointers, primitives)
  output: C types + callbacks
  protocol: C ABI (cdecl/stdcall)

requirements:
  - Shared library with C ABI
  - Header file or ABI documentation
  - Platform-specific builds

capabilities:
  streaming: yes (callbacks)
  cancellation: limited (cooperative)
  concurrency: depends on implementation
  state_sharing: yes (in-process)
```

### C ABI Design

```c
// ripgrep.h

#ifndef RIPGREP_H
#define RIPGREP_H

#include <stdint.h>
#include <stddef.h>

// Opaque handle types
typedef struct RgSearcher RgSearcher;
typedef struct RgMatcher RgMatcher;

// Match data structure
typedef struct {
    const char* path;
    size_t path_len;
    uint64_t line_number;
    const uint8_t* line_data;
    size_t line_len;
    size_t match_start;
    size_t match_end;
} RgMatch;

// Callback type
typedef int (*RgMatchCallback)(const RgMatch* match, void* user_data);

// Error codes
typedef enum {
    RG_OK = 0,
    RG_ERR_INVALID_PATTERN = 1,
    RG_ERR_INVALID_PATH = 2,
    RG_ERR_IO = 3,
} RgError;

// API functions
RgError rg_matcher_new(const char* pattern, RgMatcher** out);
void rg_matcher_free(RgMatcher* matcher);

RgError rg_searcher_new(RgSearcher** out);
void rg_searcher_free(RgSearcher* searcher);

RgError rg_search(
    RgSearcher* searcher,
    RgMatcher* matcher,
    const char* path,
    RgMatchCallback callback,
    void* user_data
);

const char* rg_error_message(RgError err);

#endif
```

### Implementation Pattern

```python
import ctypes
from ctypes import c_char_p, c_size_t, c_uint64, c_void_p, CFUNCTYPE, POINTER, Structure

class RgMatch(Structure):
    _fields_ = [
        ("path", c_char_p),
        ("path_len", c_size_t),
        ("line_number", c_uint64),
        ("line_data", POINTER(ctypes.c_uint8)),
        ("line_len", c_size_t),
        ("match_start", c_size_t),
        ("match_end", c_size_t),
    ]

MatchCallback = CFUNCTYPE(ctypes.c_int, POINTER(RgMatch), c_void_p)

class TierCAdapter:
    """Shared library adapter using ctypes."""

    def __init__(self, lib_path: str = "libripgrep.so"):
        self.lib = ctypes.CDLL(lib_path)
        self._setup_functions()

    def _setup_functions(self):
        # rg_matcher_new
        self.lib.rg_matcher_new.argtypes = [c_char_p, POINTER(c_void_p)]
        self.lib.rg_matcher_new.restype = ctypes.c_int

        # rg_search
        self.lib.rg_search.argtypes = [c_void_p, c_void_p, c_char_p, MatchCallback, c_void_p]
        self.lib.rg_search.restype = ctypes.c_int

    def search(self, pattern: str, path: str) -> List[dict]:
        results = []

        @MatchCallback
        def callback(match, user_data):
            results.append({
                'path': match.contents.path.decode(),
                'line_number': match.contents.line_number,
                'line': bytes(match.contents.line_data[:match.contents.line_len]).decode(),
                'match_start': match.contents.match_start,
                'match_end': match.contents.match_end,
            })
            return 1  # Continue

        matcher = c_void_p()
        self.lib.rg_matcher_new(pattern.encode(), ctypes.byref(matcher))

        searcher = c_void_p()
        self.lib.rg_searcher_new(ctypes.byref(searcher))

        try:
            self.lib.rg_search(searcher, matcher, path.encode(), callback, None)
        finally:
            self.lib.rg_matcher_free(matcher)
            self.lib.rg_searcher_free(searcher)

        return results
```

### When to Use

- Maximum performance is critical
- Can build and distribute native libraries
- CLI has or can have a library form
- Target language has good FFI support

---

## Tier D: Native Extension Adapter

### Description

Direct integration into the target language runtime using language-specific binding mechanisms (PyO3 for Python, N-API for Node, JNI for Java).

### Architecture

```
┌─────────────────┐
│   Python SDK    │
│                 │
│  import ripgrep │
│                 │
│  Native Python  │
│  extension      │
│  ┌───────────┐  │
│  │   PyO3    │  │
│  │   Rust    │  │
│  │   grep    │  │
│  └───────────┘  │
└─────────────────┘
```

### Specification

```yaml
tier: D
name: native_extension
overhead:
  cold_start: 1-10ms (module import)
  warm: 0.1-10µs (native call)
  per_call: 0.1-10µs

interface:
  input: native language types
  output: native language types
  protocol: language-specific ABI

requirements:
  - Language-specific binding framework
  - Build tooling (maturin, node-gyp, etc.)
  - Platform-specific compilation

capabilities:
  streaming: yes (native iterators)
  cancellation: yes (native mechanisms)
  concurrency: yes (can release GIL, etc.)
  state_sharing: yes (in-process)
```

### Implementation Pattern (PyO3)

```rust
// src/lib.rs
use pyo3::prelude::*;
use pyo3::types::PyIterator;
use grep::regex::RegexMatcher;
use grep::searcher::{Searcher, sinks};

#[pyclass]
struct Match {
    #[pyo3(get)]
    path: String,
    #[pyo3(get)]
    line_number: u64,
    #[pyo3(get)]
    line: String,
    #[pyo3(get)]
    match_start: usize,
    #[pyo3(get)]
    match_end: usize,
}

#[pyclass]
struct SearchIterator {
    // Internal state
}

#[pymethods]
impl SearchIterator {
    fn __iter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> {
        slf
    }

    fn __next__(mut slf: PyRefMut<'_, Self>) -> Option<Match> {
        // Return next match or None
    }
}

#[pyfunction]
fn search(py: Python, pattern: &str, path: &str) -> PyResult<SearchIterator> {
    // Release GIL during search
    py.allow_threads(|| {
        // Perform search
    })
}

#[pymodule]
fn ripgrep(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(search, m)?)?;
    m.add_class::<Match>()?;
    Ok(())
}
```

### When to Use

- Absolute maximum performance required
- Tight integration with language runtime
- Can maintain language-specific bindings
- Worth the complexity for the use case

---

## Tier Selection Algorithm

```python
def select_tier(
    cli_profile: SourceProfile,
    target_profile: TargetProfile,
    requirements: Requirements
) -> Tier:
    """Select optimal integration tier."""

    # Check hard constraints
    if requirements.no_binary_dependency:
        return Tier.A  # Must use subprocess

    if not cli_profile.has_library_api and not cli_profile.structured_output:
        return Tier.A  # Can only use subprocess

    # Check performance requirements
    if requirements.latency_p99_ms < 1:
        if cli_profile.has_library_api:
            if target_profile.has_native_bindings:
                return Tier.D
            else:
                return Tier.C
        else:
            return Tier.B  # Best we can do without library

    if requirements.latency_p99_ms < 10:
        if cli_profile.can_daemon:
            return Tier.B
        else:
            return Tier.A

    # Default to simplest
    return Tier.A
```

---

## Tier Comparison Matrix

| Aspect | Tier A | Tier B | Tier C | Tier D |
|--------|--------|--------|--------|--------|
| **Complexity** | Low | Medium | High | High |
| **Setup Effort** | None | Medium | High | High |
| **Cold Start** | 5-20ms | 50-200ms | 10-50ms | 1-10ms |
| **Warm Latency** | 5-20ms | 0.1-5ms | 1-100µs | 0.1-10µs |
| **Throughput** | ~50/s | ~1000/s | ~10000/s | ~100000/s |
| **Memory** | Per-process | Shared daemon | In-process | In-process |
| **Distribution** | Binary in PATH | Binary + daemon | .so/.dll | Wheel/npm |
| **Portability** | Excellent | Good | Medium | Medium |
| **Maintenance** | Low | Medium | High | High |

---

*Phase 3 Complete. Proceed to Phase 4: CIDL Specification.*

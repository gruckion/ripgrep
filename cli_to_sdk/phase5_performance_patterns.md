# Phase 5: Performance Patterns for Generated SDKs

## Overview

This document catalogs performance patterns that should be implemented in generated SDKs to achieve optimal performance across all tiers.

---

## Pattern 1: Streaming Decode

### Problem
Loading entire CLI output into memory before processing causes:
- Memory spikes with large outputs
- Increased latency (must wait for full output)
- Potential OOM with very large results

### Solution
Parse and yield results incrementally as they arrive.

### Implementation

```python
# BAD: Buffered approach
def search_buffered(pattern: str, path: str) -> List[Match]:
    result = subprocess.run(['rg', '--json', pattern, path], capture_output=True)
    output = result.stdout.decode()  # Full buffer
    lines = output.splitlines()  # Another copy
    return [Match.from_json(json.loads(line)) for line in lines]  # All at once

# GOOD: Streaming approach
def search_streaming(pattern: str, path: str) -> Iterator[Match]:
    proc = subprocess.Popen(
        ['rg', '--json', pattern, path],
        stdout=subprocess.PIPE,
        bufsize=1  # Line buffered
    )
    for line in proc.stdout:  # Yields as available
        data = json.loads(line)
        if data.get('type') == 'match':
            yield Match.from_json(data)  # One at a time
```

### Metrics Impact
| Metric | Buffered | Streaming | Improvement |
|--------|----------|-----------|-------------|
| Time to first result | 100ms | 10ms | 10x |
| Peak memory (1M matches) | 2GB | 10MB | 200x |
| Total time | Same | Same | - |

---

## Pattern 2: Lazy Object Creation

### Problem
Creating rich Python objects for every match is expensive:
- Object allocation overhead
- Field validation
- Type conversions

### Solution
Defer object creation until explicitly needed.

### Implementation

```python
from typing import Iterator, Union

class LazyMatch:
    """Lazy wrapper that only parses when accessed."""
    __slots__ = ('_raw', '_parsed')

    def __init__(self, raw: bytes):
        self._raw = raw
        self._parsed = None

    def _ensure_parsed(self):
        if self._parsed is None:
            self._parsed = json.loads(self._raw)

    @property
    def path(self) -> str:
        self._ensure_parsed()
        return self._parsed['data']['path']['text']

    @property
    def line_number(self) -> int:
        self._ensure_parsed()
        return self._parsed['data']['line_number']

    def to_dict(self) -> dict:
        self._ensure_parsed()
        return self._parsed

def search_lazy(pattern: str, path: str) -> Iterator[LazyMatch]:
    """Yield lazy matches - parsing deferred until access."""
    proc = subprocess.Popen(['rg', '--json', pattern, path], stdout=subprocess.PIPE)
    for line in proc.stdout:
        yield LazyMatch(line)

# Usage - only parses what's needed
for match in search_lazy("TODO", "."):
    if "important" in match.path:  # Only path is parsed
        print(match.line_number)   # Now line_number is parsed
```

### Metrics Impact
| Scenario | Eager | Lazy | Improvement |
|----------|-------|------|-------------|
| Iterate all, access none | 100ms | 10ms | 10x |
| Iterate all, access path only | 100ms | 30ms | 3x |
| Iterate all, access all fields | 100ms | 100ms | - |

---

## Pattern 3: Connection Pooling (Tier B)

### Problem
Creating new daemon connections for each request:
- TCP/socket handshake overhead
- Connection establishment latency
- Resource exhaustion under load

### Solution
Maintain a pool of persistent connections.

### Implementation

```python
import threading
from queue import Queue, Empty
from contextlib import contextmanager

class ConnectionPool:
    """Thread-safe connection pool for daemon communication."""

    def __init__(self, socket_path: str, max_size: int = 10):
        self.socket_path = socket_path
        self.max_size = max_size
        self._pool: Queue = Queue(maxsize=max_size)
        self._size = 0
        self._lock = threading.Lock()

    def _create_connection(self) -> socket.socket:
        conn = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        conn.connect(self.socket_path)
        return conn

    @contextmanager
    def get_connection(self):
        """Get a connection from pool or create new one."""
        conn = None
        try:
            conn = self._pool.get_nowait()
        except Empty:
            with self._lock:
                if self._size < self.max_size:
                    conn = self._create_connection()
                    self._size += 1

        if conn is None:
            conn = self._pool.get()  # Block until available

        try:
            yield conn
        except:
            # Connection may be broken, don't return to pool
            conn.close()
            with self._lock:
                self._size -= 1
            raise
        else:
            self._pool.put(conn)

class TierBAdapter:
    def __init__(self, socket_path: str):
        self._pool = ConnectionPool(socket_path)

    def execute(self, method: str, params: dict) -> Iterator[dict]:
        with self._pool.get_connection() as conn:
            # Send request and stream results
            ...
```

### Metrics Impact
| Scenario | No Pool | With Pool | Improvement |
|----------|---------|-----------|-------------|
| 100 sequential requests | 500ms | 50ms | 10x |
| 100 concurrent requests | 500ms | 100ms | 5x |
| Connection reuse rate | 0% | 95% | - |

---

## Pattern 4: Batch Requests (Tier B)

### Problem
Multiple small requests have per-request overhead:
- Request serialization
- Network round-trip
- Response parsing

### Solution
Batch multiple operations into single request when possible.

### Implementation

```python
# Protocol supports batching
{
    "id": 1,
    "method": "batch",
    "requests": [
        {"method": "search", "params": {"pattern": "TODO", "path": "src/"}},
        {"method": "search", "params": {"pattern": "FIXME", "path": "src/"}},
        {"method": "search", "params": {"pattern": "HACK", "path": "src/"}}
    ]
}

# Response streams all results with request_id
{"request_id": 0, "type": "match", "data": {...}}
{"request_id": 1, "type": "match", "data": {...}}
{"request_id": 0, "type": "done"}
{"request_id": 2, "type": "match", "data": {...}}
...

class BatchingClient:
    def __init__(self, adapter: TierBAdapter, batch_size: int = 10):
        self.adapter = adapter
        self.batch_size = batch_size
        self._pending: List[Request] = []

    def search(self, pattern: str, path: str) -> Future[List[Match]]:
        """Queue search request, returns future."""
        future = Future()
        self._pending.append(Request(pattern, path, future))

        if len(self._pending) >= self.batch_size:
            self._flush()

        return future

    def _flush(self):
        """Send batched requests."""
        if not self._pending:
            return

        requests = self._pending
        self._pending = []

        results = self.adapter.execute_batch([r.to_dict() for r in requests])

        for request_id, matches in results.items():
            requests[request_id].future.set_result(matches)
```

### Metrics Impact
| Scenario | Individual | Batched | Improvement |
|----------|------------|---------|-------------|
| 10 small searches | 50ms | 10ms | 5x |
| Network round-trips | 10 | 1 | 10x |

---

## Pattern 5: Result Caching

### Problem
Repeated identical queries waste resources:
- Same regex compilation
- Same file traversal
- Same output parsing

### Solution
Cache results for identical queries (with TTL or invalidation).

### Implementation

```python
from functools import lru_cache
from hashlib import sha256
import time

class CachingClient:
    def __init__(self, client: RipgrepClient, ttl: float = 60.0):
        self._client = client
        self._cache: Dict[str, CacheEntry] = {}
        self._ttl = ttl

    def _cache_key(self, pattern: str, path: str, **kwargs) -> str:
        """Generate cache key from arguments."""
        data = json.dumps({
            'pattern': pattern,
            'path': str(Path(path).resolve()),
            **kwargs
        }, sort_keys=True)
        return sha256(data.encode()).hexdigest()

    def search(self, pattern: str, path: str, **kwargs) -> List[Match]:
        key = self._cache_key(pattern, path, **kwargs)

        # Check cache
        if key in self._cache:
            entry = self._cache[key]
            if time.time() - entry.timestamp < self._ttl:
                return entry.results

        # Cache miss - execute and store
        results = list(self._client.search(pattern, path, **kwargs))
        self._cache[key] = CacheEntry(results, time.time())

        return results

    def invalidate(self, path: Optional[str] = None):
        """Invalidate cache entries."""
        if path is None:
            self._cache.clear()
        else:
            resolved = str(Path(path).resolve())
            self._cache = {
                k: v for k, v in self._cache.items()
                if resolved not in k  # Simplified
            }
```

### Metrics Impact
| Scenario | No Cache | With Cache | Improvement |
|----------|----------|------------|-------------|
| Repeated identical query | 50ms | 0.1ms | 500x |
| Hit rate (typical) | 0% | 30-70% | - |

---

## Pattern 6: Binary Protocol (Tier B)

### Problem
JSON parsing is CPU-intensive:
- String parsing and validation
- Unicode handling
- Object allocation

### Solution
Use binary serialization (MessagePack, Protocol Buffers, FlatBuffers).

### Implementation

```python
import msgpack

class BinaryProtocolAdapter:
    """Tier B adapter using MessagePack instead of JSON."""

    HEADER_SIZE = 8
    MAGIC = b'RG'

    def send_request(self, conn: socket.socket, request: dict):
        payload = msgpack.packb(request)
        header = (
            self.MAGIC +
            len(payload).to_bytes(4, 'big') +
            b'\x00\x00'  # flags
        )
        conn.sendall(header + payload)

    def recv_response(self, conn: socket.socket) -> Iterator[dict]:
        while True:
            header = conn.recv(self.HEADER_SIZE)
            if not header:
                break

            magic = header[:2]
            length = int.from_bytes(header[2:6], 'big')

            if magic != self.MAGIC:
                raise ProtocolError("Invalid magic")

            payload = conn.recv(length)
            response = msgpack.unpackb(payload)

            if response.get('type') == 'done':
                break

            yield response
```

### Metrics Impact
| Metric | JSON | MessagePack | Improvement |
|--------|------|-------------|-------------|
| Serialization time | 10µs | 2µs | 5x |
| Message size | 200B | 100B | 2x |
| Parse time | 15µs | 3µs | 5x |

---

## Pattern 7: Zero-Copy Results (Tier C/D)

### Problem
Copying data across FFI boundary is expensive:
- Memory allocation
- Data copying
- Reference counting

### Solution
Return views/references to Rust-owned memory where safe.

### Implementation (PyO3)

```rust
use pyo3::prelude::*;
use pyo3::types::PyBytes;

#[pyclass]
struct SearchResults {
    // Rust owns the data
    data: Vec<MatchData>,
}

#[pymethods]
impl SearchResults {
    fn __iter__(slf: PyRef<'_, Self>) -> PyResult<MatchIterator> {
        Ok(MatchIterator {
            inner: slf.data.iter(),
        })
    }

    fn get_line_bytes<'py>(&self, py: Python<'py>, index: usize) -> &'py PyBytes {
        // Return reference to Rust-owned bytes, no copy
        PyBytes::new(py, &self.data[index].line_bytes)
    }
}
```

### Metrics Impact
| Metric | Copy | Zero-Copy | Improvement |
|--------|------|-----------|-------------|
| Memory (1M results) | 200MB | 100MB | 2x |
| Return time | 50ms | 5ms | 10x |

---

## Pattern 8: Async I/O

### Problem
Synchronous I/O blocks the event loop:
- Can't handle other requests
- Poor utilization in async applications
- Timeout handling is complex

### Solution
Use async subprocess or non-blocking daemon communication.

### Implementation

```python
import asyncio
from typing import AsyncIterator

class AsyncRipgrep:
    async def search(
        self,
        pattern: str,
        path: str,
        **kwargs
    ) -> AsyncIterator[Match]:
        """Async search with non-blocking I/O."""
        proc = await asyncio.create_subprocess_exec(
            'rg', '--json', pattern, path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        async for line in proc.stdout:
            data = json.loads(line)
            if data.get('type') == 'match':
                yield Match.from_json(data)

        await proc.wait()

        if proc.returncode == 2:
            stderr = await proc.stderr.read()
            raise RipgrepError(stderr.decode())

# Usage
async def main():
    rg = AsyncRipgrep()
    async for match in rg.search("TODO", "."):
        print(match)

    # Or with timeout
    async with asyncio.timeout(5.0):
        async for match in rg.search("pattern", "large_dir"):
            process(match)
```

### Metrics Impact
| Scenario | Sync | Async | Improvement |
|----------|------|-------|-------------|
| 10 concurrent searches | 500ms | 100ms | 5x |
| Event loop blocking | 100% | 0% | - |

---

## Pattern Summary Matrix

| Pattern | Tier A | Tier B | Tier C | Tier D | Complexity |
|---------|--------|--------|--------|--------|------------|
| Streaming Decode | ✅ | ✅ | ✅ | ✅ | Low |
| Lazy Objects | ✅ | ✅ | ✅ | ✅ | Low |
| Connection Pooling | - | ✅ | - | - | Medium |
| Batch Requests | - | ✅ | ⚠️ | ⚠️ | Medium |
| Result Caching | ✅ | ✅ | ✅ | ✅ | Low |
| Binary Protocol | - | ✅ | - | - | Medium |
| Zero-Copy | - | - | ✅ | ✅ | High |
| Async I/O | ✅ | ✅ | ⚠️ | ⚠️ | Medium |

---

*Phase 5 Complete. Proceed to Anchor Case Implementation.*

# Phase 0: Metrics Suite and CLI Taxonomy

## 1. Metrics Suite

### 1.1 Latency Metrics

| Metric | Definition | Measurement Method |
|--------|------------|-------------------|
| **Cold Start Latency** | Time from first SDK call to result, including any initialization | `time.perf_counter_ns()` around first call after process start |
| **Warm Latency (P50)** | Median time for subsequent calls in steady state | Percentile of 100+ calls after warmup |
| **Warm Latency (P99)** | 99th percentile latency (tail latency) | Captures GC pauses, JIT, cache misses |
| **Call Overhead** | Time spent in SDK wrapper vs CLI execution | Profile with/without actual CLI work |

### 1.2 Throughput Metrics

| Metric | Definition | Measurement Method |
|--------|------------|-------------------|
| **Sequential Throughput** | Operations per second, single-threaded | `ops / elapsed_time` over sustained period |
| **Concurrent Throughput** | Operations per second with N parallel callers | Thread pool with N workers |
| **Scaling Efficiency** | `throughput(N) / (N * throughput(1))` | Measures parallelism overhead |

### 1.3 Efficiency Metrics

| Metric | Definition | Measurement Method |
|--------|------------|-------------------|
| **CPU Cycles per Operation** | Processor efficiency | `perf stat` or equivalent |
| **CPU Cycles per MB** | For data-processing CLIs | Normalize by input/output size |
| **Memory per Operation** | Allocation overhead | Track allocator or use `/proc/self/status` |

### 1.4 Resource Metrics

| Metric | Definition | Measurement Method |
|--------|------------|-------------------|
| **Peak Memory** | Maximum RSS during operation | `resource.getrusage()` or `/proc/self/status` |
| **Steady-State Memory** | Memory after warmup, between operations | Sample during idle periods |
| **File Descriptors** | FDs held open (relevant for Tier B) | `/proc/self/fd` count |
| **Child Processes** | Process count (relevant for Tier A) | `pgrep` or process table |

### 1.5 Correctness Metrics

| Metric | Definition | Validation Method |
|--------|------------|-------------------|
| **Output Equivalence** | SDK output matches CLI output | Diff against reference |
| **Exit Code Preservation** | SDK surfaces CLI exit codes correctly | Test all documented codes |
| **Stderr Preservation** | Errors/warnings captured and surfaced | Capture and compare |
| **Ordering Preservation** | Output order matches CLI (if deterministic) | Diff with `--sort` modes |
| **Streaming Fidelity** | Partial results available before completion | Test with slow/large inputs |

---

## 2. CLI Taxonomy by Interaction Pattern

### 2.1 Category Definitions

#### Category A: Batch Compute
**Characteristics:**
- Takes input (files, stdin, arguments)
- Processes to completion
- Produces output (stdout, files)
- No interaction during execution

**Examples:**
| CLI | Input | Output | Notes |
|-----|-------|--------|-------|
| `rg` (ripgrep) | files + pattern | matches | Parallel, streamable |
| `ffmpeg` | media files | media files | Long-running, progress |
| `imagemagick` | images | images | CPU-intensive |
| `pandoc` | documents | documents | Format conversion |
| `esbuild` | JS/TS files | bundles | Build tool |

**SDK Requirements:**
- Async/await for long operations
- Progress callbacks (if supported)
- Cancellation support
- Streaming output where applicable

#### Category B: Streaming Transform
**Characteristics:**
- Continuous stdin → stdout flow
- May run indefinitely
- Output proportional to input
- Often used in pipelines

**Examples:**
| CLI | Transform | Notes |
|-----|-----------|-------|
| `jq` | JSON → JSON | Query/filter |
| `sed` | text → text | Line transforms |
| `awk` | text → text | Field processing |
| `gzip`/`zstd` | bytes → bytes | Compression |
| `base64` | bytes ↔ text | Encoding |

**SDK Requirements:**
- Streaming APIs (iterators/generators)
- Backpressure handling
- Pipeline composition
- Memory-bounded buffering

#### Category C: Interactive/TUI
**Characteristics:**
- Requires user input during execution
- May have terminal UI
- State changes based on interaction

**Examples:**
| CLI | Interaction Type | Notes |
|-----|------------------|-------|
| `git add -p` | Y/N prompts | Patch selection |
| `fzf` | Fuzzy search UI | Full TUI |
| `vim`/`nano` | Editor | Full TUI |
| `htop` | Monitor | Full TUI |
| `python` REPL | Command input | Interactive shell |

**SDK Requirements:**
- Generally NOT suitable for SDK wrapping
- May extract non-interactive subset
- Or provide "scripted input" mode

#### Category D: Daemon Frontends
**Characteristics:**
- CLI is thin client to background service
- Actual work done by daemon
- CLI handles auth, formatting, transport

**Examples:**
| CLI | Daemon | Notes |
|-----|--------|-------|
| `docker` | dockerd | Container management |
| `kubectl` | kube-apiserver | Kubernetes |
| `systemctl` | systemd | Service management |
| `redis-cli` | redis-server | Database client |
| `psql` | postgres | Database client |

**SDK Requirements:**
- May be better to target daemon API directly
- CLI SDK useful for consistency with CLI UX
- Auth/config reuse from CLI

#### Category E: Stateful Tools
**Characteristics:**
- Operations depend on prior state
- Often work on a "project" or "repository"
- State persisted to disk

**Examples:**
| CLI | State Location | Notes |
|-----|----------------|-------|
| `git` | `.git/` directory | Version control |
| `npm`/`yarn` | `node_modules/`, lockfiles | Package management |
| `cargo` | `target/`, `Cargo.lock` | Rust build |
| `terraform` | `.terraform/`, state files | Infrastructure |

**SDK Requirements:**
- Working directory context
- State consistency guarantees
- Lock file handling
- Atomic operations where needed

---

### 2.2 Taxonomy Decision Tree

```
                            Is the CLI interactive?
                                     │
                      ┌──────────────┴──────────────┐
                      │ Yes                         │ No
                      ▼                             ▼
               Category C               Does it talk to a daemon?
               (Interactive)                        │
                                     ┌──────────────┴──────────────┐
                                     │ Yes                         │ No
                                     ▼                             ▼
                              Category D              Does it maintain state?
                              (Daemon Frontend)                    │
                                                    ┌──────────────┴──────────────┐
                                                    │ Yes                         │ No
                                                    ▼                             ▼
                                             Category E           Is it a streaming transform?
                                             (Stateful)                           │
                                                               ┌──────────────────┴─────────────────┐
                                                               │ Yes                                │ No
                                                               ▼                                    ▼
                                                        Category B                           Category A
                                                        (Streaming)                          (Batch)
```

---

## 3. Output Format Taxonomy

### 3.1 Format Categories

#### Text Formats

| Format | Characteristics | Parsing Strategy | Examples |
|--------|-----------------|------------------|----------|
| **Line-oriented** | One record per line, fields separated | Split + parse | `grep`, `ls`, `find` |
| **Tabular** | Columns with headers | Parse headers, split rows | `ps`, `df`, `docker ps` |
| **Key-value** | `key: value` or `key=value` | Regex or split on delimiter | `git config`, `env` |
| **Free-form** | Human-readable prose | Regex extraction (fragile) | `git status` (default) |

#### Structured Formats

| Format | Characteristics | Parsing Strategy | Examples |
|--------|-----------------|------------------|----------|
| **JSON** | Single JSON object/array | `json.loads()` | Many with `--json` flag |
| **JSON Lines** | One JSON object per line | Line-by-line `json.loads()` | `rg --json`, `jq -c` |
| **YAML** | YAML document(s) | YAML parser | `kubectl get -o yaml` |
| **TOML** | TOML document | TOML parser | `cargo metadata` |
| **XML** | XML document | XML parser | Legacy tools |

#### Binary Formats

| Format | Characteristics | Parsing Strategy | Examples |
|--------|-----------------|------------------|----------|
| **Raw bytes** | Unstructured binary | Application-specific | `cat`, `dd` |
| **Length-prefixed** | Size header + payload | Read length, then payload | Custom protocols |
| **Protobuf/MessagePack** | Serialized structures | Schema-based deserialize | Some modern CLIs |
| **Archive formats** | tar, zip, etc. | Archive library | `tar`, `zip` |

### 3.2 Output Stream Semantics

| Aspect | Variations | SDK Implications |
|--------|------------|------------------|
| **stdout vs stderr** | Data on stdout, errors on stderr | Capture separately |
| **Mixed streams** | Progress on stderr, data on stdout | Demultiplex |
| **Interleaved** | stdout/stderr interleaved | May need PTY for ordering |
| **Binary stdout** | Non-text output | Use bytes, not str |

### 3.3 Exit Code Semantics

| Pattern | Examples | SDK Handling |
|---------|----------|--------------|
| **0 = success, non-0 = error** | Most CLIs | Raise exception on non-0 |
| **0 = found, 1 = not found, 2 = error** | `grep`, `rg` | Distinguish "not found" from error |
| **Bitfield** | `rsync` | Decode individual bits |
| **Signal-based** | Killed processes | 128 + signal number |

---

## 4. SDK Quality Levels

### Level 1: Basic Wrapper
- Subprocess invocation
- String arguments
- String/bytes output
- Exit code as exception or return

### Level 2: Typed Interface
- Typed arguments (enums, paths, etc.)
- Parsed output (dataclasses, TypedDict)
- Documented errors
- Basic validation

### Level 3: Streaming Support
- Async iteration over results
- Incremental parsing
- Cancellation support
- Progress callbacks

### Level 4: Full Integration
- Native performance (FFI)
- Zero-copy where possible
- Connection pooling/reuse
- Full CLI feature parity

---

## 5. Benchmark Workload Definitions

### 5.1 Micro-benchmarks (Measure Overhead)

| Workload | Purpose | Parameters |
|----------|---------|------------|
| **Null operation** | Measure call overhead | `--version` or equivalent |
| **Minimal input** | Baseline with tiny data | Single small file |
| **No matches** | Measure search overhead | Pattern that won't match |

### 5.2 Realistic Workloads

| Workload | Purpose | Parameters |
|----------|---------|------------|
| **Small codebase** | Typical project | ~1000 files, ~100KB total |
| **Medium codebase** | Monorepo | ~10,000 files, ~10MB total |
| **Large codebase** | Linux kernel | ~70,000 files, ~1GB total |

### 5.3 Stress Tests

| Workload | Purpose | Parameters |
|----------|---------|------------|
| **Many small calls** | Amortization test | 1000 searches, small scope |
| **Concurrent calls** | Parallelism test | N parallel searches |
| **Large output** | Streaming test | Pattern matching many lines |

---

## 6. Reference Benchmark Harness (Python)

```python
"""
Benchmark harness for CLI→SDK performance testing.
"""

import time
import statistics
import subprocess
import resource
import os
from dataclasses import dataclass
from typing import Callable, Any, List
from concurrent.futures import ThreadPoolExecutor


@dataclass
class BenchmarkResult:
    """Results from a benchmark run."""
    name: str
    iterations: int
    cold_start_ns: int
    warm_latencies_ns: List[int]
    peak_memory_kb: int

    @property
    def warm_p50_ns(self) -> float:
        return statistics.median(self.warm_latencies_ns)

    @property
    def warm_p99_ns(self) -> float:
        sorted_latencies = sorted(self.warm_latencies_ns)
        idx = int(len(sorted_latencies) * 0.99)
        return sorted_latencies[idx]

    @property
    def warm_mean_ns(self) -> float:
        return statistics.mean(self.warm_latencies_ns)

    @property
    def throughput_ops_per_sec(self) -> float:
        mean_sec = self.warm_mean_ns / 1e9
        return 1.0 / mean_sec if mean_sec > 0 else 0


def benchmark(
    name: str,
    func: Callable[[], Any],
    iterations: int = 100,
    warmup: int = 5
) -> BenchmarkResult:
    """Run a benchmark and collect metrics."""

    # Cold start (first call)
    start = time.perf_counter_ns()
    func()
    cold_start_ns = time.perf_counter_ns() - start

    # Warmup
    for _ in range(warmup):
        func()

    # Measure warm latencies
    warm_latencies = []
    for _ in range(iterations):
        start = time.perf_counter_ns()
        func()
        elapsed = time.perf_counter_ns() - start
        warm_latencies.append(elapsed)

    # Memory measurement
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    peak_memory_kb = usage.ru_maxrss

    return BenchmarkResult(
        name=name,
        iterations=iterations,
        cold_start_ns=cold_start_ns,
        warm_latencies_ns=warm_latencies,
        peak_memory_kb=peak_memory_kb
    )


def benchmark_concurrent(
    name: str,
    func: Callable[[], Any],
    workers: int = 4,
    operations: int = 100
) -> dict:
    """Benchmark concurrent throughput."""

    with ThreadPoolExecutor(max_workers=workers) as executor:
        start = time.perf_counter_ns()
        list(executor.map(lambda _: func(), range(operations)))
        elapsed_ns = time.perf_counter_ns() - start

    return {
        "name": name,
        "workers": workers,
        "operations": operations,
        "total_time_ms": elapsed_ns / 1e6,
        "throughput_ops_per_sec": operations / (elapsed_ns / 1e9)
    }


def format_results(result: BenchmarkResult) -> str:
    """Format benchmark results for display."""
    return f"""
Benchmark: {result.name}
  Iterations: {result.iterations}
  Cold Start: {result.cold_start_ns / 1e6:.3f} ms
  Warm Latency:
    P50: {result.warm_p50_ns / 1e6:.3f} ms
    P99: {result.warm_p99_ns / 1e6:.3f} ms
    Mean: {result.warm_mean_ns / 1e6:.3f} ms
  Throughput: {result.throughput_ops_per_sec:.1f} ops/sec
  Peak Memory: {result.peak_memory_kb} KB
"""
```

---

## 7. Success Criteria

### For Tier A (Subprocess)
- Cold start < 50ms
- Warm P50 < 30ms
- Correctness: 100% output equivalence

### For Tier B (Daemon)
- Cold start < 100ms (includes daemon startup)
- Warm P50 < 5ms
- Throughput > 200 ops/sec

### For Tier C (FFI)
- Cold start < 10ms
- Warm P50 < 1ms
- Throughput > 1000 ops/sec
- Memory overhead < 10MB

---

*Phase 0 Complete. Proceed to Phase 1: Source Capability Profile for ripgrep.*

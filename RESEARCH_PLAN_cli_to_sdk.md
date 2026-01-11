# Research Plan: CLI → SDK System

> **Objective:** Design a "CLI → SDK" system that yields the highest achievable performance for calling CLI capabilities from multiple target languages, using ripgrep→Python as an anchor use case.

---

## Table of Contents

1. [Facts (Starting Assumptions)](#facts-starting-assumptions)
2. [Constraints](#constraints)
3. [First Principles: Performance Upper Bound](#first-principles-performance-upper-bound)
4. [Research Phases](#research-phases)
5. [Source Language Considerations](#source-language-considerations)
6. [Target Language Considerations](#target-language-considerations)
7. [Standardization Strategy](#standardization-strategy)
8. [Anchor Case: ripgrep → Python](#anchor-case-ripgrep--python)
9. [Key Unknowns to Resolve](#key-unknowns-to-resolve)
10. [Deliverables](#deliverables)

---

## Facts (Starting Assumptions)

These are hypotheses to validate during research:

| # | Assumption | Validation Method |
|---|------------|-------------------|
| 1 | Many high-performance CLIs are written in systems languages (Rust/C/C++/Go) and expose functionality through CLI, not stable library ABI/API | Survey of top 100 CLI tools by GitHub stars |
| 2 | The ripgrep binary is heavily optimized relative to current Python bindings because it's built/tuned as standalone executable and avoids per-call FFI object marshalling | Benchmark comparison |
| 3 | There is no universal "SDK" definition for CLIs (thin subprocess wrapper vs native bindings with streaming, cancellation, progress, structured errors) | Literature review |
| 4 | Theoretical performance ceilings differ by integration strategy (subprocess < daemon < dynamic linking < embedding < reimplementation) | Theoretical analysis + benchmarks |
| 5 | CLIs vary dramatically in interface style (flags, subcommands, interactive TUI, streaming stdout, binary protocols, exit codes, config files, env vars) | Taxonomy creation |

---

## Constraints

### Hard Constraints (Physics and OS)

| Constraint | Description | Typical Cost |
|------------|-------------|--------------|
| **Process creation** | `exec`/`spawn` is non-trivial; varies by OS | 1-10ms (Linux), 10-50ms (Windows) |
| **IPC cost** | Pipes, stdout parsing, buffering, syscalls | ~1-5ms per call |
| **Serialization** | JSON/text parsing vs binary framing vs shared memory | 10-100µs per KB (JSON) |
| **Copying cost** | Cross-language memory movement, object materialization | Language-dependent |
| **Scheduling** | CPU affinity, I/O concurrency, thread contention | Workload-dependent |

### Product Constraints

| Constraint | Requirement |
|------------|-------------|
| **Arbitrary CLIs** | Must work for CLIs you don't control |
| **Multi-language SDKs** | Python, TypeScript, Java, Go, Rust, C#, etc. |
| **Semantic preservation** | Exit codes, stderr, ordering, streaming must be correct |
| **Cross-platform** | Linux, macOS, Windows |
| **User-friendly** | No build engineering required to use generated SDKs |

### Research Constraints

| Metric | Definition |
|--------|------------|
| **Latency per call** | Time from SDK method invocation to result |
| **Throughput** | Operations/second under concurrency |
| **Memory footprint** | Peak and steady-state memory usage |
| **Cold start vs warm** | First call vs subsequent calls |
| **Scaling** | Performance across cores/disks |

---

## First Principles: Performance Upper Bound

### The Integration Ladder

Performance ceiling depends on integration tier. Ordered by potential performance (best to worst):

```
┌─────────────────────────────────────────────────────────────────────┐
│ Tier 0: Pure library call in-process                                │
│         • No process boundary, minimal serialization                │
│         • Direct memory access                                      │
│         • Requires: library API + stable ABI or source integration  │
│         • Performance: ████████████████████ 100%                    │
├─────────────────────────────────────────────────────────────────────┤
│ Tier C: In-process FFI with coarse-grained calls                    │
│         • PyO3 / JNI / N-API / cgo                                  │
│         • Still in-process but incurs marshalling                   │
│         • Ceiling: batching, object creation minimization           │
│         • Performance: ████████████████░░░░ ~80%                    │
├─────────────────────────────────────────────────────────────────────┤
│ Tier B: Out-of-process but persistent (daemon/worker pool)          │
│         • Avoids repeated spawn, keeps caches warm                  │
│         • Requires: protocol, lifecycle, concurrency, security      │
│         • Performance: ████████████░░░░░░░░ ~60%                    │
├─────────────────────────────────────────────────────────────────────┤
│ Tier A: One-shot subprocess per call (baseline)                     │
│         • Maximum portability, minimal assumptions                  │
│         • Ceiling: spawn + serialization + parsing overhead         │
│         • Performance: ████████░░░░░░░░░░░░ ~40%                    │
└─────────────────────────────────────────────────────────────────────┘
```

### Research Principle

> For each CLI, determine the highest rung reachable given its source ecosystem, licensing, ABI realities, and interface characteristics.

---

## Research Phases

### Phase 0: Define Success Metrics and Taxonomy

**Deliverables:**

#### Metric Suite

| Category | Metrics |
|----------|---------|
| **Latency** | Cold-start latency, warm latency (steady state) |
| **Throughput** | Ops/sec under concurrency |
| **Efficiency** | CPU cycles per MB processed |
| **Memory** | Peak and steady-state |
| **Correctness** | Ordering, exit codes, stderr semantics |

#### CLI Taxonomy by Interaction Pattern

| Type | Examples | Key Characteristics |
|------|----------|---------------------|
| **Batch compute** | ffmpeg, imagemagick, rg | Input → Process → Output |
| **Streaming transform** | gzip, sed, jq | Continuous stdin → stdout |
| **Interactive/TUI** | git add -p, fzf | User interaction required |
| **Daemon fronts** | docker, kubectl | Talk to background service |
| **Stateful tools** | git, sqlite3 | Maintain state across calls |

#### Output Taxonomy

| Type | Examples | Parsing Strategy |
|------|----------|------------------|
| **Line-oriented text** | grep, ls | Line-by-line iteration |
| **Structured text** | jq --json, rg --json | JSON/YAML parser |
| **Binary output** | ffmpeg, tar | Binary protocol handler |
| **Mixed stdout/stderr** | Most CLIs | Stream multiplexing |

---

### Phase 1: Source-Side Analysis (CLI Performance Envelope)

For each CLI, research:

| Question | Why It Matters |
|----------|----------------|
| Is there an official library API? | Determines if Tier C is possible |
| Is there a stable ABI? | Determines if shared library approach works |
| Where does performance come from? | Identifies what must be preserved (mmap, SIMD, parallelism) |
| What are the hot paths? | Focus optimization efforts |
| Can it operate in persistent mode? | Determines if Tier B is feasible |

**Deliverable: Source Capability Profile Template**

```yaml
cli_name: ripgrep
implementation_language: Rust
build_system: Cargo
library_availability:
  official_api: false
  internal_crates: true (grep-searcher, grep-regex)
  stability: unstable internal APIs
abi_feasibility:
  c_abi_possible: true (via cdylib)
  effort: medium
  versioning: manual
concurrency_model: parallel file walking + parallel matching
io_model: mmap + streaming
output_modes:
  - text (default)
  - json (--json flag)
  - null-separated (--null flag)
licensing: MIT/Unlicense
portability: Linux, macOS, Windows
performance_sources:
  - SIMD regex matching
  - parallel directory walking
  - mmap for large files
  - compiled regex caching
```

---

### Phase 2: Target-Side Analysis (Language Performance Envelope)

For each target language, research:

| Aspect | Research Questions |
|--------|-------------------|
| **FFI mechanisms** | What's the best way to call native code? |
| **Subprocess handling** | How efficient is process spawning? |
| **Streaming primitives** | Async iterators? Generators? Streams? |
| **Cancellation** | How to abort long-running operations? |
| **Packaging** | How to distribute native extensions? |
| **Security** | Command injection prevention? |

**Deliverable: Target Runtime Profile Template**

```yaml
language: Python
best_ffi_option: PyO3 (Rust) or CFFI (C ABI)
best_subprocess_option: subprocess.run with PIPE
streaming_primitives:
  sync: generators, iterators
  async: async generators, asyncio.StreamReader
cancellation_mechanism:
  subprocess: process.kill() / process.terminate()
  ffi: cooperative via context manager
distribution:
  method: wheels (manylinux, musllinux, macOS, Windows)
  complexity: medium (cross-compilation required)
performance_pitfalls:
  - Per-object creation overhead
  - GIL contention for CPU-bound work
  - Memory copying at FFI boundary
```

---

### Phase 3: Define Bridging Strategies (Avoid N×M)

#### Standardized Bridge Tiers

| Tier | Name | Description | When to Use |
|------|------|-------------|-------------|
| **A** | Structured CLI Wrapper | Spawn CLI per call, use JSON/machine output | Always available, baseline |
| **B** | Persistent Worker Protocol | Background process, request/response over stdio/socket | High call volume, need caching |
| **C** | Shared Library Bridge | C ABI wrapper, generate bindings per language | Maximum performance required |
| **D** | Native Extension | Direct PyO3/N-API/JNI into core libraries | Specific high-value integrations |

#### Tier Selection Matrix

```
                        Library API Available?
                        Yes                 No
                    ┌───────────────┬───────────────┐
    High call       │   Tier C      │   Tier B      │
    volume          │   (native)    │   (daemon)    │
                    ├───────────────┼───────────────┤
    Low call        │   Tier C      │   Tier A      │
    volume          │   (native)    │   (subprocess)│
                    └───────────────┴───────────────┘
```

---

### Phase 4: CLI Interface Definition Language (CIDL)

**Purpose:** Common internal representation to avoid N×M combinations.

#### CIDL Schema (Draft)

```yaml
# Example: ripgrep CIDL
name: ripgrep
version: "14.0.0"
binary: rg

commands:
  search:
    description: "Search for pattern in files"
    args:
      - name: pattern
        type: string
        required: true
        position: 0
      - name: path
        type: path
        required: false
        position: 1
        default: "."

    options:
      - name: ignore-case
        short: i
        type: bool
        default: false
      - name: context
        short: C
        type: int
        default: 0
      - name: json
        type: bool
        default: false
        affects_output: true
      - name: type
        short: t
        type: string
        repeatable: true

    stdin:
      supported: true
      required: false
      type: text

    stdout:
      modes:
        text:
          format: line-oriented
          streaming: true
        json:
          format: jsonlines
          streaming: true
          schema: ripgrep-match-schema.json

    stderr:
      type: errors-and-warnings

    exit_codes:
      0: matches_found
      1: no_matches
      2: error

    performance_hints:
      parallelism: file-level
      caching: regex-compilation
      streaming_safe: true

    concurrency:
      thread_safe: true
      multiple_patterns: supported
```

#### CIDL Acquisition Methods

| Method | Pros | Cons |
|--------|------|------|
| **Parse --help** | Automatic | Incomplete, inconsistent |
| **Shell completions** | Structured | Not always available |
| **Manual specification** | Accurate | Labor-intensive |
| **Tracing/learning** | Discovers real behavior | Requires test corpus |
| **Man pages** | Detailed | Parsing is complex |

---

### Phase 5: Performance Patterns for Generated SDKs

| Pattern | Description | Applicable Tiers |
|---------|-------------|------------------|
| **Batching** | Multiple queries in one request | B, C |
| **Streaming decode** | Parse stdout incrementally | A, B |
| **Binary framing** | MessagePack/CBOR instead of JSON | B |
| **Zero-copy** | Avoid memory duplication | C |
| **Warm caches** | Keep compiled regex, walkers alive | B, C |
| **Work stealing** | Coordinate parallelism at boundary | B, C |
| **Cancellation** | OS kill or cooperative cancellation | All |
| **Backpressure** | Prevent pipe buffer deadlocks | A, B |

---

## Source Language Considerations

### Rust CLIs

| Aspect | Analysis |
|--------|----------|
| **Library potential** | Often have internal crates; may expose C ABI |
| **ABI stability** | Internal APIs unstable; cdylib requires manual ABI |
| **Best path** | Build core as cdylib + C ABI → Tier C |
| **Risk** | API churn, crate ecosystem not ABI-stable |

### C/C++ CLIs

| Aspect | Analysis |
|--------|----------|
| **Library potential** | Often have libraries or can extract |
| **ABI stability** | Feasible but versioning critical |
| **Best path** | Link to shared library or C ABI wrapper → Tier C |
| **Risk** | Header complexity, undefined behavior |

### Go CLIs

| Aspect | Analysis |
|--------|----------|
| **Library potential** | c-shared builds exist but awkward |
| **ABI stability** | Go runtime constraints complicate embedding |
| **Best path** | Tier B daemon (avoids Go runtime in host) |
| **Risk** | cgo overhead, runtime conflicts |

### Java CLIs

| Aspect | Analysis |
|--------|----------|
| **Library potential** | Easy if staying on JVM |
| **ABI stability** | N/A (JVM bytecode) |
| **Best path** | Tier B for non-JVM targets |
| **Risk** | JVM startup time |

### Python CLIs

| Aspect | Analysis |
|--------|----------|
| **Library potential** | Already Python; SDK is structural/typing |
| **ABI stability** | N/A |
| **Best path** | Direct import; Tier B only if caching helps |
| **Risk** | Python runtime perf ceiling |

### Decision Table

| Source Language | Tier A | Tier B | Tier C | Tier D | Best Default |
|-----------------|--------|--------|--------|--------|--------------|
| Rust | ✅ | ✅ | ✅ (cdylib) | ✅ (PyO3) | C or B |
| C/C++ | ✅ | ✅ | ✅ (native) | ✅ | C |
| Go | ✅ | ✅ | ⚠️ (cgo) | ⚠️ | B |
| Java | ✅ | ✅ | ❌ | ❌ | B |
| Python | ✅ | ⚠️ | ❌ | ❌ | A |

---

## Target Language Considerations

### Python

| Aspect | Recommendation |
|--------|----------------|
| **Tier A** | Easy; use `subprocess.run` with `--json` |
| **Tier B** | Removes spawn overhead; asyncio integration |
| **Tier C** | PyO3 or CFFI; excellent perf but wheel complexity |
| **Optimization** | Avoid per-match objects; use bulk arrays/memoryviews |
| **Async** | asyncio subprocess or async generators |

### TypeScript/Node

| Aspect | Recommendation |
|--------|----------------|
| **Tier A** | Easy; `child_process.spawn` |
| **Tier B** | Works well with streams |
| **Tier C** | N-API bindings; good perf, build complexity |
| **Optimization** | Use streams, avoid buffering entire output |
| **Async** | Promises + async iterators |

### Java

| Aspect | Recommendation |
|--------|----------------|
| **Tier A** | `ProcessBuilder` |
| **Tier B** | Strong for high throughput |
| **Tier C** | JNI is effort; Panama FFI may change this |
| **Optimization** | ByteBuffer for large outputs |
| **Async** | CompletableFuture + virtual threads (Java 21+) |

### Go

| Aspect | Recommendation |
|--------|----------------|
| **Tier A** | `os/exec` |
| **Tier B** | Straightforward |
| **Tier C** | cgo feasible but distribution complexity |
| **Optimization** | io.Reader streaming |
| **Async** | Goroutines + channels |

### .NET (C#)

| Aspect | Recommendation |
|--------|----------------|
| **Tier A** | `Process` class |
| **Tier B** | Good support |
| **Tier C** | P/Invoke feasible |
| **Optimization** | Span<T> for zero-copy |
| **Async** | async/await + IAsyncEnumerable |

---

## Standardization Strategy

### Avoiding N×M Combinations

```
┌─────────────────────────────────────────────────────────────────┐
│                         THE ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌─────────┐     ┌─────────┐     ┌─────────┐                  │
│   │ ripgrep │     │   jq    │     │  ffmpeg │   ... N CLIs     │
│   └────┬────┘     └────┬────┘     └────┬────┘                  │
│        │               │               │                        │
│        ▼               ▼               ▼                        │
│   ┌─────────────────────────────────────────┐                  │
│   │              CIDL Specs                  │  ← Per-CLI       │
│   │  (CLI Interface Definition Language)    │    (N specs)     │
│   └─────────────────────┬───────────────────┘                  │
│                         │                                       │
│                         ▼                                       │
│   ┌─────────────────────────────────────────┐                  │
│   │           Tier Adapters                  │  ← Small set     │
│   │  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐    │    (3-4 total)   │
│   │  │  A  │  │  B  │  │  C  │  │  D  │    │                  │
│   │  └─────┘  └─────┘  └─────┘  └─────┘    │                  │
│   └─────────────────────┬───────────────────┘                  │
│                         │                                       │
│                         ▼                                       │
│   ┌─────────────────────────────────────────┐                  │
│   │         SDK Generators                   │  ← Per-language  │
│   │  ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐   │    (M generators)│
│   │  │ Py │ │ TS │ │Java│ │ Go │ │ C# │   │                  │
│   │  └────┘ └────┘ └────┘ └────┘ └────┘   │                  │
│   └─────────────────────────────────────────┘                  │
│                                                                 │
│   Total implementations: N + 4 + M (not N × M)                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Key Insight

You do NOT generate "Rust→Python" or "Go→Java" individually.

You generate:
1. **CLI → CIDL** (per CLI, N specs)
2. **CIDL → SDK** (per target language, M generators)
3. **Tier adapters** (small finite set, ~4)

**Complexity: O(N + M) instead of O(N × M)**

---

## Anchor Case: ripgrep → Python

### Purpose

Validate the tier model using ripgrep as reference CLI.

### Implementation Plan

| Tier | Implementation | Expected Performance |
|------|----------------|---------------------|
| **A** | `subprocess.run(['rg', '--json', ...])` with streaming parser | Baseline |
| **B** | Long-lived `rg` worker with binary framed protocol | 2-5x baseline |
| **C** | C ABI wrapper around ripgrep crates, PyO3/CFFI bindings | 5-10x baseline |

### Measurement Plan

| Metric | Method |
|--------|--------|
| Cold start | Time first search after process start |
| Warm latency | Time subsequent searches (steady state) |
| Throughput | Searches/second under concurrent load |
| Overhead breakdown | Profile: spawn, parse, object creation, I/O |

### Workloads

| Workload | Description |
|----------|-------------|
| Small file, simple pattern | Single file, literal string |
| Large codebase, simple pattern | Linux kernel, literal string |
| Large codebase, complex regex | Linux kernel, regex with alternation |
| Many small searches | 1000 searches, small scope each |

---

## Key Unknowns to Resolve

| Unknown | Research Method |
|---------|-----------------|
| When does JSON parsing dominate vs spawn cost? | Benchmark with varying output sizes |
| How often can Tier B apply without modifying upstream? | Survey CLIs for daemon/server modes |
| Feasibility of Tier C for Rust CLIs without stable APIs? | Prototype with ripgrep crates |
| Packaging/distribution costs per language for Tier C? | Build and publish test wheels/packages |
| Correctness and security guarantees (escaping, injection)? | Security audit, fuzzing |
| Stable SDK contract if CLI help text changes? | Versioning strategy, CIDL pinning |

---

## Deliverables

### Phase 0
- [ ] Metric suite definition
- [ ] CLI taxonomy document
- [ ] Output format taxonomy

### Phase 1
- [ ] Source Capability Profile template
- [ ] 5 example profiles (ripgrep, jq, ffmpeg, git, docker)

### Phase 2
- [ ] Target Runtime Profile template
- [ ] Profiles for Python, TypeScript, Java, Go, C#

### Phase 3
- [ ] Tier adapter specifications (A, B, C, D)
- [ ] Tier selection algorithm

### Phase 4
- [ ] CIDL specification v0.1
- [ ] CIDL parser/validator
- [ ] Example CIDL for ripgrep

### Phase 5
- [ ] Performance patterns catalog
- [ ] SDK template for each target language

### Anchor Case
- [ ] ripgrep Tier A implementation (Python)
- [ ] ripgrep Tier B implementation (Python)
- [ ] ripgrep Tier C implementation (Python)
- [ ] Benchmark results and analysis

---

## Next Steps

When ready to execute research:

1. **Start with Phase 0** - Define metrics and taxonomy
2. **Build ripgrep profiles** - Source (Phase 1) and Target/Python (Phase 2)
3. **Prototype all three tiers** for ripgrep→Python
4. **Benchmark and analyze** - Validate the tier model
5. **Generalize** - Create templates and CIDL spec

---

## References

- [Stainless](https://www.stainlessapi.com/) - REST API to SDK (inspiration)
- [PyO3](https://pyo3.rs/) - Rust bindings for Python
- [ripgrep crates](https://github.com/BurntSushi/ripgrep/tree/master/crates) - Library architecture
- [orjson](https://github.com/ijl/orjson) - High-performance Rust-Python example
- [pydantic-core](https://github.com/pydantic/pydantic-core) - Rust validation in Python

# Research Plan: Maximum Performance ripgrep in Python

## Facts (What We Know)

1. **ripgrep is Rust** - compiled, native code with SIMD, parallelism, memory-mapped I/O
2. **ripgrepy uses subprocess** - spawns `rg` process, captures stdout, parses in Python
3. **Python has inherent overhead** - interpreted, GIL, dynamic typing
4. **Rust can expose C-compatible APIs** - via `#[no_mangle]` and `extern "C"`
5. **PyO3 exists** - mature framework for Rust ↔ Python bindings
6. **ripgrep is modular** - built from multiple crates (grep-regex, grep-searcher, grep-matcher, etc.)

---

## Constraints

| Constraint | Implication |
|------------|-------------|
| Must use Python | Cannot use pure Rust CLI directly |
| Want maximum performance | Must minimize Python ↔ native boundary crossings |
| ripgrep is a CLI tool, not a library | May need to use underlying crates instead |
| GIL exists | Parallelism must happen in Rust, not Python |
| Data must cross language boundary | Serialization/deserialization has cost |

---

## Performance Hierarchy (First Principles)

From fastest to slowest:

```
1. Pure Rust (ripgrep CLI)           → Baseline (fastest possible)
2. Python → PyO3 → Rust library      → Near-native, minimal FFI overhead
3. Python → ctypes/cffi → .so/.dll   → FFI overhead, manual memory management
4. Python → subprocess → rg binary   → Process spawn + IPC overhead (ripgrepy)
```

**Upper bound** = Approach #2 (PyO3 bindings to ripgrep's internal crates)

---

## Research Questions to Investigate

### 1. ripgrep's Architecture
- What crates make up ripgrep?
- Which crate contains the core search logic?
- Is there already a library API, or is it CLI-only?
- What are the public APIs of `grep-searcher`, `grep-regex`, `grep-matcher`?

### 2. Existing Python Bindings
- Do PyO3 bindings for ripgrep or its crates already exist?
- Are there any abandoned/partial attempts we can learn from?
- What does the Python packaging ecosystem have? (check PyPI)

### 3. PyO3 Feasibility
- Can ripgrep's crates be wrapped with PyO3?
- What types need to cross the boundary? (strings, callbacks, iterators?)
- How would results be returned efficiently? (streaming vs batch)

### 4. Alternative Approaches
- Could we use `grep-regex` crate directly (the regex engine)?
- Is there a pure-Rust regex library with existing Python bindings?
- What about `ruff` or other Rust-Python tools - how do they achieve speed?

### 5. Benchmarking Strategy
- How to measure: subprocess vs hypothetical native bindings?
- What are the overhead components? (spawn time, IPC, parsing)
- At what scale does each approach matter? (single search vs millions)

---

## Research Execution Plan

| Step | Action | Purpose |
|------|--------|---------|
| 1 | Examine ripgrep's `Cargo.toml` and crate structure | Understand modular architecture |
| 2 | Read `grep-searcher` and `grep-regex` public APIs | Identify what can be exposed |
| 3 | Search GitHub for "ripgrep pyo3" or "ripgrep python bindings" | Find existing work |
| 4 | Search PyPI for ripgrep-related packages | Find existing packages |
| 5 | Examine how similar projects (ruff, pydantic-core, orjson) do Rust→Python | Learn patterns |
| 6 | Prototype or find benchmarks comparing subprocess vs native | Quantify the gap |

---

## Hypotheses to Validate

1. **ripgrep's crates are library-usable** - They expose public APIs suitable for embedding
2. **No production-ready Python bindings exist** - Otherwise we'd just use them
3. **PyO3 bindings are feasible** - The API surface is wrappable
4. **Performance gain is significant** - Worth the effort vs subprocess approach
5. **Streaming results is important** - Batch return would negate some benefits

---

## Research Outcomes

### Hypothesis Results

| Hypothesis | Result |
|------------|--------|
| ripgrep's crates are library-usable | ✅ **CONFIRMED** - `grep-searcher` has documented library API |
| No production-ready Python bindings exist | ❌ **REFUTED** - `ripgrep-python` exists (v0.1.0) |
| PyO3 bindings are feasible | ✅ **CONFIRMED** - `ripgrep-python` proves it |
| Performance gain is significant | ❌ **REFUTED** - Current bindings are SLOWER than subprocess |
| Streaming results is important | ⚠️ **UNCLEAR** - Not tested |

### Unexpected Finding

**Subprocess is currently faster than native bindings!**

```
ripgrep-python (PyO3): 119.2 ms average
subprocess (rg binary): 55.6 ms average
```

This is because:
1. The `rg` binary has years of optimization (LTO, PGO, SIMD)
2. `ripgrep-python` is v0.1.0 and not yet optimized
3. FFI overhead in current implementation exceeds subprocess overhead

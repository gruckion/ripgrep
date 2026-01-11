# GitHub Issue: Research: Python Integration Performance Analysis

> **To create this issue on GitHub, copy the content below the line into a new issue.**

---

## Summary

This issue documents research into using ripgrep from Python with maximum performance. The findings are counterintuitive but backed by benchmarks.

## Key Finding

**Calling the `rg` binary via subprocess currently outperforms existing native Python bindings.**

| Approach | Average Time | Relative Performance |
|----------|--------------|---------------------|
| `rg` via subprocess | **27-56 ms** | Baseline (fastest) |
| ripgrep-python (PyO3 native) | 64-119 ms | ~2x slower |
| rure (Rust regex bindings) | 556 ms | Slower than Python's `re` |

## Benchmark Details

### Environment
- ripgrep repository codebase
- 1000 generated test files
- 100 iterations per test

### Results

```
=== Subprocess Overhead ===
Calling 'true':          4.4 ms average
Calling 'rg --version':  9.9 ms average

=== Search Performance (1000 files, 100 iterations) ===
ripgrep-python (PyO3):   119.2 ms average
subprocess (rg binary):   55.6 ms average
Winner: Subprocess is 2.1x FASTER

=== Regex Performance (4.5MB text, 300K matches) ===
rure (Rust regex):  556 ms
Python re:          240 ms
Winner: Python re is 2.3x FASTER
```

## Why Native Bindings Are Currently Slower

1. **ripgrep-python is v0.1.0** - Early stage, not yet optimized
2. **The `rg` binary has aggressive optimizations** - LTO, PGO, `codegen-units=1`, SIMD runtime dispatch
3. **FFI overhead accumulates** - Each Python↔Rust boundary crossing has cost
4. **rure is abandoned** - Last updated in 2019

## ripgrep's Library Architecture

ripgrep is already modular and designed for library use:

| Crate | Purpose |
|-------|---------|
| `grep` | Facade crate - "ripgrep as a library" |
| `grep-searcher` | Line-oriented search with mmap, parallel I/O |
| `grep-regex` | Regex matching using Rust's `regex` crate |
| `grep-matcher` | Trait abstraction for matchers |
| `grep-printer` | Output formatting |

The `grep-searcher` crate explicitly documents library usage:

```rust
use grep_searcher::Searcher;
use grep_regex::RegexMatcher;

let matcher = RegexMatcher::new(r"pattern")?;
Searcher::new().search_path(&matcher, "file.txt", sink)?;
```

## Existing Python Options

| Package | Type | Status |
|---------|------|--------|
| [ripgrepy](https://github.com/securisec/ripgrepy) | Subprocess wrapper | Active, convenient API |
| [ripgrep-python](https://pypi.org/project/ripgrep-python/) | PyO3 native bindings | v0.1.0, needs optimization |
| [rure](https://pypi.org/project/rure/) | Rust regex bindings | Abandoned (2019) |

## Recommendations

### For Maximum Performance Today

```python
import subprocess
import json

def ripgrep_search(pattern: str, path: str) -> list[dict]:
    result = subprocess.run(
        ['rg', '--json', pattern, path],
        capture_output=True, text=True
    )
    return [
        json.loads(line)
        for line in result.stdout.splitlines()
        if json.loads(line).get('type') == 'match'
    ]
```

### For a Future Optimal Native Binding

A properly optimized PyO3 binding would need to:

1. **Use `grep-searcher` and `grep-regex` directly** - Not wrap the CLI
2. **Cache compiled regex** - Reuse between searches
3. **Return Python objects directly** - Avoid JSON serialization
4. **Build with LTO + PGO** - Match the binary's optimizations
5. **Minimize boundary crossings** - Do bulk work in Rust, return results once

### Lessons from High-Performance Rust-Python Projects

| Project | Key Pattern |
|---------|-------------|
| **orjson** | Single bulk operation per call, minimal FFI crossings |
| **pydantic-core** | Compiled validator tree, one validation call |
| **ruff** | Process entire file in one call, return structured data |

## Decision Matrix

| Use Case | Recommendation |
|----------|----------------|
| Maximum raw speed | Subprocess → `rg` binary |
| Pythonic API convenience | ripgrepy |
| Avoid external binary dependency | ripgrep-python |
| Bulk searches (1000s) | Subprocess with process pooling |
| Just need fast regex | Python's built-in `re` (seriously) |

## Related

- Issue #165 - Original Python API request (2016)
- [ripgrep-python on PyPI](https://pypi.org/project/ripgrep-python/)
- [ripgrepy on GitHub](https://github.com/securisec/ripgrepy)

## Conclusion

The subprocess approach wins today because:

1. The `rg` binary is **exceptionally optimized** (years of tuning)
2. Subprocess overhead (~5-10ms) is **smaller than current binding overhead**
3. The overhead is **amortized** when searching large codebases

A truly optimal native binding is theoretically possible and would eliminate subprocess overhead, but would require significant engineering effort to match the binary's performance.

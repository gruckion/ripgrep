# Phase 1: Source Capability Profile - ripgrep

## 1. Basic Information

| Field | Value |
|-------|-------|
| **CLI Name** | ripgrep |
| **Binary Name** | `rg` |
| **Version** | 15.1.0 |
| **Implementation Language** | Rust |
| **Build System** | Cargo |
| **License** | Unlicense OR MIT |
| **Repository** | https://github.com/BurntSushi/ripgrep |

---

## 2. Architecture Overview

### 2.1 Crate Structure

ripgrep is modular, with functionality split across workspace crates:

```
ripgrep/
├── Cargo.toml              # Main binary crate
├── crates/
│   ├── core/               # CLI entry point and argument handling
│   ├── grep/               # "ripgrep as a library" facade
│   ├── cli/                # CLI utilities (colors, human output)
│   ├── matcher/            # Matcher trait abstraction
│   ├── regex/              # Regex implementation
│   ├── searcher/           # Core search engine
│   ├── printer/            # Output formatting
│   ├── ignore/             # .gitignore aware file walking
│   ├── globset/            # Glob pattern matching
│   └── pcre2/              # Optional PCRE2 support
```

### 2.2 Crate Dependency Graph

```
                    ┌─────────────────┐
                    │     ripgrep     │
                    │   (binary)      │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
        ┌─────────┐    ┌─────────┐    ┌─────────┐
        │  grep   │    │ ignore  │    │   cli   │
        │(facade) │    │(walker) │    │(colors) │
        └────┬────┘    └─────────┘    └─────────┘
             │
    ┌────────┼────────┬────────┬────────┐
    │        │        │        │        │
    ▼        ▼        ▼        ▼        ▼
┌───────┐┌───────┐┌───────┐┌───────┐┌───────┐
│matcher││ regex ││searcher││printer││ pcre2 │
└───────┘└───────┘└───────┘└───────┘└───────┘
```

---

## 3. Library API Availability

### 3.1 Official Library Status

| Aspect | Status |
|--------|--------|
| **Official Library Crate** | `grep` crate (published on crates.io) |
| **Documentation** | https://docs.rs/grep |
| **API Stability** | Semver, but "no high level documentation yet" |
| **Intended for External Use** | Yes, explicitly stated as "ripgrep as a library" |

### 3.2 Library Entry Point

From `crates/grep/src/lib.rs`:

```rust
/*!
ripgrep, as a library.

This library is intended to provide a high level facade to the crates that
make up ripgrep's core searching routines.
*/

pub extern crate grep_cli as cli;
pub extern crate grep_matcher as matcher;
pub extern crate grep_printer as printer;
pub extern crate grep_regex as regex;
pub extern crate grep_searcher as searcher;
```

### 3.3 Key Public APIs

#### Matcher Trait (`grep-matcher`)
```rust
pub trait Matcher {
    type Captures: Captures;
    type Error: std::fmt::Display;

    fn find_at(&self, haystack: &[u8], at: usize) -> Result<Option<Match>, Self::Error>;
    fn new_captures(&self) -> Result<Self::Captures, Self::Error>;
    // ... many more methods
}
```

#### Searcher (`grep-searcher`)
```rust
pub struct Searcher { /* ... */ }
pub struct SearcherBuilder { /* ... */ }

impl Searcher {
    pub fn search_path<M, S>(&mut self, matcher: M, path: &Path, sink: S) -> Result<(), S::Error>;
    pub fn search_file<M, S>(&mut self, matcher: M, file: &File, sink: S) -> Result<(), S::Error>;
    pub fn search_slice<M, S>(&mut self, matcher: M, slice: &[u8], sink: S) -> Result<(), S::Error>;
    pub fn search_reader<M, R, S>(&mut self, matcher: M, rdr: R, sink: S) -> Result<(), S::Error>;
}
```

#### Sink Trait (`grep-searcher`)
```rust
pub trait Sink {
    type Error;
    fn matched(&mut self, searcher: &Searcher, mat: &SinkMatch<'_>) -> Result<bool, Self::Error>;
    // ... context methods, finish, etc.
}
```

---

## 4. ABI Feasibility Analysis

### 4.1 Current ABI Status

| Aspect | Status |
|--------|--------|
| **Existing C ABI** | No |
| **cdylib Build** | Not currently supported |
| **Stable ABI** | No (Rust internal) |

### 4.2 ABI Exposure Feasibility

#### What Would Be Required

1. **Create C ABI Wrapper Crate**
   ```rust
   // Hypothetical ripgrep-ffi crate
   #[no_mangle]
   pub extern "C" fn rg_search(
       pattern: *const c_char,
       path: *const c_char,
       callback: extern "C" fn(*const RgMatch) -> bool
   ) -> i32;
   ```

2. **Build as cdylib**
   ```toml
   [lib]
   crate-type = ["cdylib"]
   ```

3. **Define Stable Data Structures**
   ```rust
   #[repr(C)]
   pub struct RgMatch {
       pub path: *const c_char,
       pub line_number: u64,
       pub line_start: *const u8,
       pub line_len: usize,
       pub match_start: usize,
       pub match_end: usize,
   }
   ```

#### Effort Estimate

| Task | Effort |
|------|--------|
| Design C ABI surface | Medium |
| Implement wrapper functions | Medium |
| Memory management (who owns what) | High |
| Error handling across FFI | Medium |
| Build system integration | Low |
| **Total** | **Medium-High** |

#### Risks

1. **API Churn**: Internal APIs may change between versions
2. **Complexity**: The Sink/callback model doesn't map cleanly to C
3. **Performance**: May need to copy data across FFI boundary
4. **Maintenance**: Must track upstream changes

---

## 5. Performance Sources

### 5.1 Key Performance Features

| Feature | Implementation | Location |
|---------|----------------|----------|
| **SIMD Regex** | Runtime SIMD dispatch via `regex` crate | `grep-regex` |
| **Parallel File Walking** | `ignore` crate with `crossbeam` | `crates/ignore/src/walk.rs` |
| **Memory Mapping** | Optional mmap for large files | `crates/searcher/src/searcher/mmap.rs` |
| **Literal Optimization** | Aho-Corasick, memchr for literals | `grep-regex/src/literal.rs` |
| **Line-Oriented Search** | Specialized line finding | `grep-searcher/src/lines.rs` |
| **Binary Detection** | Skip binary files early | `grep-searcher` |

### 5.2 Build Optimizations

From `Cargo.toml` profile `release-lto`:

```toml
[profile.release-lto]
opt-level = 3
debug = "none"
strip = "symbols"
debug-assertions = false
overflow-checks = false
lto = "fat"           # Link-time optimization
panic = "abort"
incremental = false
codegen-units = 1     # Single codegen unit for max optimization
```

### 5.3 Performance-Critical Paths

1. **Regex Compilation**: Done once, reused for all files
2. **Directory Walking**: Parallel traversal with ignore rules
3. **File Reading**: mmap or buffered I/O based on file size
4. **Line Finding**: Optimized memchr-based line iteration
5. **Match Finding**: SIMD-accelerated regex matching

---

## 6. Daemon/Persistent Mode Potential

### 6.1 Current Support

| Feature | Status |
|---------|--------|
| **Built-in Daemon Mode** | No |
| **Server/Client Architecture** | No |
| **Long-Running Mode** | No |
| **Watch Mode** | No |

### 6.2 Feasibility of Adding Daemon Mode

#### What Could Be Preserved in Daemon Mode

| State | Cacheable? | Benefit |
|-------|------------|---------|
| Compiled regex | Yes | Avoid recompilation |
| Ignore patterns | Yes | Avoid re-parsing .gitignore |
| File type definitions | Yes | Avoid re-parsing |
| Directory structure cache | Partially | Faster walking (but stale risk) |

#### Implementation Approach

1. **Wrapper Daemon** (Recommended for SDK)
   - External process that keeps `grep` library loaded
   - Accepts requests via stdin/socket
   - Returns results via stdout/socket
   - SDK manages lifecycle

2. **Upstream Enhancement** (Requires contribution)
   - Add `--server` mode to ripgrep
   - Define protocol
   - Unlikely to be accepted (adds complexity)

---

## 7. CLI Interface Analysis

### 7.1 Command Structure

```
rg [OPTIONS] PATTERN [PATH ...]
rg [OPTIONS] -e PATTERN ... [PATH ...]
rg [OPTIONS] -f PATTERNFILE ... [PATH ...]
rg [OPTIONS] --files [PATH ...]
rg [OPTIONS] --type-list
```

### 7.2 Output Modes

| Mode | Flag | Format | Parsing |
|------|------|--------|---------|
| Standard | (default) | Human-readable text | Regex-based (fragile) |
| JSON Lines | `--json` | One JSON object per line | `json.loads()` per line |
| Files only | `-l` | One path per line | Line split |
| Count | `-c` | `path:count` | Split on `:` |
| Null-separated | `--null` | NUL-delimited paths | Split on `\0` |

### 7.3 Exit Codes

| Code | Meaning |
|------|---------|
| 0 | At least one match found |
| 1 | No matches found |
| 2 | Error occurred |

### 7.4 Streaming Behavior

- Output is streamed as matches are found
- Order depends on parallelism (`--sort` for determinism)
- JSON mode supports streaming parsing (JSON Lines)

---

## 8. SDK Integration Recommendations

### 8.1 Tier Feasibility

| Tier | Feasibility | Recommendation |
|------|-------------|----------------|
| **A: Subprocess** | ✅ Excellent | Use `--json` for structured output |
| **B: Daemon** | ✅ Good | Implement wrapper daemon using `grep` crate |
| **C: C ABI** | ⚠️ Medium | Possible but significant effort |
| **D: Native (PyO3)** | ⚠️ Medium | Could wrap `grep` crate directly |

### 8.2 Recommended Approach

**Primary: Tier A (Subprocess)**
- Use `rg --json` for all operations
- Stream-parse JSON Lines for incremental results
- Handle exit codes correctly (1 = no matches, not error)

**Secondary: Tier B (Daemon)**
- Build custom daemon using `grep` crate
- Keep regex compiled, walker cached
- Binary protocol for performance

**Stretch: Tier C/D (FFI)**
- Build `ripgrep-ffi` crate with C ABI
- Generate Python bindings with PyO3 or CFFI
- Requires ongoing maintenance

---

## 9. Source Capability Profile Summary

```yaml
cli: ripgrep
version: "15.1.0"
language: rust
build_system: cargo

library_availability:
  has_library: true
  crate_name: grep
  docs_url: https://docs.rs/grep
  stability: semver
  documented: partially

abi_feasibility:
  existing_c_abi: false
  cdylib_possible: true
  effort: medium-high
  risks:
    - api_churn
    - callback_model_complexity
    - memory_management

performance_sources:
  simd: true (runtime dispatch)
  parallelism: true (file walking)
  mmap: true (optional)
  literal_optimization: true
  build_optimizations:
    - lto: fat
    - codegen_units: 1
    - panic: abort

daemon_mode:
  built_in: false
  feasibility: high
  cacheable_state:
    - compiled_regex
    - ignore_patterns
    - type_definitions

cli_interface:
  structured_output: true (--json)
  streaming: true
  exit_codes:
    success: 0
    no_match: 1
    error: 2

tier_recommendations:
  tier_a: recommended
  tier_b: recommended
  tier_c: possible
  tier_d: possible
```

---

*Phase 1 Complete. Proceed to Phase 2: Target Runtime Profile for Python.*

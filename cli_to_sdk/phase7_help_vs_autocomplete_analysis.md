# Phase 7: --help vs Autocomplete Information Analysis

## Executive Summary

This analysis compares what information is available from `--help` output versus shell autocomplete scripts versus direct codebase access, to determine whether `--help` + autocomplete is sufficient for building production-quality SDKs.

**Verdict**: --help + autocomplete provides ~70% of what's needed. The remaining 30% (including critical blockers like exit codes and output schema) requires codebase analysis.

---

## Matrix 1: Information Available by Source

| Information Category | `-h` | `--help` | Autocomplete (zsh) | Autocomplete (bash) | Codebase |
|---------------------|------|----------|--------------------|--------------------|----------|
| **Option Names** |
| Long name (`--foo`) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Short name (`-f`) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Negation (`--no-foo`) | ❌ | ✅ text | ✅ | ✅ | ✅ |
| Aliases | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Descriptions** |
| Short description | ✅ | ✅ | ✅ | ❌ | ✅ |
| Long description | ❌ | ✅ | ❌ | ❌ | ✅ |
| Examples | ❌ | ✅ | ❌ | ❌ | ✅ |
| **Value Types** |
| Is switch (boolean) | Implicit | Implicit | ✅ | Implicit | ✅ |
| Enum choices | Partial | ✅ | ✅ | ✅ | ✅ |
| Completion type (file/exec/etc) | ❌ | ❌ | ✅ | Partial | ✅ |
| Numeric type | ❌ | ✅ text | ❌ | ❌ | ✅ |
| **Constraints** |
| Mutual exclusivity | ❌ | ✅ text | ✅ groups | ❌ | ✅ |
| Override behavior | ❌ | ✅ text | ❌ | ❌ | ✅ |
| Default values | ❌ | Partial | ❌ | ❌ | ✅ |
| **Metadata** |
| Exit codes | ❌ | ❌ | ❌ | ❌ | ✅ |
| Environment vars | ❌ | ❌ | ❌ | ❌ | ✅ |
| Output schema (JSON) | ❌ | ❌ | ❌ | ❌ | ✅ |

---

## Matrix 2: ripgrep CompletionType System

ripgrep defines these completion types in `crates/core/flags/mod.rs`:

```rust
enum CompletionType {
    Other,      // Default - uses doc_choices() or is_switch()
    Filename,   // File path completion
    Executable, // Command/binary completion
    Filetype,   // Dynamic from --type-list
    Encoding,   // Hardcoded encoding list
}
```

| CompletionType | zsh | bash | fish |
|----------------|-----|------|------|
| `Other` | ✅ | ✅ | ✅ |
| `Filename` | ✅ file compl | ❌ generic | ✅ `-r -F` |
| `Executable` | ✅ cmd compl | ❌ generic | ✅ `__fish_complete_command` |
| `Filetype` | ✅ dynamic | ❌ generic | ✅ dynamic |
| `Encoding` | ✅ hardcoded | ✅ hardcoded | ✅ hardcoded |

---

## Matrix 3: Exit Codes (Codebase Only)

| Exit Code | Meaning | In --help | In man | In autocomplete |
|-----------|---------|-----------|--------|-----------------|
| `0` | Match found / success | ❌ | ❌ | ❌ |
| `1` | No match found | ❌ | ❌ | ❌ |
| `2` | Error occurred | ❌ | ❌ | ❌ |

**Source**: `crates/core/main.rs:95-100`

---

## Matrix 4: Environment Variables (Codebase Only)

| Variable | Purpose | Documented In |
|----------|---------|---------------|
| `RIPGREP_CONFIG_PATH` | Config file | man page only |
| `NO_COLOR` | Disable colors | man page only |
| `TERM` | Terminal type | nowhere |
| `PWD` | CWD fallback | nowhere |

---

## Critical Gaps Analysis

### Gap 1: Exit Codes 🔴 BLOCKER

**Problem**: No source exposes exit code semantics.

**Impact on SDK**:
```python
# Without exit codes, SDK cannot:
class RipgrepError(Exception): pass
class NoMatchError(RipgrepError): pass  # Exit code 1
class SearchError(RipgrepError): pass   # Exit code 2

# User cannot distinguish:
try:
    results = rg.search("pattern")
except NoMatchError:
    print("Pattern not found")  # vs actual error
```

**Solution Required**: Extract from codebase or test empirically.

---

### Gap 2: Output Schema 🔴 BLOCKER

**Problem**: JSON output structure only defined in `crates/printer/src/jsont.rs`.

**JSON Message Types**:
```rust
pub(crate) enum Message<'a> {
    Begin(Begin<'a>),   // {"type":"begin","data":{"path":...}}
    End(End<'a>),       // {"type":"end","data":{"path":...,"stats":...}}
    Match(Match<'a>),   // {"type":"match","data":{"path":...,"lines":...}}
    Context(Context<'a>), // {"type":"context","data":{...}}
}
```

**Impact on SDK**:
- Cannot generate typed dataclasses for responses
- Cannot validate parsing correctness
- Users don't know response structure

**Solution Required**: Extract from codebase or infer from samples.

---

### Gap 3: Default Values 🟡 HIGH

**Problem**: Defaults scattered throughout codebase.

| Option | Actual Default | In --help |
|--------|----------------|-----------|
| `--threads` | `num_cpus` | "approximate" |
| `--context` | `0` | ❌ |
| `--max-depth` | unlimited | ❌ |
| `--color` | `auto` | ✅ |
| `--context-separator` | `"--"` | ❌ |

**Solution Required**: Parse codebase `Default` implementations.

---

### Gap 4: Type Precision 🟡 MEDIUM

**Problem**: --help uses "NUM" without bounds/units.

| Option | --help | Actual Type |
|--------|--------|-------------|
| `--threads` | NUM | `usize`, 1..=num_cpus*2 |
| `--max-filesize` | NUM+SUFFIX | `u64` + K/M/G/T suffix |
| `--after-context` | NUM | `usize`, ≥0 |

---

### Gap 5: Override Semantics 🟡 MEDIUM

**Problem**: Relationships in prose only.

```
# From --help:
"This flag overrides the -i/--ignore-case and -S/--smart-case flags."
```

Would need NLP to extract:
- `--case-sensitive` overrides `--ignore-case`
- `--case-sensitive` overrides `--smart-case`

---

## Feasibility Assessment

### What --help + Autocomplete CAN Provide (70%)

| Capability | Feasible | Quality |
|------------|----------|---------|
| Complete option inventory | ✅ | High |
| Short descriptions | ✅ | High |
| Enum value lists | ✅ | High |
| Switch vs value-taking | ✅ | High |
| File/executable type hints | ✅ | Medium (zsh/fish only) |
| Mutual exclusivity groups | ✅ | Medium (zsh only) |
| Category organization | ✅ | High |

### What REQUIRES Codebase Access (30%, includes blockers)

| Capability | Impact | Workaround |
|------------|--------|------------|
| Exit codes | 🔴 Critical | Test empirically |
| Output schema | 🔴 Critical | Sample and infer |
| Default values | 🟡 High | Accept imprecision |
| Type bounds | 🟡 Medium | Use generic types |
| Override rules | 🟡 Medium | NLP on --help text |
| Environment vars | 🟡 Medium | Document separately |

---

## Conclusion

**Can --help + autocomplete alone enable CLI→SDK?**

| SDK Tier | Feasible | What's Missing |
|----------|----------|----------------|
| **Basic wrapper** | ✅ Yes | Works but no error semantics |
| **Typed responses** | ⚠️ Partial | No output schema |
| **Input validation** | ⚠️ Partial | No type bounds |
| **Production quality** | ❌ No | Exit codes, defaults, schema |

**The hybrid approach is REQUIRED**, not optional:

1. **--help** → Option names, descriptions, enum values
2. **Autocomplete** → Type hints (file/exec), mutual exclusivity
3. **Claude Agent SDK** → Exit codes, output schema, defaults, bounds

The last 30% is what separates a demo from a production tool.

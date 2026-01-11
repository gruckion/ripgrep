# PRD-001: CLI→SDK System

## Product Requirements Document

**Version**: 1.0
**Date**: 2025-01-11
**Author**: Research Phase
**Status**: Research Complete, Ready for Implementation

---

## 1. Executive Summary

### 1.1 Vision

Build a system that automatically generates high-performance, idiomatic SDKs from command-line interfaces—the "Stainless for CLIs." Just as Stainless transforms OpenAPI specs into production-quality API clients, CLI→SDK transforms CLI tools into native language libraries.

### 1.2 Problem Statement

**The N×M Problem**: There are thousands of CLI tools and dozens of programming languages. Currently, if you want to use a CLI from code, you either:

1. **Subprocess directly** - Manual argument construction, string parsing, no type safety
2. **Find a wrapper library** - Rare, often outdated, inconsistent quality
3. **Use native bindings** - Requires deep expertise, high maintenance burden

**Example**: ripgrep is one of the most popular CLI tools. To use it from Python:
- **ripgrepy** exists but is just a thin subprocess wrapper with no types
- **ripgrep-python** (PyO3) exists but is actually slower than subprocess
- No official SDK from the ripgrep team

### 1.3 Solution

Create an intermediate representation (CIDL - CLI Interface Definition Language) that captures everything needed to generate SDKs, then build generators for each target language.

```
CLI Tool → CIDL Extraction → CIDL Spec → SDK Generator → Native SDK
   N            1                1            M            N×M

Complexity: O(N+M) instead of O(N×M)
```

### 1.4 Key Insight from Research

**Counterintuitive finding**: Subprocess-based SDKs can outperform "native" bindings.

| Approach | ripgrep Python Benchmark |
|----------|-------------------------|
| Subprocess (Tier A) | ~27-55ms |
| PyO3 native (ripgrep-python) | ~64-119ms |

This validates the subprocess-first approach while leaving room for optimization.

---

## 2. Research Findings

### 2.1 Anchor Case Study: ripgrep

#### 2.1.1 ripgrep vs ripgrepy Comparison

| Aspect | ripgrep | ripgrepy |
|--------|---------|----------|
| **Language** | Rust | Python |
| **Type** | Actual search engine | Subprocess wrapper |
| **Performance** | Native speed, SIMD | Subprocess overhead |
| **Code** | 50k+ lines Rust | ~500 lines Python |
| **Relationship** | Original tool | Calls `rg` binary |

**Realization**: ripgrepy is exactly what CLI→SDK would generate—but manually written and without types.

#### 2.1.2 ripgrep Architecture

```
ripgrep/
├── crates/
│   ├── core/           # CLI, argument parsing, orchestration
│   │   └── flags/      # 100+ flag definitions with rich metadata
│   ├── grep/           # Core grep library
│   ├── grep-searcher/  # File searching logic
│   ├── grep-regex/     # Regex engine integration
│   ├── grep-matcher/   # Matcher trait abstractions
│   ├── printer/        # Output formatting (including JSON)
│   └── ignore/         # .gitignore handling
```

**Key Finding**: ripgrep already has structured flag definitions (`Flag` trait) with:
- `name_long()`, `name_short()`, `name_negated()`
- `doc_short()`, `doc_long()`
- `doc_choices()` for enum values
- `completion_type()` for shell completion hints
- `is_switch()` for boolean vs value-taking

This is essentially an internal CIDL that generates completions. Our system extracts/recreates this.

### 2.2 Performance Analysis

#### 2.2.1 Integration Tiers

| Tier | Mechanism | Latency | Throughput | Complexity |
|------|-----------|---------|------------|------------|
| **A: Subprocess** | Fork+exec per call | ~27ms | ~37 ops/s | Low |
| **B: Daemon** | Persistent process, IPC | ~5ms | ~200 ops/s | Medium |
| **C: Shared Library** | C ABI via FFI | ~1ms | ~1000 ops/s | High |
| **D: Native Extension** | PyO3/N-API direct | ~0.5ms | ~2000 ops/s | Very High |

#### 2.2.2 Benchmark Results (ripgrep)

```
Subprocess (rg):           ~27ms per search
ripgrep_sdk (Tier A):      ~49ms (includes Python overhead)
ripgrep-python (PyO3):     ~64-119ms (surprisingly slower!)
```

**Why is PyO3 slower?**
1. GIL contention in search loops
2. Memory allocation patterns differ
3. ripgrep optimized for CLI, not library use

#### 2.2.3 Performance Recommendations

| Use Case | Recommended Tier | Rationale |
|----------|-----------------|-----------|
| Scripts, automation | A (Subprocess) | Simplicity, good enough |
| Interactive tools | B (Daemon) | Low latency, amortized startup |
| High-throughput | C (Shared Lib) | Best balance if available |
| Embedded/real-time | D (Native) | Only if absolutely required |

### 2.3 Information Source Analysis

#### 2.3.1 What's Available from --help + Autocomplete

| Information | --help | Autocomplete | Coverage |
|-------------|--------|--------------|----------|
| Option names | ✅ | ✅ | 100% |
| Short names | ✅ | ✅ | 100% |
| Descriptions | ✅ | ✅ (short) | 100% |
| Enum choices | ✅ | ✅ | 100% |
| Is switch | Implicit | ✅ | 100% |
| Type hints (file/exec) | ❌ | ✅ (zsh/fish) | 70% |
| Mutual exclusivity | ❌ | ✅ (zsh groups) | 50% |
| Categories | ✅ | ✅ | 100% |

#### 2.3.2 What REQUIRES Codebase Analysis

| Information | Impact | Source |
|-------------|--------|--------|
| **Exit codes** | 🔴 BLOCKER | main.rs |
| **JSON output schema** | 🔴 BLOCKER | jsont.rs |
| **Default values** | 🟡 HIGH | lowargs.rs |
| **Type bounds** | 🟡 MEDIUM | defs.rs |
| **Override rules** | 🟡 MEDIUM | defs.rs (prose) |
| Environment variables | 🟡 MEDIUM | config.rs |

#### 2.3.3 Coverage Summary

```
--help + Autocomplete alone:     70% of SDK requirements
+ NLP on help text:              +20%
+ Codebase analysis (AI):        +10% (but includes BLOCKERS)
```

**Conclusion**: Hybrid approach is REQUIRED, not optional.

### 2.4 Ecosystem Analysis

#### 2.4.1 Existing Solutions Comparison

| Solution | Input | Output | Completeness |
|----------|-------|--------|--------------|
| **Stainless** | OpenAPI | SDKs | Full (API-focused) |
| **complgen** | .usage grammar | Shell completions | Completions only |
| **scog** | YAML | Shell completions | Completions only |
| **clap_complete** | Rust struct | Shell completions | Completions only |
| **Click** | Decorators | Shell completions | Completions only |
| **CLI→SDK (proposed)** | CIDL | Full SDKs | Full (CLI-focused) |

**Gap**: No existing tool generates full SDKs from CLI definitions.

#### 2.4.2 Related Standards

| Standard | Domain | Equivalent In CLI |
|----------|--------|-------------------|
| OpenAPI | REST APIs | **CIDL** (proposed) |
| GraphQL SDL | GraphQL | CIDL |
| Protocol Buffers | RPC | CIDL |
| JSON Schema | Data validation | Part of CIDL |
| TypeScript .d.ts | JS types | SDK type definitions |
| @types/* (DefinitelyTyped) | Community types | **CIDL Registry** (proposed) |

#### 2.4.3 Shell Completion Ecosystem

| Shell | Format | Complexity | Extractable |
|-------|--------|------------|-------------|
| Bash | Shell functions | Medium | Hard |
| Zsh | _arguments DSL | Very High | Medium |
| Fish | complete commands | Low-Medium | Easy |
| PowerShell | Register-ArgumentCompleter | Medium | Medium |

**Finding**: No standard schema exists. Each shell has its own format.
Closest: complgen's .usage grammar, but limited to completions.

---

## 3. Product Requirements

### 3.1 System Components

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLI→SDK System                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐             │
│  │   CIDL      │    │    CIDL     │    │    SDK      │             │
│  │  Extractor  │───▶│   Schema    │───▶│  Generator  │             │
│  └─────────────┘    └─────────────┘    └─────────────┘             │
│         │                  │                  │                     │
│         ▼                  ▼                  ▼                     │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐             │
│  │  - --help   │    │  - Options  │    │  - Python   │             │
│  │  - Complete │    │  - Types    │    │  - TypeScript│            │
│  │  - Source   │    │  - Exit     │    │  - Go       │             │
│  │  - AI Agent │    │  - Schema   │    │  - Rust     │             │
│  └─────────────┘    └─────────────┘    └─────────────┘             │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                      CIDL Registry                           │   │
│  │  (Community-maintained CIDL definitions, like DefinitelyTyped)│  │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 Core Requirements

#### 3.2.1 CIDL Extractor (PRD-002)

**Must Have**:
- Parse `--help` output for options, descriptions, choices
- Parse shell completion scripts (zsh, bash, fish)
- Detect built-in completion generation (`--generate complete-*`)
- AI-assisted source code analysis for gaps

**Should Have**:
- Man page parsing
- Version detection and tracking
- Diff detection for CIDL updates

#### 3.2.2 CIDL Schema (PRD-002)

**Must Have**:
- Command and subcommand definitions
- Option specifications (name, short, type, description)
- Positional argument definitions
- Exit code semantics
- Output format schemas (JSON, etc.)

**Should Have**:
- Environment variable documentation
- Config file format specification
- Override/conflict rules
- Deprecation markers

#### 3.2.3 SDK Generator (PRD-003)

**Must Have**:
- Python SDK generation with full type hints
- Streaming output support
- Proper error handling with typed exceptions
- Async/await support

**Should Have**:
- TypeScript SDK generation
- Go SDK generation
- Rust SDK generation (for non-Rust CLIs)

#### 3.2.4 CIDL Registry (PRD-004)

**Must Have**:
- Version-controlled CIDL storage
- Searchable index
- Contribution workflow

**Should Have**:
- Automated CIDL validation
- SDK auto-generation CI/CD
- Version compatibility tracking

### 3.3 Non-Functional Requirements

| Requirement | Target | Rationale |
|-------------|--------|-----------|
| SDK generation time | <5s per CLI | Fast iteration |
| Generated SDK size | <100KB | Minimal footprint |
| Type coverage | >95% | Match source fidelity |
| Python version | 3.9+ | Modern typing support |
| Documentation | 100% public API | Usability |

---

## 4. Success Metrics

### 4.1 Adoption Metrics

| Metric | Target (6mo) | Target (12mo) |
|--------|--------------|---------------|
| CIDLs in registry | 50 | 200 |
| SDK downloads/month | 1,000 | 10,000 |
| Contributors | 10 | 50 |
| GitHub stars | 500 | 2,000 |

### 4.2 Quality Metrics

| Metric | Target |
|--------|--------|
| SDK test coverage | >90% |
| Type hint accuracy | >99% |
| Exit code coverage | 100% |
| Documentation coverage | 100% |

### 4.3 Performance Metrics

| Metric | Target |
|--------|--------|
| Subprocess overhead | <20ms |
| SDK import time | <100ms |
| Memory overhead | <10MB |

---

## 5. Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| CLI output format changes | High | Medium | Version pinning, auto-detection |
| Incomplete CIDL extraction | Medium | High | AI fallback, community contributions |
| Performance regressions | Medium | Medium | Continuous benchmarking |
| Low adoption | Medium | High | Focus on top 50 CLIs first |
| Maintenance burden | High | Medium | Automation, community model |

---

## 6. Roadmap

### Phase 1: Foundation (Weeks 1-4)
- [ ] Finalize CIDL JSON Schema
- [ ] Build --help parser
- [ ] Build zsh completion parser
- [ ] Create Python SDK generator (Tier A)

### Phase 2: Core (Weeks 5-8)
- [ ] AI-assisted codebase analyzer
- [ ] Exit code extraction
- [ ] JSON schema inference
- [ ] ripgrep SDK as reference implementation

### Phase 3: Registry (Weeks 9-12)
- [ ] CIDL Registry infrastructure
- [ ] Contribution workflow
- [ ] Automated validation
- [ ] CI/CD for SDK publishing

### Phase 4: Scale (Weeks 13-16)
- [ ] Top 50 CLI CIDLs
- [ ] TypeScript generator
- [ ] Performance optimization (Tier B daemon)
- [ ] Documentation site

---

## 7. Appendices

### A. Glossary

| Term | Definition |
|------|------------|
| **CIDL** | CLI Interface Definition Language - structured description of a CLI tool |
| **Tier A** | Subprocess-based integration |
| **Tier B** | Daemon/persistent process integration |
| **Tier C** | Shared library (C ABI) integration |
| **Tier D** | Native extension (PyO3/N-API) integration |

### B. References

- [ripgrep source](https://github.com/BurntSushi/ripgrep)
- [ripgrepy](https://github.com/securisec/ripgrepy)
- [Stainless](https://www.stainlessapi.com/)
- [complgen](https://github.com/adaszko/complgen)
- [zsh-completions](https://github.com/zsh-users/zsh-completions)
- [DefinitelyTyped](https://github.com/DefinitelyTyped/DefinitelyTyped)

### C. Research Artifacts

- `phase0_metrics_and_taxonomy.md` - Metrics framework
- `phase1_ripgrep_source_profile.md` - ripgrep analysis
- `phase2_python_target_profile.md` - Python integration options
- `phase3_tier_adapters.md` - Integration tier specifications
- `phase4_cidl_spec.md` - CIDL schema and examples
- `phase5_performance_patterns.md` - Optimization techniques
- `phase6_cidl_generation_sources.md` - Extraction strategies
- `phase7_help_vs_autocomplete_analysis.md` - Information gap analysis

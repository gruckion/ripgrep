# Gap Analysis: Stainless (REST) vs OpenCLI vs Our Needs

## The "Stainless for CLIs" Vision

You want this workflow:
```
CLI Tool → Spec (CIDL/OpenCLI) → Generator → Production SDK
              ↓                      ↓            ↓
         Auto-extracted      Like Stainless   Python/TS/Go
         or hand-written     "just works"     No glue code
```

## What Stainless Does for REST APIs

| Capability | Stainless | How It Works |
|------------|-----------|--------------|
| **Input** | OpenAPI spec | Upload JSON/YAML |
| **Output** | Production SDKs | Python, TypeScript, Go, Java, Kotlin |
| **HTTP handling** | ✅ Automatic | Requests, retries, backoff |
| **Pagination** | ✅ Automatic | Iterator patterns |
| **Streaming** | ✅ Automatic | SSE, WebSocket support |
| **Error handling** | ✅ Typed exceptions | From HTTP status codes |
| **Types** | ✅ Full coverage | From JSON Schema |
| **Auth** | ✅ Automatic | OAuth, API keys, etc. |
| **Docs** | ✅ Generated | From spec descriptions |
| **Updates** | ✅ Automatic | CI/CD regeneration |
| **Time to SDK** | ~28 seconds | For OpenAI's 24k LOC spec |

**Result**: OpenAI, Anthropic, Cloudflare all use Stainless. Zero glue code.

---

## What OpenCLI Currently Provides

| Capability | OpenCLI | Status |
|------------|---------|--------|
| **Spec format** | ✅ JSON/YAML | Draft spec |
| **Commands** | ✅ Hierarchical | Supported |
| **Options** | ✅ Long/short/aliases | Supported |
| **Arguments** | ✅ Positional | Supported |
| **Types** | ✅ Basic | string, int, bool, etc. |
| **Descriptions** | ✅ For docs | Supported |
| **Exit codes** | ❌ Not specified | Missing |
| **Output schema** | ❌ Not specified | Missing |
| **Streaming** | ❌ Not addressed | Missing |
| **Stdin/stdout types** | ❌ Not specified | Missing |
| **SDK generation** | ⚠️ Mentioned as goal | No implementation |
| **Error mapping** | ❌ Not specified | Missing |
| **Tooling** | ⚠️ Minimal | Schema validation only |

**Current State**: OpenCLI is a **spec only**, no SDK generator exists.

---

## What TypeSpec Provides

| Capability | TypeSpec | Notes |
|------------|----------|-------|
| **Primary focus** | REST/Cloud APIs | Not CLI-focused |
| **SDK generation** | ✅ Yes | Python, JS, C#, Java |
| **CLI support** | ❌ No | Not designed for CLIs |
| **Used by** | Azure SDKs | Microsoft internal |

**Verdict**: TypeSpec generates OpenCLI's JSON Schema, but doesn't help with CLI→SDK.

---

## The Gap: What's Missing for "Stainless for CLIs"

### Critical Missing Pieces

| Component | REST (Stainless) | CLI (Today) | Gap |
|-----------|------------------|-------------|-----|
| **Spec** | OpenAPI ✅ | OpenCLI (draft) | ⚠️ Incomplete |
| **Exit codes** | HTTP status → exceptions | Nothing | 🔴 BLOCKER |
| **Output schema** | JSON Schema response | Nothing | 🔴 BLOCKER |
| **Streaming** | SSE/WebSocket | stdout parsing | 🔴 BLOCKER |
| **SDK Generator** | Stainless, Speakeasy | **Does not exist** | 🔴 BLOCKER |
| **Error handling** | 4xx/5xx → typed errors | Exit code → ??? | 🔴 BLOCKER |

### What Needs to Be Built

```
┌─────────────────────────────────────────────────────────────────┐
│                    "Stainless for CLIs"                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. SPEC EXTENSION (extend OpenCLI or create CIDL)              │
│     ├── Exit code definitions                                    │
│     ├── Output schemas (JSON, structured text)                   │
│     ├── Streaming indicators                                     │
│     ├── Error message patterns                                   │
│     └── Environment variable effects                             │
│                                                                  │
│  2. EXTRACTOR (auto-generate spec from CLI)                     │
│     ├── Parse --help                                            │
│     ├── Parse shell completions                                 │
│     ├── AI-assisted codebase analysis                           │
│     └── Runtime probing (exit codes, output formats)            │
│                                                                  │
│  3. SDK GENERATOR (the core product) ← DOES NOT EXIST           │
│     ├── subprocess management                                    │
│     ├── Argument building from method calls                     │
│     ├── Output parsing (JSON, text patterns)                    │
│     ├── Exit code → exception mapping                           │
│     ├── Streaming → iterators/generators                        │
│     ├── Type generation from schema                             │
│     └── Multi-language (Python, TypeScript, Go, Rust)           │
│                                                                  │
│  4. REGISTRY (like DefinitelyTyped)                             │
│     ├── Community-maintained specs                              │
│     ├── Auto-update detection                                   │
│     └── Published SDKs (PyPI, npm)                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Honest Assessment

### OpenCLI Gets You: 30%
- ✅ Spec format for commands/options/arguments
- ✅ Mentioned goal of SDK generation
- ❌ No actual SDK generator
- ❌ Missing exit codes, output schema, streaming

### TypeSpec Gets You: 0% (for CLIs)
- Only generates OpenCLI's JSON Schema
- Designed for REST APIs, not CLIs
- SDK generation is REST-focused

### What You'd Still Need to Build: 70%

| Component | Effort | Exists? |
|-----------|--------|---------|
| Exit code spec extension | Medium | No |
| Output schema spec extension | Medium | No |
| **SDK Generator** | **Large** | **No** |
| Spec extractor | Medium | Partial (our research) |
| Registry | Medium | No |

---

## Recommendation

### Option A: Extend OpenCLI + Build Generator
1. Contribute exit codes, output schemas to OpenCLI spec
2. Build the SDK generator ourselves
3. Collaborate with Patrik Svensson (OpenCLI creator)

**Pros**: Leverage existing community, avoid fragmentation
**Cons**: May need to compromise on spec design

### Option B: Full CIDL Stack
1. Use our CIDL spec (already has exit codes, output schemas)
2. Build the SDK generator
3. Provide OpenCLI compatibility layer

**Pros**: Full control, already designed for SDK generation
**Cons**: Competing standard, less community

### Option C: Wait
1. Hope OpenCLI adds missing pieces
2. Hope someone builds a generator

**Pros**: No work
**Cons**: May never happen; no one is building this

---

## The Bottom Line

**No "Stainless for CLIs" exists today.**

- OpenCLI is a spec (30% of the puzzle)
- TypeSpec helps OpenCLI generate JSON Schema (not relevant)
- The SDK generator (70% of the puzzle) **does not exist**

To get what you want, someone needs to build:
1. Spec extension for exit codes + output schemas
2. **The SDK generator** (the hard part)
3. Extractor tooling
4. Registry infrastructure

Our research has already done the spec design work (CIDL). The SDK generator is the missing product.

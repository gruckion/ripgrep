# CLI Specification Gaps & Opportunities Research

**Research Date**: 2025-01-11
**Context**: CLI-to-SDK System Research Phase
**Status**: Complete

---

## Executive Summary

The CLI specification landscape is evolving rapidly. OpenCLI (opencli.org), created by Patrik Svensson in July 2025, has claimed the "OpenCLI" name and domain. Our research reveals significant gaps in ALL existing specifications that present opportunities for differentiation or contribution.

**Key Findings**:
1. The name "Open CLI Spec" conflicts with OpenCLI at opencli.org
2. All existing specs (OpenCLI, Usage, docopt, ONAP OCS) have major gaps
3. Collaboration with OpenCLI may be more strategic than competition
4. The CLI specification space is less mature than API specifications

---

## Q7: Naming Strategy Analysis

### Current Landscape Conflict

**OpenCLI** is already claimed:
- **Domain**: opencli.org (active)
- **GitHub**: github.com/spectreconsole/open-cli
- **Creator**: Patrik Svensson (Spectre.Console creator)
- **Announced**: July 7, 2025
- **Status**: Draft specification, actively seeking community input

Source: [Patrik Svensson - Introducing OpenCLI](https://patriksvensson.se/posts/2025/07/introducing-open-cli)

### Alternative Name Analysis

| Candidate Name | Domain | Analysis | Verdict |
|---------------|--------|----------|---------|
| **CLI Blueprint** | cliblueprint.dev | Multiple unrelated "blueprint CLI" tools exist (AWS CodeCatalyst, Juniper, etc.). Term is somewhat generic but not claimed as a specification name. | Possible |
| **CLISpec** | clispec.org | Ruby gem "clispec" exists for testing. Generic but memorable. Low conflict risk. | Strong |
| **Command Schema** | commandschema.org | No existing specification. Clear meaning. Aligns with JSON Schema ecosystem. | Strong |
| **CLI Definition Language** (CDL) | N/A | Matches "IDL" pattern. CodeSynthesis has "CLI language" for C++. Risk of confusion. | Medium |
| **Universal CLI Spec** (UCS) | N/A | Bold claim. May face adoption resistance. No existing conflicts found. | Medium |
| **CLI Interface Spec** (CLIS) | N/A | Redundant (CLI already has "Interface"). Could confuse with ECMA CLI (.NET). | Weak |
| **CIDL** | N/A | Already used in our research. "CLI Interface Definition Language". Novel. | Strong |

### Successful Specification Naming Patterns

| Specification | Naming Pattern | Key Success Factor |
|--------------|----------------|-------------------|
| **OpenAPI** | "Open" + Domain | Neutrality signal, Linux Foundation backing |
| **GraphQL** | Descriptive + Novel | Clear purpose (Graph Query Language) |
| **Protocol Buffers** | Technical + Descriptive | Backed by Google, clear function |
| **JSON Schema** | Format + Function | Builds on existing standard (JSON) |
| **AsyncAPI** | "Async" + Existing Standard | Positioned as "OpenAPI for events" |

**Patterns for success**:
1. **Neutrality Signal**: "Open" prefix indicates vendor-neutral governance
2. **Clear Purpose**: Name should suggest function
3. **Differentiator**: What makes it different from existing standards
4. **Avoiding Trademarks**: Check USPTO, existing projects, domain availability

Source: [How to choose a brand name for your open source project](https://opensource.com/business/16/2/how-choose-brand-name-open-source-project)

### Recommendation: Naming Strategy

**Primary Recommendation**: **CIDL** (CLI Interface Definition Language)

**Rationale**:
1. Novel term with no existing conflicts
2. Follows established "IDL" pattern (MIDL, AIDL, RIDL)
3. Already used extensively in our research documentation
4. Clear technical meaning
5. Short, memorable, distinct from OpenCLI

**Alternative**: **Command Schema**
- More accessible to non-experts
- Aligns with JSON Schema ecosystem
- Lower barrier to understanding

### Should We Contribute to OpenCLI Instead?

**OpenCLI Status Assessment**:
- Draft specification (incomplete)
- Actively seeking community input
- 2 open issues, discussions enabled
- Built with .NET tooling (Cake, .NET 9.0 SDK)

**What Differentiates Our Vision (CIDL)**:

| Aspect | OpenCLI (Current) | CIDL (Our Vision) |
|--------|------------------|-------------------|
| **Exit Codes** | Not specified | Full semantic mapping with exception correlation |
| **Output Schemas** | Basic mention | Full JSON Schema integration, streaming support |
| **SDK Generation** | "Generate clients" listed | Bidirectional: introspection + generation |
| **Performance** | Not addressed | Performance hints, streaming, parallelism |
| **Security** | Not addressed | Input validation contracts, injection prevention |
| **Cross-Platform** | "Platform agnostic" | Explicit behavioral contracts for Windows/Linux/macOS |
| **Type System** | Basic types | Rich semantic types, domain-specific extensions |

**Recommendation**: **Dual approach**
1. **Short-term**: Contribute to OpenCLI discussions on gaps we've identified
2. **Long-term**: If OpenCLI doesn't evolve to address gaps, fork or propose CIDL as complementary spec

---

## Q8: Gap Analysis - Missing Capabilities

### Methodology

Analyzed gaps across:
- **OpenCLI** (Spectre.Console, July 2025)
- **Usage Specification** (jdx.dev)
- **docopt** (docopt.org)
- **ONAP OCS** (Open Command Specification)

### Gap Matrix

| Capability | OpenCLI | Usage | docopt | ONAP OCS | CIDL (Our Spec) |
|-----------|---------|-------|--------|----------|-----------------|
| **Basic Arguments** | Yes | Yes | Yes | Yes | Yes |
| **Options/Flags** | Yes | Yes | Yes | Yes | Yes |
| **Subcommands** | Yes | Yes | Partial | Yes | Yes |
| **Enum Choices** | Yes | Yes | No | Yes | Yes |
| **Descriptions** | Yes | Yes | Yes | Yes | Yes |
| **Exit Code Semantics** | No | No | Partial (64) | Partial | **Yes** |
| **Exit-to-Exception Mapping** | No | No | No | No | **Yes** |
| **Output Format Schemas** | No | No | No | No | **Yes** |
| **JSON/Structured Output** | No | No | No | No | **Yes** |
| **Streaming Output Handling** | No | No | No | No | **Yes** |
| **Performance Characteristics** | No | No | No | No | **Yes** |
| **Parallelism Hints** | No | No | No | No | **Yes** |
| **Semantic Typing** | Basic | Basic | No | Basic | **Rich** |
| **Bidirectional SDK Gen** | Partial | No | No | No | **Yes** |
| **CLI Introspection** | No | No | No | No | **Yes** |
| **Cross-Platform Contracts** | No | No | No | No | **Yes** |
| **Formal Verification** | No | No | No | No | **Possible** |
| **Input Validation Rules** | No | No | No | No | **Yes** |
| **Security Annotations** | No | No | No | No | **Yes** |
| **Config File Integration** | No | Yes | No | No | **Yes** |
| **Environment Variables** | Basic | Yes | No | Yes | **Yes** |

### Detailed Gap Analysis

#### 1. Exit Code Semantics and Exception Mapping

**Current State**: Most specs ignore exit codes entirely.
- **docopt**: Returns EX_USAGE (64) on parse failure
- **ONAP OCS**: Implicit success/failure only
- **OpenCLI/Usage**: No exit code specification

**Gap**: No spec defines:
- Semantic meaning of exit codes (e.g., 0=match found, 1=no match, 2=error)
- How SDK should map exit codes to exceptions/errors
- Exit code ranges for categories (signals, user errors, system errors)

**CIDL Approach**:
```yaml
exit_codes:
  0:
    name: SUCCESS_WITH_MATCHES
    exception: null
    description: "At least one match was found"
  1:
    name: SUCCESS_NO_MATCHES
    exception: NoMatchesFound  # Not an error, but distinct
    description: "Search completed but no matches found"
  2:
    name: ERROR
    exception: RipgrepError
    description: "An error occurred"
```

Source: [docopt exit handling issue](https://github.com/docopt/docopt/issues/106)

#### 2. Output Format Schemas

**Current State**: No existing spec handles structured output.

**Gap**: CLIs increasingly support `--json` or structured output, but:
- No schema definition for JSON output
- No streaming JSON (JSON Lines) specification
- No way to generate type-safe SDK response parsers

**CIDL Approach**:
```yaml
output:
  modes:
    text:
      format: text
      streaming: true
    json:
      format: jsonlines
      streaming: true
      trigger: "--json"
      schema:
        $ref: "#/schemas/Match"

schemas:
  Match:
    type: object
    properties:
      type: { const: "match" }
      data:
        $ref: "#/schemas/MatchData"
```

Source: [Tips on Adding JSON Output to Your CLI App](https://blog.kellybrazil.com/2021/12/03/tips-on-adding-json-output-to-your-cli-app/)

#### 3. Streaming Output Handling

**Current State**: Not addressed by any specification.

**Gap**: Many CLIs produce streaming output (grep, ripgrep, find), but specs don't define:
- Buffering behavior
- Progressive result handling
- Memory management expectations

**CIDL Approach**:
```yaml
performance:
  streaming_safe: true
  buffer_behavior: line  # or: none, chunk, full
  memory_model: O(1)     # Constant memory per result
```

#### 4. Performance Characteristics

**Current State**: Completely absent from all specs.

**Gap**: SDK generators need to know:
- Is the operation parallelizable?
- What can be cached?
- Is the operation idempotent?
- Does it have side effects?

**CIDL Approach**:
```yaml
performance:
  parallelism: file-level  # none, file-level, directory-level, unlimited
  cacheable:
    - compiled_regex
    - file_type_definitions
  idempotent: true
  side_effects: false
```

#### 5. Semantic Typing Beyond Basic Types

**Current State**:
- **docopt**: No type checking at all ("limits applications for which this library is useful")
- **OpenCLI**: Basic types (string, int, bool)
- **Usage**: Basic types with choices

**Gap**: No support for:
- Domain-specific types (file paths, URLs, email, IP addresses)
- Type validation patterns (regex constraints)
- Numeric bounds (min/max values)
- Unit types (size: "10MB", duration: "30s")

**CIDL Approach**:
```yaml
types:
  ThreadCount:
    base: integer
    bounds: { min: 1, max: null }  # null = runtime-determined
    env_override: RIPGREP_THREADS

  FileSize:
    base: string
    pattern: "^\\d+[KMGT]?B?$"
    examples: ["10M", "1GB"]
```

Source: [docopt type checking issue](https://github.com/docopt/docopt.cpp/issues/39)

#### 6. Bidirectional SDK Generation

**Current State**:
- **OpenCLI**: "Generate clients" mentioned, not detailed
- All others: One-way (spec -> code) or none

**Gap**: No spec supports:
- Introspection: Running CLI to extract spec
- Round-tripping: Spec -> SDK -> invocations that match spec
- Verification: Checking SDK behavior matches spec

**CIDL Approach**:
- Define introspection protocol (`--cidl-dump`)
- Generate SDK that can be verified against spec
- Support extracting spec from running CLI

Source: [gRPC Server Reflection](https://github.com/grpc/grpc/blob/master/doc/server-reflection.md)

#### 7. Cross-Platform Behavioral Contracts

**Current State**: "Platform agnostic" claims without substance.

**Gap**: Real differences exist:
- Path separators (/ vs \)
- Exit code ranges (Windows uses larger values)
- Signal handling (SIGPIPE on Unix, none on Windows)
- Encoding (UTF-8 vs. system codepages)
- Temp file behavior (deletion semantics differ)

**CIDL Approach**:
```yaml
platform_behaviors:
  unix:
    signals:
      SIGPIPE: "ignored"
      SIGINT: "graceful_shutdown"
  windows:
    exit_code_mapping:
      # Windows exit codes > 255 need mapping
      ERROR_FILE_NOT_FOUND: 2
```

Source: [Five Considerations When Building Cross-Platform Tools](https://semgrep.dev/blog/2025/five-considerations-when-building-cross-platform-tools-for-windows-and-macos/)

#### 8. Formal Verification Possibilities

**Current State**: No CLI spec supports formal verification.

**Gap**: For safety-critical CLIs:
- No way to express invariants
- No property-based testing contracts
- No proofs of input handling correctness

**CIDL Future Extension**:
```yaml
contracts:
  search:
    preconditions:
      - "pattern != ''"
      - "paths.all(path => exists(path))"
    postconditions:
      - "exit_code in {0, 1, 2}"
    invariants:
      - "matches.all(m => m.line_number > 0)"
```

Source: [Formal Verification Wikipedia](https://en.wikipedia.org/wiki/Formal_verification)

#### 9. Security Considerations

**Current State**: No CLI spec addresses security.

**Gap**: Critical security gaps:
- No input validation requirements
- No command injection prevention guidance
- No secrets handling specification
- No privilege escalation markers

**CIDL Approach**:
```yaml
security:
  input_validation:
    pattern:
      sanitize: false  # Regex is inherently safe
      max_length: 65536
    paths:
      allow_shell_expansion: false
      validate_existence: optional

  privilege:
    requires_elevated: false
    drops_privileges: false

  sensitive_options:
    - name: password
      masked: true
      no_log: true
```

Source: [OWASP OS Command Injection Defense](https://cheatsheetseries.owasp.org/cheatsheets/OS_Command_Injection_Defense_Cheat_Sheet.html)

---

## Q9: Collaboration & Unification Opportunity

### Historical Precedent: RAML + API Blueprint + Swagger -> OpenAPI

**Timeline**:
- **2010**: Swagger development begins at Wordnik (Tony Tam)
- **2013**: RAML 0.8 released by MuleSoft
- **2013**: API Blueprint released by Apiary
- **2015**: SmartBear acquires Swagger, donates to Linux Foundation
- **2015**: OpenAPI Initiative founded (10 founding members)
- **2016**: Apiary joins OpenAPI Initiative
- **2016**: Swagger spec renamed to OpenAPI Specification
- **2017**: MuleSoft joins OpenAPI Initiative

**Key Quote**: "Instead of keeping direct competition between the three efforts going on, hoping that one would win and replace the two others, a better path became necessary and possible."

**Outcome**:
- OpenAPI dominates (55% adoption)
- RAML and API Blueprint still exist but with ~7% combined
- Convergence, not merging, of efforts

Sources:
- [RAML and API Blueprint: where are they now?](https://blog.postman.com/raml-and-api-blueprint-where-are-they-now/)
- [MuleSoft Joins the OpenAPI Initiative](https://swagger.io/blog/news/mulesoft-joins-the-openapi-initiative/)
- [Competitors Join OAI](https://www.openapis.org/blog/2017/05/02/competitors-join-oai-to-lead-convergence-of-api-landscape)

### Lessons for CLI Specification Space

1. **First-mover advantage is real but not absolute**: Swagger dominated but needed to evolve
2. **Joining forces > competing**: MuleSoft's RAML team contributed to OpenAPI
3. **Governance matters**: Linux Foundation neutrality enabled collaboration
4. **Convergence != merging**: RAML still exists, but OpenAPI is the standard

### CLI Specification Landscape Comparison

| Spec | Creator | Status | Adoption | Governance |
|------|---------|--------|----------|-----------|
| **OpenCLI** | Patrik Svensson | Draft | Early | Individual/Spectre.Console |
| **Usage** | jdx | Active | Growing (mise users) | Individual |
| **docopt** | Vladimir Keleshev | Stable | Mature but stagnant | Individual |
| **ONAP OCS** | Linux Foundation/ONAP | Active | ONAP-specific | Linux Foundation |
| **CIDL (ours)** | Research phase | Proposal | None yet | TBD |

### Unification Strategy Options

#### Option A: Contribute to OpenCLI
**Pros**:
- Existing community and momentum
- Domain and branding established
- Patrik Svensson is respected in .NET community

**Cons**:
- .NET-centric tooling
- May not be open to major architectural changes
- Our gaps might not align with their vision

**Action Items**:
1. Open discussions on OpenCLI GitHub for each gap we've identified
2. Propose CIDL concepts as extensions
3. Gauge community reception

#### Option B: Propose CIDL as Extension/Complementary Spec
**Pros**:
- Freedom to fully address gaps
- Can reference OpenCLI for basic structure
- Position as "OpenCLI for SDK generation"

**Cons**:
- Fragmentation concern
- Starting from zero adoption
- Need our own governance

**Action Items**:
1. Publish CIDL spec with clear differentiation
2. Create converter: OpenCLI <-> CIDL
3. Position as complementary, not competing

#### Option C: Propose CLI Working Group to Linux Foundation
**Pros**:
- Neutral governance
- Model proven by OpenAPI, GraphQL Foundation
- Could unify all CLI spec efforts

**Cons**:
- Significant organizational overhead
- Needs corporate sponsors
- 1-2 year timeline to establish

**Action Items**:
1. Research Linux Foundation project submission process
2. Identify potential corporate sponsors
3. Draft working group charter

### Governance Model Analysis

| Model | Example | Pros | Cons |
|-------|---------|------|------|
| **Linux Foundation** | OpenAPI, GraphQL | Neutral, proven, professional | Slow, requires sponsors |
| **Independent Foundation** | Rust Foundation | Focused, agile | Needs substantial funding |
| **Company-Backed** | GraphQL (originally Facebook) | Resources, momentum | Perceived bias |
| **Individual Maintainer** | docopt, OpenCLI (current) | Fast decisions | Bus factor, sustainability |

**Recommendation**: Start as individual/small team, plan for Linux Foundation transition if adoption grows.

### Fragmentation vs. Unification: What's Better Now?

**Arguments for Fragmentation (Multiple Specs)**:
1. Different use cases (SDK generation vs. documentation vs. completion)
2. Innovation through competition
3. Early stage - too early to standardize
4. Allows experimentation with missing capabilities

**Arguments for Unification (Single Spec)**:
1. Tooling ecosystem benefits from single target
2. Developer learning curve reduced
3. Prevents confusion
4. Network effects accelerate adoption

**Assessment**: The CLI specification space is **less mature than API specifications were in 2015**. Some fragmentation is healthy to explore the design space, but a unification effort should begin within 1-2 years.

**Recommendation**: **Pursue Option B now, plan for Option C in 18-24 months**.

---

## Strategic Recommendations

### Naming Decision

**Adopt "CIDL" (CLI Interface Definition Language)** as our specification name.

**Rationale**:
1. No conflicts with existing projects
2. Clear technical meaning (follows IDL pattern)
3. Differentiates from OpenCLI's more basic scope
4. Already used in our research (continuity)

### Gap Positioning

Position CIDL as addressing these **unique capabilities**:
1. **Exit code semantics** - No other spec has this
2. **Output schema integration** - JSON Schema for CLI output
3. **Bidirectional SDK generation** - Introspection + generation
4. **Performance contracts** - First to address streaming, parallelism
5. **Security annotations** - Unique in CLI spec space

### Collaboration Strategy

**Phase 1 (Immediate)**: Engage with OpenCLI
- Open GitHub discussions on gaps
- Offer to contribute exit code and output schema extensions
- Build relationship with Patrik Svensson

**Phase 2 (3-6 months)**: Establish CIDL
- Publish CIDL specification
- Create reference implementation
- Build OpenCLI <-> CIDL converter
- Position as "complementary for advanced use cases"

**Phase 3 (12-24 months)**: Drive Unification
- If adoption grows, propose Linux Foundation CLI Working Group
- Invite OpenCLI, Usage, and other spec maintainers
- Goal: CIDL features merge into unified spec

### Success Metrics

| Metric | 6 Month Target | 18 Month Target |
|--------|---------------|-----------------|
| GitHub stars | 500 | 2,500 |
| CLI tools with CIDL specs | 10 | 100 |
| SDK generators using CIDL | 2 (Python, TypeScript) | 5+ |
| Corporate contributors | 1 | 3 |
| Community engagement (discussions/issues) | 50 | 500 |

---

## Appendix: Research Sources

### Primary Sources
- [OpenCLI Specification](https://opencli.org/)
- [Patrik Svensson - Introducing OpenCLI](https://patriksvensson.se/posts/2025/07/introducing-open-cli)
- [Usage Specification](https://usage.jdx.dev/spec/)
- [docopt - Language for CLI Interfaces](http://docopt.org/)
- [ONAP Open CLI Platform](https://docs.onap.org/projects/onap-cli/en/latest/OCLIP.html)

### OpenAPI/API Specification Convergence
- [A brief history of the OpenAPI Specification](https://dev.to/mikeralphson/a-brief-history-of-the-openapi-specification-3g27)
- [RAML and API Blueprint: where are they now?](https://blog.postman.com/raml-and-api-blueprint-where-are-they-now/)
- [MuleSoft Joins the OpenAPI Initiative](https://swagger.io/blog/news/mulesoft-joins-the-openapi-initiative/)
- [OpenAPI Specification Governance](https://github.com/OAI/OpenAPI-Specification/blob/main/GOVERNANCE.md)

### Governance Models
- [Linux Foundation Standards and Specifications](https://www.linuxfoundation.org/projects/standards)
- [GraphQL Foundation Governance](https://graphql.org/community/contribute/governance/)
- [Joint Development Foundation](https://www.linuxfoundation.org/blog/blog/joint-development-foundation-celebrates-10-years-of-high-impact-open-standards-innovation-and-development)

### Security and Best Practices
- [OWASP OS Command Injection Defense](https://cheatsheetseries.owasp.org/cheatsheets/OS_Command_Injection_Defense_Cheat_Sheet.html)
- [Five Considerations for Cross-Platform CLI Tools](https://semgrep.dev/blog/2025/five-considerations-when-building-cross-platform-tools-for-windows-and-macos/)

### Naming and Branding
- [How to choose a brand name for your open source project](https://opensource.com/business/16/2/how-choose-brand-name-open-source-project)
- [A look at 6 iconic open source brands](https://opensource.com/article/17/2/six-open-source-brands)

---

*Research conducted 2025-01-11. Sources verified via web search.*

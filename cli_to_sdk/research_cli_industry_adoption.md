# CLI Specification Industry Adoption & Tools Research

**Research Date**: January 2025
**Focus**: Industry adoption status, AI/LLM integration, and tooling ecosystems for CLI specifications

---

## Table of Contents

1. [Q4: Adoption Status & Ecosystem Maturity](#q4-adoption-status--ecosystem-maturity)
2. [Q5: AI/LLM CLI Tool Discovery](#q5-aillm-cli-tool-discovery)
3. [Q6: Tooling Ecosystems](#q6-tooling-ecosystems)
4. [Key Findings & Conclusions](#key-findings--conclusions)

---

## Q4: Adoption Status & Ecosystem Maturity

### Overview Matrix

| Specification | Creator | Status | GitHub Stars | Language Support | Primary Use Case |
|--------------|---------|--------|--------------|------------------|------------------|
| **OpenCLI (OCS)** | Patrik Svensson | Draft (July 2025) | 211 | .NET (Spectre.Console) | Multi-purpose: docs, AI, automation |
| **Usage Spec (KDL)** | jdx (mise) | Active | Part of mise (~10k+) | Rust (usage-lib) | Shell completions, documentation |
| **docopt** | Vladimir Keleshev | Inactive/Legacy | ~8k (fragmented) | 15+ languages | Help-as-spec parsing |
| **ONAP OCS** | Linux Foundation | Active | 4 (archived CLI) | Java | Enterprise telecom automation |

---

### 1. OpenCLI (spectreconsole/open-cli)

**Overview**: The OpenCLI specification (OCS) defines a standard, platform and language-agnostic interface to CLI applications, allowing both humans and computers to understand how a CLI tool should be invoked without access to source code or documentation.

#### GitHub Statistics
- **Stars**: 211
- **Forks**: 8
- **Watchers**: 5
- **Contributors**: 4
- **Total Commits**: 46 on main branch
- **License**: MIT
- **Status**: Draft specification (no releases yet)

#### Framework Integrations

| Framework | Language | Integration Status | Details |
|-----------|----------|-------------------|---------|
| Spectre.Console | .NET/C# | **Official** (v0.52+) | `--help-dump-opencli` flag generates OCS output |

**Spectre.Console Stats** (parent framework):
- 11,043 GitHub stars
- 627 forks
- 115+ contributors
- .NET Foundation supported
- Used by Microsoft teams and .NET community

#### Language Support
- **Native**: .NET/C# (via Spectre.Console)
- **Planned**: Language-agnostic JSON/YAML schema allows any language implementation
- **Current Gap**: No implementations outside .NET ecosystem yet

#### Key Use Cases (per specification)
1. Create documentation for CLI tools
2. Generate clients for interacting with CLI tools
3. **Automate external tools such as MCP servers**
4. Detect changes in CLI APIs
5. Generate auto-completion scripts

#### Barriers to Broader Adoption
1. **Very New**: Only introduced July 2025, still in draft
2. **Single Framework**: Currently only integrated with Spectre.Console
3. **Limited Tooling**: No standalone validators, converters, or generators yet
4. **Community Size**: Small contributor base (4 people)
5. **Competing with OpenAPI mindshare**: Developers familiar with OpenAPI may expect similar tooling maturity

**Sources**:
- [OpenCLI GitHub Repository](https://github.com/spectreconsole/open-cli)
- [OpenCLI Specification](https://opencli.org/)
- [Introducing OpenCLI Blog Post](https://patriksvensson.se/posts/2025/07/introducing-open-cli)

---

### 2. Usage Spec (jdx/mise)

**Overview**: Usage is a spec and CLI for defining CLI tools - essentially "OpenAPI (swagger) for CLIs" using KDL (KDL Document Language) format.

#### Adoption in mise Ecosystem

The Usage specification serves as a single source of truth for defining all CLI commands, arguments, flags, and help documentation in mise.

**mise Project Stats**:
- **Status**: Production-ready, mature
- **Growth**: Hit Hacker News front page in 2024, "thousands of stargazers"
- **Enterprise Adoption**: Increasing, especially since tasks came out of experimental
- **Latest Version**: mise 2025.12.0
- **Recommendation**: Officially recommended by tuist

#### Framework Integrations

| Framework | Language | Integration Status | Details |
|-----------|----------|-------------------|---------|
| mise | Rust | Native | Core use case |
| hk | Rust | Native | Uses hk.usage.kdl |
| usage-lib | Rust | Library | Bridges clap API to Usage spec |

#### Language Support
- **Native**: Rust (via usage-lib crate)
- **Design**: Language-agnostic KDL format
- **Gap**: No official implementations for Python, Go, Node.js, etc.

#### Generated Outputs
- Shell completions (bash, zsh, fish)
- Markdown documentation
- Man pages
- CLI argument parsing

#### Barriers to Broader Adoption
1. **Rust-centric**: usage-lib only available for Rust
2. **KDL Format**: Less familiar than JSON/YAML for most developers
3. **Tied to mise**: Primarily designed for mise ecosystem
4. **Limited Promotion**: Not marketed as standalone specification
5. **No Formal Versioning**: Specification versioning unclear

**Sources**:
- [Usage Specification](https://usage.jdx.dev/spec/)
- [mise GitHub Repository](https://github.com/jdx/mise)
- [mise Usage KDL File](https://github.com/jdx/mise/blob/main/mise.usage.kdl)

---

### 3. docopt

**Overview**: docopt is a "language for description of command-line interfaces" where the help message IS the specification - "you write the help message first, and get a parser for free."

#### Language Implementations

| Language | Repository | Status | Notes |
|----------|------------|--------|-------|
| Python | docopt/docopt | **Inactive** | Reference implementation, last major update years ago |
| Python (fork) | docopt-ng | **Active** | Maintained fork with type hints (updated Aug 2025) |
| Rust | docopt-rs | Maintained | Alternative to clap |
| Ruby | docopt.rb | Legacy | |
| Go | docopt-go | Legacy | |
| C++ | docopt.cpp | Legacy | |
| Haskell | docopt | Available | On Hackage |
| .NET | docopt.net | Legacy | |
| JavaScript | docopt | **Inactive** | 1 weekly npm download, unmaintained |
| JavaScript | neodoc | Active | Improved fork with 95%+ compatibility |
| Shell | docopts | Legacy | Shell interpreter |
| Nim | docopt.nim | Legacy | |
| R | docopt | **Active** | CRAN package, updated March 2025 |
| PHP | docopt-php | Legacy | |
| C | docopt.c | Legacy | Code generator |

#### GitHub Statistics (Aggregate)
- **Python (original)**: ~8k stars (fragmented across forks)
- **npm (docopt)**: ~500 dependents, but only 1 weekly download
- **Implementations**: 15+ languages

#### Framework Integrations
- **None formal**: docopt is a parsing approach, not integrated into frameworks
- **Philosophy**: Replaces frameworks rather than integrating with them

#### Barriers to Broader Adoption
1. **Maintenance Abandoned**: Original project unmaintained since ~2017
2. **Fragmentation**: Multiple forks with incompatible features
3. **No 1.0 Release**: "Soon" promised for years, never delivered
4. **Limited Expressiveness**: Cannot model all CLI patterns (GNU-style focus)
5. **No Modern Features**: Missing shell completions, man page generation
6. **Competition**: clap (Rust), Click (Python), Cobra (Go) offer more features

**Sources**:
- [docopt Official Site](http://docopt.org/)
- [docopt GitHub Organization](https://github.com/docopt)
- [docopt-ng (Active Fork)](https://github.com/jazzband/docopt-ng)
- [docopt Maintenance Issue](https://github.com/docopt/docopt/issues/371)

---

### 4. ONAP OCS (Open Command Specification)

**Overview**: The Open CLI Platform (OCLIP) defines Open Command Specification (OCS) for CLI, similar to OpenAPI specification for REST APIs, specifically designed for telecom network automation.

#### Enterprise Adoption

**Target Users**:
- Communication Service Providers (CSPs)
- Telecom operators (AT&T, China Mobile, Huawei, ZTE)
- Network automation engineers

**ONAP Background**:
- Formed February 2017 from merger of OpenECOMP (AT&T) and Open-Orchestrator (Open-O)
- Part of LF Networking Fund (Linux Foundation)
- Major enterprise telecom focus

#### GitHub Statistics
- **Stars**: 4
- **Forks**: 4
- **Status**: Repository archived (onap/archived-cli)

#### Framework Integrations

| Integration | Type | Details |
|-------------|------|---------|
| OCLIP | Java Framework | Model-based CLI development using YAML templates |
| VNF Test Platform | Testing | Uses OCLIP for test case execution |
| ONAP Components | Orchestration | CLI for SDNC, VNFM, EMS |

#### Language Support
- **Primary**: Java (OCLIP platform)
- **Template Format**: YAML
- **Scope**: Enterprise telecom only

#### Key Features
- Catalog/discovery mode for service details
- Multi-product support (ONAP, VNFM, SDNC, EMS, commercial products)
- Template-based command modeling
- CI/CD integration support

#### Barriers to Broader Adoption
1. **Niche Domain**: Designed exclusively for telecom/network automation
2. **Enterprise Complexity**: Requires ONAP infrastructure
3. **Archived Repository**: Limited active development
4. **No General-Purpose Use**: Not designed for typical CLI applications
5. **Heavy Dependencies**: Requires Java and OCLIP platform

**Sources**:
- [ONAP OCS 1.0 Specification](https://docs.onap.org/projects/onap-cli/en/latest/open_cli_schema_version_1_0.html)
- [OCLIP Documentation](https://docs.onap.org/projects/onap-cli/en/latest/OCLIP.html)
- [ONAP CLI GitHub](https://github.com/onap/cli)

---

## Q5: AI/LLM CLI Tool Discovery

### Current Approaches

#### 1. Model Context Protocol (MCP)

**Overview**: MCP is an open specification (launched late 2024) for connecting LLM clients to external tools and resources.

**Tool Discovery Mechanism**:
```
Client sends: tools/list request
Server returns: Tool metadata with JSON Schema definitions
```

**Key Features** (Protocol Revision 2025-06-18):
- Tools uniquely identified by name with metadata describing schema
- Output schema validation for structured results
- Pagination support for large tool lists
- OAuth 2.0 Resource Server security model

**Tool Schema Structure**:
```json
{
  "name": "tool_name",
  "description": "What the tool does",
  "inputSchema": { /* JSON Schema */ },
  "outputSchema": { /* JSON Schema (optional) */ }
}
```

**Adoption** (2025):
- MCP Registry launched preview September 2025
- API freeze (v0.1) on October 24, 2025
- ~2,000 MCP servers scanned by security researchers
- Adopted by Claude, OpenAI (via AGENTS.md), Cursor, and others

**mcp-cli Tool**:
- Lightweight CLI for dynamic MCP discovery
- Commands: `mcp-cli` (list servers), `mcp-cli <server>` (show tools), `mcp-cli <server>/<tool>` (get schema)
- Reduces token consumption for AI coding agents

**Sources**:
- [MCP Tools Specification](https://modelcontextprotocol.io/specification/2025-06-18/server/tools)
- [MCP GitHub Repository](https://github.com/modelcontextprotocol/modelcontextprotocol)
- [MCP Registry](https://github.com/modelcontextprotocol/registry)
- [mcp-cli by Phil Schmid](https://www.philschmid.de/mcp-cli)

---

#### 2. OpenAI Function Calling

**Overview**: Function calling provides a way for OpenAI models to interface with external systems using JSON Schema.

**Key Features**:
- `strict: true` mode ensures reliable schema adherence
- Tool definitions passed in `tools` parameter
- Supports complex nested schemas
- Function calls generated by model, executed by client

**Schema Structure**:
```json
{
  "type": "function",
  "function": {
    "name": "function_name",
    "description": "Description",
    "parameters": { /* JSON Schema */ },
    "strict": true
  }
}
```

**2025 Developments**:
- AGENTS.md specification pushed
- Agentic AI Foundation (AAIF) co-founded with Anthropic and Block
- Codex CLI supports AGENTS.md and MCP
- gpt-5.1-codex-max model for agentic coding

**AGENTS.md Adoption**:
- Adopted by 60,000+ open-source projects
- Supported by: Amp, Codex, Cursor, Devin, Factory, Gemini CLI, GitHub Copilot, Jules, VS Code

**Sources**:
- [OpenAI Function Calling Guide](https://platform.openai.com/docs/guides/function-calling)
- [OpenAI Agents SDK Tools](https://openai.github.io/openai-agents-python/tools/)
- [OpenAI for Developers 2025](https://developers.openai.com/blog/openai-for-developers-2025)

---

#### 3. Claude Tool Use (Anthropic)

**Overview**: Anthropic's Claude uses JSON Schema for tool definitions with recent structured output guarantees.

**Key Features**:
- Tools specified in `tools` parameter
- JSON Schema for parameter definitions
- `tool_use` and `tool_result` message types
- Tool Runner (beta) for automatic tool handling

**Structured Outputs** (November 2025):
- Public beta for Claude Sonnet 4.5 and Opus 4.1
- Guaranteed JSON Schema compliance
- `strict: true` for tool definitions
- Header: `anthropic-beta: structured-outputs-2025-11-13`

**Advanced Features**:
- Tool Search Tool: Access thousands of tools without context window consumption
- Programmatic Tool Calling: Invoke tools in code execution environment

**Schema Structure**:
```json
{
  "name": "tool_name",
  "description": "Description",
  "input_schema": {
    "type": "object",
    "properties": { /* JSON Schema */ },
    "required": ["param1", "param2"]
  }
}
```

**Sources**:
- [Claude Tool Use Documentation](https://docs.anthropic.com/en/docs/build-with-claude/tool-use)
- [Implement Tool Use Guide](https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use)
- [Advanced Tool Use Announcement](https://www.anthropic.com/engineering/advanced-tool-use)

---

#### 4. Agent Frameworks

| Framework | Tool Discovery | CLI Support | Notes |
|-----------|---------------|-------------|-------|
| **LangChain** | Graph-based tool nodes | Via subprocess | create_agent with LangGraph |
| **AutoGPT** | Dynamic tool invocation | File system tools | Autonomous decision-making |
| **CrewAI** | Agent tool assignment | Limited | Multi-agent orchestration |
| **OpenAI Agents SDK** | Function tools, hosted tools | Via MCP | Agents-as-tools support |
| **Deep Agents (LangChain)** | MCP via langchain-mcp-adapters | Filesystem backend | Pluggable backends |

**LangChain Tool Integration**:
- Tools give agents ability to take actions
- Multiple tool calls in sequence from single prompt
- State persistence across tool calls
- ReAct pattern: Reason -> Action -> Observation loop

**AutoGPT Characteristics**:
- Long-term memory
- Independent work without user input
- Dynamic tool invocation
- Known issues: task errors, infinite loops, high token consumption

**Sources**:
- [LangChain Agents Documentation](https://docs.langchain.com/oss/python/langchain/agents)
- [Deep Agents GitHub](https://github.com/langchain-ai/deepagents)
- [AutoGPT via LangChain](https://python.langchain.com/api_reference/experimental/autonomous_agents/langchain_experimental.autonomous_agents.autogpt.agent.AutoGPT.html)

---

### Convergence Analysis

#### Is There Convergence Toward a Standard CLI Description Format for AI?

**Finding**: **Partial convergence on JSON Schema, but no CLI-specific standard**

| Aspect | Convergence Level | Details |
|--------|-------------------|---------|
| Schema Format | **High** | All major players use JSON Schema |
| Tool Description | **High** | Name, description, parameters pattern universal |
| Discovery Protocol | **Medium** | MCP gaining traction, but not universal |
| CLI-Specific Features | **Low** | No standard for subcommands, stdin/stdout, exit codes |
| Agent Interoperability | **Growing** | AAIF, AGENTS.md, Skills showing promise |

**Key 2025 Developments**:
1. **Agentic AI Foundation (AAIF)**: Linux Foundation project with OpenAI, Anthropic, Block, Google, Microsoft, AWS
2. **AGENTS.md**: 60,000+ project adoption
3. **MCP Registry**: Centralized tool discovery infrastructure
4. **Skills Specification**: Anthropic's agent capability standard
5. **A2A + MCP Collaboration**: Working toward unified entity cards

**Remaining Gaps**:
- No standard for CLI-specific semantics (pipes, redirection, TTY)
- No standard for streaming output
- No standard for interactive CLI sessions
- Security/sandboxing not standardized

---

### How Does OpenCLI Position Itself for AI Consumption?

**Explicit AI/MCP Positioning**:

OpenCLI explicitly lists "Automate external tools such as MCP servers" as a primary use case.

**Alignment with AI Tool Schemas**:

| OpenCLI Feature | AI Tool Schema Equivalent |
|-----------------|---------------------------|
| Command name | Tool name |
| Description | Tool description |
| Arguments/Options | JSON Schema parameters |
| Examples | Few-shot prompting data |
| Return values | Output schema |

**Advantages for AI**:
1. **Structured Format**: JSON/YAML machine-readable
2. **Complete Metadata**: All invocation details in one place
3. **Version Information**: API change detection
4. **Examples**: Useful for LLM context

**Current Limitations**:
1. No MCP adapter/converter yet
2. No function calling bridge
3. Draft status limits adoption
4. Single framework support

---

### What's Missing for Reliable AI-CLI Interaction?

| Gap | Description | Impact |
|-----|-------------|--------|
| **Exit Code Semantics** | No standard mapping of exit codes to success/failure/error types | LLMs cannot reliably interpret results |
| **Output Parsing** | No standard for structured vs. unstructured output | Requires custom parsing per tool |
| **Interactive Mode** | No handling for prompts, confirmations, pagers | Cannot automate interactive CLIs |
| **Environment Context** | No standard for required env vars, working directory | Setup failures |
| **Streaming Output** | No standard for progress, logs, chunked output | Long-running commands problematic |
| **Error Messages** | No structured error format | Error handling is guesswork |
| **Side Effects** | No declaration of file system, network effects | Safety/sandboxing challenges |
| **Idempotency** | No indication if command is safe to retry | Recovery strategies unclear |
| **Authentication** | No standard for credential handling | Security model varies |
| **Composition** | No standard for piping, command chaining | Complex workflows difficult |

---

## Q6: Tooling Ecosystems

### Documentation Generators

| Tool | Language | Input | Output | Features |
|------|----------|-------|--------|----------|
| **Asciidoctor** | Ruby/Java | AsciiDoc | HTML, PDF, man pages | Industry standard for technical docs |
| **picocli gen-manpage** | Java | Annotations | AsciiDoc -> man pages | Localization, template support |
| **Usage CLI** | Rust | KDL | Markdown, man pages | Shell-specific completions |
| **Cobra** | Go | Code | Markdown, man pages | Built-in to framework |
| **Click** | Python | Decorators | Markdown | Via plugins |
| **Sphinx + autodoc** | Python | Docstrings | HTML, PDF | General-purpose |

**Strongest Community Support**: Asciidoctor (cross-language), Cobra (Go ecosystem)

---

### Completion Script Generators

| Tool/Framework | Bash | Zsh | Fish | PowerShell | Method |
|---------------|------|-----|------|------------|--------|
| **Cobra** | Yes | Yes | Yes | Yes | Code generation |
| **Click-Completion** | Yes | Yes | Yes | Yes | Jinja2 templates |
| **clap (Rust)** | Yes | Yes | Yes | Yes | Built-in |
| **.NET CLI** | Yes | Yes | Yes | Yes | Hybrid/Dynamic modes |
| **Usage CLI** | Yes | Yes | Yes | No | KDL-based |
| **oclif** | Yes | Yes | Yes | No | Auto-generated |
| **picocli** | Yes | Yes | No | No | Generated scripts |
| **argparse** | No | No | No | No | Manual only |

**Strongest Community Support**: Cobra (41.7k stars, 184k+ importers)

---

### SDK/Wrapper Generators

**Note**: CLI-specific SDK generators are rare. Most SDK generators target REST APIs.

| Tool | Target | Languages | CLI Focus |
|------|--------|-----------|-----------|
| **OpenAPI Generator** | REST APIs | 50+ client generators | No |
| **Fern** | REST APIs | 9 languages | No |
| **Kiota (Microsoft)** | REST APIs | 7 languages | No |
| **Swagger Codegen** | REST APIs | Multiple | No |
| **OpenCLI** | CLI tools | .NET (planned) | **Yes** (future) |

**Gap Identified**: No mature CLI-to-SDK generators exist. OpenCLI aims to fill this gap.

---

### Validators and Linters

| Tool | Target | Features |
|------|--------|----------|
| **ShellCheck** | Shell scripts | Static analysis, bug detection, style |
| **shfmt** | Shell scripts | Auto-formatting |
| **dockerlint** | Dockerfiles | Best practices |
| **MegaLinter** | Multiple | Aggregates 100+ linters |

**CLI-Specific Schema Validators**: None found for CLI specification formats

**Gap Identified**: No validators exist for OpenCLI, Usage Spec, or docopt schemas.

---

### IDE Integrations

| IDE | CLI Support | Type |
|-----|------------|------|
| **VSCode** | ShellCheck integration | Linting |
| **VSCode** | Shell completions | Via extensions |
| **IntelliJ** | Command completion | Built-in for specific tools |
| **Continue.dev** | AI autocomplete | General coding |

**CLI Specification IDE Support**: None found

**Gap Identified**: No IDE plugins for editing/validating CLI specifications.

---

### Framework Comparison Matrix

| Framework | Stars | Lang | Docs | Completions | Man Pages | Schema Export |
|-----------|-------|------|------|-------------|-----------|---------------|
| **Cobra** | 41.7k | Go | Yes | All 4 shells | Yes | No |
| **Spectre.Console** | 11k | .NET | Yes | Via OpenCLI | Via OpenCLI | **OpenCLI** |
| **clap** | 14k+ | Rust | Yes | All 4 shells | Yes | No |
| **Click** | 15k+ | Python | Via plugins | Via plugin | No | No |
| **argparse** | stdlib | Python | Partial | No | No | No |
| **picocli** | 4.8k | Java | Yes | Bash/Zsh | Yes | No |
| **oclif** | 9k+ | Node | Yes | 3 shells | No | No |

---

## Key Findings & Conclusions

### 1. Ecosystem Maturity Summary

| Specification | Maturity | Active Development | Real-World Usage |
|--------------|----------|-------------------|------------------|
| **OpenCLI** | Early (Draft) | Yes | Limited to Spectre.Console |
| **Usage Spec** | Mature | Yes | mise ecosystem |
| **docopt** | Legacy | No (forks only) | Declining |
| **ONAP OCS** | Mature | Minimal | Telecom niche |

### 2. AI Integration Readiness

| Approach | MCP Compatible | Function Calling | Agent Framework |
|----------|---------------|------------------|-----------------|
| **OpenCLI** | Designed for it | Needs adapter | Needs adapter |
| **JSON Schema** | Native | Native | Native |
| **Usage Spec** | Not designed | Not designed | Not designed |
| **docopt** | No | No | No |

### 3. Critical Gaps Identified

1. **No Universal CLI Specification**: Unlike OpenAPI for REST, no single standard dominates
2. **No CLI-to-SDK Generators**: Major tooling gap compared to API ecosystem
3. **No CLI Schema Validators**: Quality assurance tools missing
4. **Limited AI Bridges**: OpenCLI mentions MCP but no implementation exists
5. **IDE Support Absent**: No specification editing/validation tools

### 4. Recommendations for CLI-to-SDK System

Based on this research:

1. **Align with JSON Schema**: All AI systems use it; maximize compatibility
2. **Consider OpenCLI Format**: Best positioned for AI use cases
3. **Build MCP Adapter**: Enable AI discovery of CLI tools
4. **Create Validators**: Fill tooling gap
5. **Support Multiple Outputs**: Completions, docs, SDKs from single source
6. **Document CLI Semantics**: Exit codes, streaming, interactivity

### 5. Market Opportunity

The convergence of:
- AI agents needing tool discovery (MCP, function calling)
- CLI tools needing structured descriptions (OpenCLI)
- Developers wanting generated SDKs (no tools exist)

Creates a significant opportunity for a comprehensive CLI-to-SDK system that bridges these gaps.

---

## Sources Summary

### Specifications
- [OpenCLI Specification](https://opencli.org/)
- [Usage Specification](https://usage.jdx.dev/spec/)
- [docopt](http://docopt.org/)
- [ONAP OCS](https://docs.onap.org/projects/onap-cli/en/latest/open_cli_schema_version_1_0.html)

### AI/LLM Tools
- [MCP Specification](https://modelcontextprotocol.io/specification/2025-06-18/server/tools)
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)
- [Claude Tool Use](https://docs.anthropic.com/en/docs/build-with-claude/tool-use)
- [LangChain Agents](https://docs.langchain.com/oss/python/langchain/agents)

### CLI Frameworks
- [Cobra](https://github.com/spf13/cobra)
- [Spectre.Console](https://github.com/spectreconsole/spectre.console)
- [clap](https://github.com/clap-rs/clap)
- [picocli](https://picocli.info/)
- [oclif](https://github.com/oclif/oclif)

### Industry Developments
- [OpenAI for Developers 2025](https://developers.openai.com/blog/openai-for-developers-2025)
- [Agentic AI Foundation](https://openai.com/index/agentic-ai-foundation/)
- [Anthropic Agent Skills](https://www.unite.ai/anthropic-opens-agent-skills-standard-continuing-its-pattern-of-building-industry-infrastructure/)

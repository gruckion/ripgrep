# Research: Existing CLI Standards & Specifications

**Research Date**: January 2026
**Context**: Comparing CLI specification formats for potential CIDL (CLI Interface Definition Language) development

---

## Executive Summary

This document analyzes four major CLI specification formats:
1. **OpenCLI (spectreconsole/open-cli)** - JSON/YAML specification inspired by OpenAPI
2. **Usage Spec (jdx/usage)** - KDL-based specification for CLI definition
3. **docopt** - Grammar-based help text parser
4. **ONAP Open CLI Schema (OCS)** - Enterprise YAML schema for REST API command generation

We discovered that **OpenCLI already exists** as a specification created by Patrik Svensson (Spectre.Console creator) in July 2025. This significantly impacts our naming considerations for any new CLI specification format.

---

## Q1: OpenCLI (spectreconsole/open-cli) Technical Specification

### Overview

OpenCLI defines "a standard, platform and language-agnostic interface to CLI applications which allows both humans and computers to understand how a CLI tool should be invoked without access to source code or documentation."

- **Website**: https://opencli.org/
- **GitHub**: https://github.com/spectreconsole/open-cli
- **Status**: Draft specification (as of July 2025)
- **Creator**: Patrik Svensson (Spectre.Console)

### Schema Structure and JSON Format

#### Document Structure
```json
{
  "$schema": "https://opencli.org/draft.json",
  "opencli": "0.1",
  "info": {
    "title": "Application Name",
    "version": "1.0.0",
    "description": "Application description",
    "license": "MIT"
  },
  "options": [...],
  "commands": [...]
}
```

#### Key Schema Elements

| Element | Description |
|---------|-------------|
| `opencli` | Specification version (e.g., "0.1") |
| `info` | Metadata: title, version, description, license, binary name |
| `options` | Global options with names, aliases, descriptions |
| `commands` | Hierarchical command definitions |
| `arguments` | Positional parameters with types and requirements |

#### TypeSpec Definition

OpenCLI uses **TypeSpec** (Microsoft's API definition language) for its core specification:
- Repository contains TypeSpec definitions in `/typespec` directory
- JSON Schema generated from TypeSpec for validation
- Build uses .NET 9.0 SDK and Cake build automation

### Versioning Approach

Following OpenAPI conventions:
- **major.minor.patch** versioning scheme
- major.minor designates the feature set
- patch versions address errors/clarifications only
- Tooling should not distinguish between patch versions (e.g., 3.1.0 vs 3.1.1)

### Feature Set

| Feature | Support Level | Notes |
|---------|---------------|-------|
| Commands | Full | Hierarchical with `group: true` for parents |
| Subcommands | Full | Nested command definitions |
| Options/Flags | Full | Short/long forms, aliases |
| Arguments | Full | Positional with types and requirements |
| Data Types | Partial | string, likely others (schema in progress) |
| Exit Codes | Not Yet | Feature request exists (#1724) |
| Output Schemas | Not Yet | Not in current draft |
| Streaming | Not Yet | Not addressed |
| Environment Variables | Not Yet | Not in current specification |
| Config File Integration | Not Yet | Not addressed |

### Comparison to Envisioned CIDL

| Aspect | OpenCLI | Our CIDL Vision |
|--------|---------|-----------------|
| Exit Codes | Not specified | Explicit semantic exit code definitions |
| Output Schemas | Not specified | JSON Schema for stdout/stderr |
| Streaming | Not addressed | Explicit streaming indicators |
| Stdin/Stdout Types | Not specified | Full type annotations |
| MCP Integration | Mentioned goal | Primary use case |
| Shell Completions | Via tooling | Generated from spec |

### Design Philosophy Differences

**OpenCLI Philosophy**:
- Heavily influenced by OpenAPI specification
- Focus on human-readable documentation
- Client code generation for CLI tool interaction
- External tool automation (including MCP servers)
- Platform and language agnostic

**Our CIDL Vision**:
- SDK generation as primary goal
- Runtime type safety
- Programmatic CLI invocation
- Structured output parsing
- Exit code semantics

---

## Q2: Advanced Features Comparison

### 2.1 OpenCLI (spectreconsole)

#### Subcommand Hierarchies
```yaml
commands:
  - name: "build"
    group: true
    commands:
      - name: "debug"
        arguments:
          - name: "PROJECT"
            summary: "Project to build"
```

#### Mutually Exclusive Options
- **Not explicitly supported** in current draft
- May be handled through validation tooling

#### Environment Variable Binding
- **Not currently specified**

#### Config File Integration
- **Not addressed** in specification

#### Stdin/Stdout Typing
- **Not specified** - major gap vs CIDL vision

#### Shell-Specific Completions
- Generated via tooling (Spectre.Console.Cli)
- `--help-dump-opencli` dumps spec to stdout

### 2.2 Usage Spec (jdx/mise)

**Website**: https://usage.jdx.dev/spec/
**GitHub**: https://github.com/jdx/usage
**Format**: KDL (KDL Document Language)

#### KDL Syntax Example
```kdl
name "mycli"
bin "mycli"
version "1.0.0"

flag "-v --verbose" global=#true count=#true help="Increase verbosity"

cmd "build" help="Build the project" {
    alias "b"
    flag "-r --release" help="Build in release mode"
    arg "<TARGET>" help="Build target" required=#true

    cmd "clean" help="Clean build artifacts" {
        flag "--all" help="Clean everything"
    }
}
```

#### Subcommand Hierarchies
```kdl
cmd "parent" help="Parent command" {
    cmd "child" help="Child command" {
        cmd "grandchild" help="Deeply nested"
    }
}
```

#### Mutually Exclusive Options
- **Not directly supported** in spec
- Must be handled in implementation

#### Environment Variable Binding
```kdl
flag "--user" env="MYCLI_USER" help="Username" {
    arg "<USER>"
}
```

#### Config File Integration
```kdl
flag "--config" config="settings.path" default="~/.config/mycli" {
    arg "<PATH>"
}
```

#### Stdin/Stdout Typing
- **Not explicitly typed**
- Handled at implementation level

#### Shell-Specific Completions
```kdl
arg "[SHELL]" help="Shell type" choices=["bash", "fish", "zsh", "elvish", "nu", "xonsh", "pwsh"]
```

Completions generated via:
```bash
usage generate completion bash --spec-file mycli.usage.kdl
```

**Supported shells**: bash, fish, zsh, elvish, nu, xonsh, pwsh

#### Dynamic Completions
```kdl
complete "run" run="mycli --list-targets"
```

### 2.3 docopt

**Website**: http://docopt.org/
**Format**: Help text DSL (Domain-Specific Language)

#### Syntax Example
```
Naval Fate.

Usage:
  naval_fate ship new <name>...
  naval_fate ship <name> move <x> <y> [--speed=<kn>]
  naval_fate mine (set|remove) <x> <y> [--moored | --drifting]
  naval_fate (-h | --help)
  naval_fate --version

Options:
  -h --help     Show this screen.
  --version     Show version.
  --speed=<kn>  Speed in knots [default: 10].
  --moored      Moored (anchored) mine.
  --drifting    Drifting mine.
```

#### Subcommand Hierarchies
- Via `options_first=True` parameter
- Multi-level help requires separate docstrings
- Limited compared to structured specs

#### Mutually Exclusive Options
```
Usage: prog (--left | --right)           # Required, one of
Usage: prog [--left | --right]           # Optional, one of
Usage: prog [--format=json | --format=csv]
```

**Syntax elements**:
- `|` (pipe) - mutually exclusive
- `( )` - grouping, required
- `[ ]` - optional
- `...` - repeating

#### Environment Variable Binding
- **Not supported natively**
- Must be handled in implementation code

#### Config File Integration
- **Not supported**

#### Stdin/Stdout Typing
- Special handling for `-` (stdin convention)
- No explicit typing

#### Shell-Specific Completions
- **Not generated from spec**
- Must be created separately

### 2.4 ONAP Open CLI Schema (OCS)

**Documentation**: https://docs.onap.org/projects/onap-cli/en/latest/open_cli_schema_version_1_0.html
**Format**: YAML
**Focus**: Enterprise CLI for REST API interaction

#### YAML Schema Example
```yaml
open_cli_schema_version: 1.0
name: service-list
description: List all services
product: onap-dublin

parameters:
  - name: service-name
    type: string
    description: Filter by service name
    is_optional: true
    default_value: ""

  - name: output-format
    type: string
    description: Output format
    is_optional: true
    default_value: "table"

results:
  direction: landscape
  attributes:
    - name: service-id
      description: Service identifier
      type: string
      scope: short
    - name: status
      description: Service status
      type: string

http:
  service:
    name: sdc
    version: v1
  request:
    uri: /services
    method: GET
  success_codes:
    - 200
  result_map:
    service-id: $b{$.services[*].id}
    status: $b{$.services[*].status}
```

#### Subcommand Hierarchies
- Flat command structure (no nesting)
- Commands organized by product/feature

#### Mutually Exclusive Options
- **Not directly supported**
- Handled through validation logic

#### Environment Variable Binding
```yaml
# Set via environment
OPEN_CLI_PRODUCT_IN_USE=onap-dublin
```

- Parameters can reference environment variables
- `OPEN_CLI_` prefix for platform variables

#### Config File Integration
- Profile system for saved configurations
- `profile <name>` command for switching
- JSON/YAML parameter files for batching

#### Stdin/Stdout Typing
- **Not typed**
- Output direction: `landscape` (table) or `portrait` (key-value)

#### Shell-Specific Completions
- **Not generated from schema**

---

## Q3: Formal Grammars & Schema Validation Mechanisms

### 3.1 JSON Schema Usage

| Specification | JSON Schema | Notes |
|---------------|-------------|-------|
| OpenCLI | Yes | Generated from TypeSpec definitions |
| Usage Spec | No | Uses KDL format |
| docopt | No | Grammar-based parser |
| ONAP OCS | Partial | YAML with implicit schema |

### 3.2 Custom DSLs

#### docopt Grammar (EBNF-like)

```ebnf
Docopt      = [ Prologue ] , Usage , [ Free_text ] , [ Options ] , [ Free_text ] ;
Usage       = "Usage:" , pattern+ ;
pattern     = element+ ;
element     = command | argument | option | group ;
command     = word ;
argument    = "<" word ">" | UPPER_WORD ;
option      = short_option | long_option ;
group       = "(" elements ")" | "[" elements "]" ;
elements    = element ( "|" element )* ;
```

**Key patterns**:
- `<argument>` or `ARGUMENT` - positional arguments
- `--option` or `-o` - options
- `( a | b )` - required, mutually exclusive
- `[ a | b ]` - optional, mutually exclusive
- `...` - repeating

#### KDL Format (Usage Spec)

KDL 2.0.0 specification (released 2024-12-21):

```kdl
// Nodes with properties and children
node_name "argument" property=#value {
    child_node "value"
}

// Type annotations
flag "-v" (bool)=#true

// Raw strings
description #"Contains "quotes" safely"#
```

**KDL Key Features**:
- XML-like hierarchy
- JSON-like values
- TypeScript-inspired syntax
- `#true`, `#false`, `#null` keywords (v2.0)
- Multi-line strings with `"""`

### 3.3 Extensibility Support

| Specification | Extensibility | Mechanism |
|---------------|---------------|-----------|
| OpenCLI | High | TypeSpec decorators, custom emitters |
| Usage Spec | Medium | KDL properties, custom generators |
| docopt | Low | Fixed grammar, limited extension |
| ONAP OCS | Medium | Custom macros, HTTP templates |

### 3.4 Versioning and Backward Compatibility

#### OpenCLI Versioning
```json
{
  "opencli": "0.1"
}
```
- Semantic versioning (major.minor.patch)
- Patch versions for clarifications only
- Influenced by OpenAPI approach

#### KDL Versioning
```kdl
/- kdl-version 2
```
- Optional version marker
- v1.0 and v2.0 are unambiguous
- Forward/backward compatible migration

#### ONAP OCS Versioning
```yaml
open_cli_schema_version: 1.0
```
- Version in first line
- Major version increments for breaking changes

### 3.5 Lessons from POSIX

**POSIX Utility Conventions** (IEEE Std 1003.1-2024):

| Convention | Description |
|------------|-------------|
| Option format | Single dash + letter (`-o`) |
| Long options | GNU extension (`--option`) |
| Option grouping | `-abc` equivalent to `-a -b -c` |
| Option terminator | `--` ends option parsing |
| Stdin convention | `-` means stdin |
| Exit codes | 0 = success, 1-255 = failure |
| Name length | 2-9 characters recommended |

**Key lessons**:
- Consistency matters more than features
- Backwards compatibility is paramount
- Some historical decisions cannot be changed
- Standards evolve slowly but deliberately

### 3.6 Lessons from OpenAPI Evolution

| Version | Year | Key Changes |
|---------|------|-------------|
| 2.0 | 2014 | Swagger donation to OAI |
| 3.0 | 2017 | Components, better security |
| 3.1 | 2021 | JSON Schema alignment |

**Key lessons for CLI specs**:
- Start with clear versioning strategy
- Align with existing standards (JSON Schema)
- Build tooling ecosystem early
- Community governance matters
- Backward compatibility is essential
- Minor versions can include non-breaking changes

---

## Comparison Tables

### Feature Matrix

| Feature | OpenCLI | Usage Spec | docopt | ONAP OCS |
|---------|---------|------------|--------|----------|
| **Format** | JSON/YAML | KDL | Help text | YAML |
| **Subcommands** | Hierarchical | Hierarchical | Limited | Flat |
| **Mutually Exclusive** | No | No | Yes | No |
| **Env Var Binding** | No | Yes | No | Yes |
| **Config Integration** | No | Yes | No | Yes |
| **Stdin Typing** | No | No | Convention | No |
| **Stdout Typing** | No | No | No | Direction |
| **Exit Codes** | No | No | No | Implicit |
| **Shell Completions** | Tooling | Generated | No | No |
| **JSON Schema** | Yes | No | No | Partial |
| **MCP Ready** | Goal | No | No | No |

### Schema Validation

| Specification | Validation Method | Tools |
|---------------|-------------------|-------|
| OpenCLI | JSON Schema | TypeSpec compiler |
| Usage Spec | KDL parser | usage CLI |
| docopt | Grammar parser | Language-specific |
| ONAP OCS | YAML schema | oclip schema-validate |

### Tooling Ecosystem

| Specification | Documentation | Code Gen | Completions |
|---------------|---------------|----------|-------------|
| OpenCLI | Yes | Planned | Yes (Spectre) |
| Usage Spec | Yes | Yes | Yes (multi-shell) |
| docopt | Help text | Parser only | No |
| ONAP OCS | Yes | REST wrappers | No |

---

## Gaps Analysis for CIDL

Based on this research, a comprehensive CIDL should address:

### Critical Gaps in Existing Specs

1. **Exit Code Semantics**
   - None of the specs formally define exit codes
   - Should include: code, meaning, conditions

2. **Output Schema Typing**
   - Only ONAP has output structure (limited)
   - Need: JSON Schema for stdout, structured error schemas

3. **Streaming Indicators**
   - Not addressed by any specification
   - Need: streaming mode, chunking, progress indicators

4. **Stdin/Stdout Type Contracts**
   - docopt has convention only
   - Need: explicit input/output type annotations

5. **MCP Integration**
   - OpenCLI mentions as goal
   - Need: explicit tool metadata for LLM consumption

6. **Mutual Exclusivity Groups**
   - Only docopt handles this well
   - Need: option groups, conflicts, dependencies

### Recommended CIDL Features

```yaml
# Proposed CIDL structure
cidl: "1.0"
info:
  name: "mytool"
  version: "1.0.0"

commands:
  build:
    description: "Build the project"
    arguments:
      - name: target
        type: string
        required: true
    options:
      - name: release
        short: r
        type: boolean
        conflicts: [debug]
      - name: debug
        short: d
        type: boolean
        conflicts: [release]
    stdin:
      accepts: true
      type: "application/json"
      schema: { $ref: "#/components/schemas/BuildConfig" }
    stdout:
      type: "application/json"
      schema: { $ref: "#/components/schemas/BuildResult" }
      streaming: progressive
    exit_codes:
      0: "Build succeeded"
      1: "Build failed - compilation error"
      2: "Build failed - missing dependencies"
    env:
      BUILD_TARGET: target
      BUILD_RELEASE: release
```

---

## Sources

### OpenCLI
- [Patrik Svensson - Introducing OpenCLI](https://patriksvensson.se/posts/2025/07/introducing-open-cli)
- [OpenCLI Specification](https://opencli.org/)
- [GitHub - spectreconsole/open-cli](https://github.com/spectreconsole/open-cli)
- [GitHub - bcdxn/opencli](https://github.com/bcdxn/opencli)

### Usage Spec
- [Usage Specification](https://usage.jdx.dev/spec/)
- [GitHub - jdx/usage](https://github.com/jdx/usage)
- [mise.usage.kdl example](https://github.com/jdx/mise/blob/main/mise.usage.kdl)

### KDL
- [KDL Document Language](https://kdl.dev/)
- [KDL v2.0 Specification](https://github.com/kdl-org/kdl/blob/main/SPEC.md)

### docopt
- [docopt - Command Line Interface Description Language](http://docopt.org/)
- [docopt GitHub](https://github.com/docopt/docopt)
- [docopts EBNF Grammar](https://github.com/docopt/docopts/wiki)

### ONAP OCS
- [ONAP CLI Schema Version 1.0](https://docs.onap.org/projects/onap-cli/en/latest/open_cli_schema_version_1_0.html)
- [CLI Developer Guide](https://docs.onap.org/projects/onap-cli/en/latest/developer_guide.html)

### TypeSpec
- [TypeSpec Official](https://typespec.io/)
- [GitHub - microsoft/typespec](https://github.com/microsoft/typespec)

### Standards
- [POSIX Utility Conventions](https://pubs.opengroup.org/onlinepubs/9699919799/basedefs/V1_chap12.html)
- [GNU Coding Standards - CLI](https://www.gnu.org/prep/standards/html_node/Command_002dLine-Interfaces.html)
- [Command Line Interface Guidelines](https://clig.dev/)
- [OpenAPI Specification](https://spec.openapis.org/oas/v3.2.0.html)
- [JSON Schema Specification](https://json-schema.org/specification)

### Exit Codes
- [Exit Codes With Special Meanings](https://tldp.org/LDP/abs/html/exitcodes.html)
- [Standard Exit Status Codes in Linux](https://www.baeldung.com/linux/status-codes)

---

## Conclusions

1. **OpenCLI exists and is actively developed** - We should not use "OpenCLI" as a name for any new specification.

2. **No existing spec fully covers our CIDL vision** - Gaps exist in exit codes, output schemas, streaming, and MCP integration.

3. **KDL is a compelling format** - More expressive than JSON/YAML for CLI definitions.

4. **TypeSpec approach is interesting** - Generating schemas from a higher-level language.

5. **Tooling matters as much as spec** - Usage Spec's success comes from practical tooling.

6. **Community adoption requires ecosystem** - OpenAPI succeeded due to tooling, not just specification.

**Recommendation**: Consider contributing to OpenCLI or creating a complementary specification focused specifically on SDK generation and programmatic CLI interaction, avoiding naming conflicts.

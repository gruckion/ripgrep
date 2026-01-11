# PRD-002: CIDL (CLI Interface Definition Language) Specification

## Product Requirements Document

**Version**: 1.0
**Date**: 2025-01-11
**Author**: Research Phase
**Status**: Research Complete, Specification Draft Ready
**Parent**: PRD-001 CLI→SDK System

---

## 1. Executive Summary

### 1.1 Purpose

CIDL (CLI Interface Definition Language) is a structured specification format for describing command-line interfaces. It serves the same role for CLIs that OpenAPI serves for REST APIs—a machine-readable contract enabling tooling generation.

### 1.2 Analogy Map

| REST API Ecosystem | CLI Ecosystem (Proposed) |
|--------------------|-------------------------|
| OpenAPI Specification | **CIDL Specification** |
| Swagger UI | CIDL Viewer/Explorer |
| Swagger Codegen | SDK Generator |
| Stoplight, Redocly | CIDL Editor |
| APIs.guru | **CIDL Registry** |
| Postman Collections | CLI invocation examples |

### 1.3 Why Not Use Existing Formats?

| Format | Why Not Sufficient |
|--------|-------------------|
| **Shell completions** | Shell-specific, no output schema, no exit codes |
| **Man pages (roff)** | Prose-based, not machine-readable |
| **--help output** | Unstructured text, inconsistent formats |
| **JSON Schema** | Data-focused, not CLI-focused |
| **OpenAPI** | HTTP-specific concepts (paths, methods) |
| **complgen .usage** | Completion-focused, missing SDK requirements |

---

## 2. Research Findings

### 2.1 Information Required for SDK Generation

Based on our ripgrep analysis, a complete CLI definition requires:

#### 2.1.1 Fully Available from --help + Autocomplete

| Information | Example | Extraction |
|-------------|---------|------------|
| Option long name | `--ignore-case` | Easy |
| Option short name | `-i` | Easy |
| Option description | "Search case-insensitively" | Easy |
| Enum choices | `--color=never\|auto\|always` | Easy |
| Is switch (boolean) | `--hidden` takes no value | Medium |
| Categories | "SEARCH OPTIONS" | Easy |
| Positional args | `PATTERN`, `PATH...` | Easy |

#### 2.1.2 Partially Available (Requires NLP/Heuristics)

| Information | Example | Extraction |
|-------------|---------|------------|
| Negation form | `--no-ignore-case` | Medium |
| Override rules | "overrides --ignore-case" | Hard (NLP) |
| Default values | "default: auto" | Medium |
| Type hints | "NUM", "PATH" | Medium |
| Deprecation | "(DEPRECATED)" | Easy |

#### 2.1.3 Requires Codebase Analysis

| Information | Example | Impact |
|-------------|---------|--------|
| **Exit codes** | 0=match, 1=no match, 2=error | 🔴 BLOCKER |
| **Output schema** | JSON message format | 🔴 BLOCKER |
| Type bounds | threads: 1..num_cpus*2 | 🟡 HIGH |
| Environment vars | RIPGREP_CONFIG_PATH | 🟡 MEDIUM |
| Config file format | .ripgreprc syntax | 🟡 LOW |

### 2.2 Existing Completion Formats Analysis

#### 2.2.1 Zsh Completion Format

```zsh
# Most structured, but complex DSL
_arguments \
  '(-i --ignore-case)'{-i,--ignore-case}'[search case-insensitively]' \
  '--color=[when to use color]:when:(never auto always ansi)' \
  '*:file:_files'
```

**Extractable**: names, descriptions, choices, file types, mutual exclusivity
**Missing**: exit codes, output schema, defaults

#### 2.2.2 Bash Completion Format

```bash
# Less structured
opts="--ignore-case -i --color --help"
COMPREPLY=($(compgen -W "${opts}" -- "${cur}"))
case "${prev}" in
  --color) COMPREPLY=($(compgen -W "never auto always" -- "${cur}")) ;;
esac
```

**Extractable**: names, enum choices
**Missing**: descriptions, types, everything else

#### 2.2.3 Fish Completion Format

```fish
# Simple but informative
complete -c rg -s i -l ignore-case -d 'Search case-insensitively'
complete -c rg -l color -r -f -a 'never auto always'
```

**Extractable**: names, descriptions, choices, requires-value flag
**Missing**: mutual exclusivity, exit codes, output schema

#### 2.2.4 ripgrep Internal Flag Trait

```rust
// Most complete - this is what CIDL should capture
trait Flag {
    fn is_switch(&self) -> bool;
    fn name_short(&self) -> Option<u8>;
    fn name_long(&self) -> &'static str;
    fn name_negated(&self) -> Option<&'static str>;
    fn aliases(&self) -> &'static [&'static str];
    fn doc_short(&self) -> &'static str;
    fn doc_long(&self) -> &'static str;
    fn doc_choices(&self) -> &'static [&'static str];
    fn doc_category(&self) -> Category;
    fn completion_type(&self) -> CompletionType; // File, Executable, Filetype, Encoding
    fn update(&self, v: FlagValue, args: &mut LowArgs) -> anyhow::Result<()>;
}
```

**This is essentially CIDL**—we're formalizing what good CLIs already have internally.

---

## 3. CIDL Specification

### 3.1 Design Principles

1. **Complete**: Capture everything needed for SDK generation
2. **Extractable**: Fields should be derivable from available sources
3. **Extensible**: Allow custom fields for tool-specific features
4. **Versionable**: Support tracking changes over time
5. **Language-agnostic**: JSON/YAML, no language-specific constructs

### 3.2 Schema Overview

```yaml
cidl: "1.0"
meta:
  name: string           # CLI binary name
  version: string        # CLI version
  description: string    # One-line description
  homepage: url          # Project URL
  license: string        # SPDX identifier

commands:
  - name: string         # Command/subcommand name
    description: string
    options: [Option]
    positional: [Positional]

options:
  - name: string         # Long name without --
    short: char?         # Short name without -
    negated: string?     # Negation form without --
    aliases: [string]    # Alternative names
    type: OptionType     # switch | string | integer | float | path | enum | ...
    choices: [string]?   # For enum types
    default: any?        # Default value
    required: bool       # Is this option required?
    multiple: bool       # Can be specified multiple times?
    description: string  # Short description
    long_description: string?  # Extended documentation
    category: string?    # Grouping category
    deprecated: bool     # Is deprecated?
    overrides: [string]? # Options this overrides
    completion_type: CompletionType?  # file | directory | executable | ...

exit_codes:
  - code: integer
    name: string         # Symbolic name
    description: string

output:
  formats: [OutputFormat]
  default_format: string

schemas:
  json:
    messages: [MessageSchema]  # For streaming JSON (like ripgrep --json)
  # or standard JSON Schema for single-response tools

environment:
  - name: string
    description: string
    affects: [string]    # Which options/behaviors
```

### 3.3 Full JSON Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://cidl.dev/schema/v1",
  "title": "CIDL - CLI Interface Definition Language",
  "type": "object",
  "required": ["cidl", "meta", "commands"],
  "properties": {
    "cidl": {
      "type": "string",
      "pattern": "^[0-9]+\\.[0-9]+$",
      "description": "CIDL specification version"
    },
    "meta": {
      "type": "object",
      "required": ["name", "version"],
      "properties": {
        "name": { "type": "string", "pattern": "^[a-z0-9_-]+$" },
        "version": { "type": "string" },
        "description": { "type": "string" },
        "homepage": { "type": "string", "format": "uri" },
        "repository": { "type": "string", "format": "uri" },
        "license": { "type": "string" },
        "authors": { "type": "array", "items": { "type": "string" } },
        "extracted_from": {
          "type": "object",
          "properties": {
            "sources": { "type": "array", "items": { "type": "string" } },
            "extracted_at": { "type": "string", "format": "date-time" },
            "extractor_version": { "type": "string" }
          }
        }
      }
    },
    "commands": {
      "type": "array",
      "items": { "$ref": "#/$defs/Command" }
    },
    "exit_codes": {
      "type": "array",
      "items": { "$ref": "#/$defs/ExitCode" }
    },
    "output": { "$ref": "#/$defs/OutputSpec" },
    "environment": {
      "type": "array",
      "items": { "$ref": "#/$defs/EnvironmentVar" }
    },
    "config": { "$ref": "#/$defs/ConfigSpec" }
  },
  "$defs": {
    "Command": {
      "type": "object",
      "required": ["name"],
      "properties": {
        "name": { "type": "string" },
        "description": { "type": "string" },
        "long_description": { "type": "string" },
        "options": { "type": "array", "items": { "$ref": "#/$defs/Option" } },
        "positional": { "type": "array", "items": { "$ref": "#/$defs/Positional" } },
        "subcommands": { "type": "array", "items": { "$ref": "#/$defs/Command" } }
      }
    },
    "Option": {
      "type": "object",
      "required": ["name", "type"],
      "properties": {
        "name": { "type": "string", "pattern": "^[a-z0-9][a-z0-9-]*$" },
        "short": { "type": "string", "pattern": "^[a-zA-Z0-9.]$" },
        "negated": { "type": "string" },
        "aliases": { "type": "array", "items": { "type": "string" } },
        "type": { "$ref": "#/$defs/OptionType" },
        "choices": { "type": "array", "items": { "type": "string" } },
        "default": {},
        "required": { "type": "boolean", "default": false },
        "multiple": { "type": "boolean", "default": false },
        "description": { "type": "string" },
        "long_description": { "type": "string" },
        "category": { "type": "string" },
        "deprecated": { "type": "boolean", "default": false },
        "deprecation_message": { "type": "string" },
        "overrides": { "type": "array", "items": { "type": "string" } },
        "requires": { "type": "array", "items": { "type": "string" } },
        "conflicts": { "type": "array", "items": { "type": "string" } },
        "completion_type": { "$ref": "#/$defs/CompletionType" },
        "value_name": { "type": "string" },
        "examples": { "type": "array", "items": { "type": "string" } }
      }
    },
    "OptionType": {
      "oneOf": [
        { "const": "switch" },
        { "const": "string" },
        { "const": "integer" },
        { "const": "float" },
        { "const": "path" },
        { "const": "enum" },
        { "const": "regex" },
        { "const": "glob" },
        {
          "type": "object",
          "properties": {
            "base": { "type": "string" },
            "suffix": { "type": "array", "items": { "type": "string" } }
          }
        }
      ]
    },
    "CompletionType": {
      "enum": ["file", "directory", "executable", "hostname", "username", "pid", "signal", "custom"]
    },
    "Positional": {
      "type": "object",
      "required": ["name"],
      "properties": {
        "name": { "type": "string" },
        "description": { "type": "string" },
        "required": { "type": "boolean", "default": true },
        "multiple": { "type": "boolean", "default": false },
        "type": { "$ref": "#/$defs/OptionType" },
        "completion_type": { "$ref": "#/$defs/CompletionType" }
      }
    },
    "ExitCode": {
      "type": "object",
      "required": ["code", "name"],
      "properties": {
        "code": { "type": "integer", "minimum": 0, "maximum": 255 },
        "name": { "type": "string" },
        "description": { "type": "string" }
      }
    },
    "OutputSpec": {
      "type": "object",
      "properties": {
        "formats": { "type": "array", "items": { "type": "string" } },
        "default_format": { "type": "string" },
        "streaming": { "type": "boolean", "default": false },
        "schemas": {
          "type": "object",
          "additionalProperties": { "$ref": "#/$defs/OutputSchema" }
        }
      }
    },
    "OutputSchema": {
      "type": "object",
      "description": "JSON Schema or message type definitions for output parsing"
    },
    "EnvironmentVar": {
      "type": "object",
      "required": ["name"],
      "properties": {
        "name": { "type": "string" },
        "description": { "type": "string" },
        "affects": { "type": "array", "items": { "type": "string" } },
        "default": { "type": "string" }
      }
    },
    "ConfigSpec": {
      "type": "object",
      "properties": {
        "file_patterns": { "type": "array", "items": { "type": "string" } },
        "format": { "type": "string" },
        "schema": {}
      }
    }
  }
}
```

### 3.4 Example: ripgrep CIDL

```yaml
cidl: "1.0"

meta:
  name: rg
  version: "14.1.1"
  description: "ripgrep recursively searches directories for a regex pattern"
  homepage: "https://github.com/BurntSushi/ripgrep"
  repository: "https://github.com/BurntSushi/ripgrep"
  license: "MIT OR Unlicense"
  authors:
    - "Andrew Gallant <jamslam@gmail.com>"
  extracted_from:
    sources:
      - "rg --generate complete-zsh"
      - "rg --help"
      - "source:crates/core/flags/defs.rs"
    extracted_at: "2025-01-11T00:00:00Z"

commands:
  - name: rg
    description: "Search for PATTERN in PATH"

    positional:
      - name: PATTERN
        description: "A regular expression used for searching"
        required: false  # Not required if -e or -f used
        type: regex

      - name: PATH
        description: "Files or directories to search"
        required: false
        multiple: true
        type: path
        completion_type: file

    options:
      # Input Options
      - name: regexp
        short: e
        type: string
        multiple: true
        description: "A pattern to search for"
        long_description: |
          This option can be provided multiple times, where all patterns
          given are searched. Lines matching at least one pattern are printed.
        category: "Input"
        value_name: PATTERN

      - name: file
        short: f
        type: path
        multiple: true
        description: "Search for patterns from the given file"
        category: "Input"
        completion_type: file
        value_name: PATTERNFILE

      # Search Options
      - name: ignore-case
        short: i
        type: switch
        description: "Search case-insensitively"
        category: "Search"
        conflicts:
          - case-sensitive
          - smart-case

      - name: case-sensitive
        short: s
        type: switch
        description: "Search case sensitively (default)"
        category: "Search"
        overrides:
          - ignore-case
          - smart-case

      - name: smart-case
        short: S
        type: switch
        description: "Search case-insensitively if pattern is all lowercase"
        category: "Search"
        conflicts:
          - case-sensitive
          - ignore-case

      - name: word-regexp
        short: w
        type: switch
        description: "Show matches surrounded by word boundaries"
        category: "Search"
        conflicts:
          - line-regexp

      - name: line-regexp
        short: x
        type: switch
        description: "Show matches surrounded by line boundaries"
        category: "Search"
        overrides:
          - word-regexp

      # Output Options
      - name: color
        type: enum
        choices: [never, auto, always, ansi]
        default: auto
        description: "When to use color"
        category: "Output"

      - name: context
        short: C
        type: integer
        description: "Show NUM lines before and after each match"
        category: "Output"
        default: 0
        value_name: NUM

      - name: after-context
        short: A
        type: integer
        description: "Show NUM lines after each match"
        category: "Output"
        value_name: NUM
        overrides:
          - context  # partial override

      - name: before-context
        short: B
        type: integer
        description: "Show NUM lines before each match"
        category: "Output"
        value_name: NUM
        overrides:
          - context  # partial override

      - name: json
        type: switch
        description: "Show search results in JSON Lines format"
        negated: no-json
        category: "Output"

      - name: count
        short: c
        type: switch
        description: "Show count of matching lines for each file"
        category: "Output Modes"

      - name: files-with-matches
        short: l
        type: switch
        description: "Print paths with at least one match"
        category: "Output Modes"

      # Filter Options
      - name: type
        short: t
        type: string
        multiple: true
        description: "Only search files matching TYPE"
        category: "Filter"
        completion_type: custom  # from --type-list
        value_name: TYPE

      - name: glob
        short: g
        type: glob
        multiple: true
        description: "Include or exclude files matching GLOB"
        category: "Filter"
        value_name: GLOB

      - name: hidden
        short: "."
        type: switch
        negated: no-hidden
        description: "Search hidden files and directories"
        category: "Filter"

      - name: max-depth
        short: d
        type: integer
        description: "Descend at most NUM directories"
        category: "Filter"
        aliases: [maxdepth]
        value_name: NUM

      # Deprecated
      - name: auto-hybrid-regex
        type: switch
        deprecated: true
        deprecation_message: "Use --engine=auto instead"
        description: "DEPRECATED: Use PCRE2 if appropriate"
        category: "Search"

exit_codes:
  - code: 0
    name: match_found
    description: "At least one match was found"
  - code: 1
    name: no_match
    description: "No matches were found"
  - code: 2
    name: error
    description: "An error occurred (file not found, invalid regex, etc.)"

output:
  formats: [text, json]
  default_format: text
  streaming: true
  schemas:
    json:
      description: "JSON Lines format with message types"
      messages:
        - type: begin
          description: "Signals the start of searching a file"
          schema:
            type: object
            properties:
              type: { const: "begin" }
              data:
                type: object
                properties:
                  path: { "$ref": "#/$defs/Data" }

        - type: match
          description: "A match within a file"
          schema:
            type: object
            properties:
              type: { const: "match" }
              data:
                type: object
                required: [lines, line_number, absolute_offset, submatches]
                properties:
                  path: { "$ref": "#/$defs/Data" }
                  lines: { "$ref": "#/$defs/Data" }
                  line_number: { type: integer }
                  absolute_offset: { type: integer }
                  submatches:
                    type: array
                    items:
                      type: object
                      properties:
                        match: { "$ref": "#/$defs/Data" }
                        start: { type: integer }
                        end: { type: integer }

        - type: context
          description: "Context lines around a match"
          schema:
            type: object
            properties:
              type: { const: "context" }
              data:
                type: object
                properties:
                  path: { "$ref": "#/$defs/Data" }
                  lines: { "$ref": "#/$defs/Data" }
                  line_number: { type: integer }
                  absolute_offset: { type: integer }

        - type: end
          description: "Signals the end of searching a file"
          schema:
            type: object
            properties:
              type: { const: "end" }
              data:
                type: object
                properties:
                  path: { "$ref": "#/$defs/Data" }
                  binary_offset: { type: [integer, "null"] }
                  stats:
                    type: object
                    properties:
                      elapsed: { type: object }
                      searches: { type: integer }
                      searches_with_match: { type: integer }
                      bytes_searched: { type: integer }
                      bytes_printed: { type: integer }
                      matched_lines: { type: integer }
                      matches: { type: integer }

      $defs:
        Data:
          description: "Text data with both text and bytes representations"
          oneOf:
            - type: object
              properties:
                text: { type: string }
            - type: object
              properties:
                bytes: { type: string, description: "base64 encoded" }

environment:
  - name: RIPGREP_CONFIG_PATH
    description: "Path to configuration file"
    affects: [all]

  - name: NO_COLOR
    description: "When set, disables color output"
    affects: [color]

  - name: TERM
    description: "Terminal type, affects color auto-detection"
    affects: [color]

config:
  file_patterns:
    - ".ripgreprc"
    - "$RIPGREP_CONFIG_PATH"
  format: "args"
  description: "One argument per line, same as command line"
```

---

## 4. Requirements

### 4.1 Extraction Requirements

| Source | Priority | Extracts |
|--------|----------|----------|
| `--help` | P0 | Options, descriptions, categories |
| `--generate complete-*` | P0 | Names, types, choices, completion types |
| Shell completions | P1 | Names, descriptions, conflicts |
| Man pages | P1 | Long descriptions, examples |
| Source code (AI) | P1 | Exit codes, output schema, defaults |
| Empirical testing | P2 | Exit codes, output formats |

### 4.2 Validation Requirements

| Validation | Required |
|------------|----------|
| Schema compliance | Yes |
| Option name uniqueness | Yes |
| Exit code uniqueness | Yes |
| Circular override detection | Yes |
| Deprecated option warnings | Yes |
| Output schema validation | If present |

### 4.3 Versioning Requirements

- CIDL files must track CLI version
- Breaking changes require version bump
- Support diff generation between versions
- Maintain changelog per CIDL

---

## 5. Ecosystem Comparison

### 5.1 CIDL vs OpenAPI

| Aspect | OpenAPI | CIDL |
|--------|---------|------|
| **Domain** | REST APIs | CLI tools |
| **Operations** | HTTP methods (GET/POST) | Commands/subcommands |
| **Parameters** | Query, path, body | Options, positional args |
| **Types** | JSON Schema | Simplified + CLI-specific |
| **Responses** | Status codes + schemas | Exit codes + output schemas |
| **Auth** | OAuth, API keys | N/A (local execution) |
| **Streaming** | WebSocket addendum | First-class (stdout) |
| **Maturity** | 10+ years | New |

### 5.2 CIDL vs Shell Completions

| Aspect | Shell Completions | CIDL |
|--------|-------------------|------|
| **Purpose** | Tab completion | SDK generation |
| **Exit codes** | ❌ | ✅ |
| **Output schema** | ❌ | ✅ |
| **Defaults** | ❌ | ✅ |
| **Override rules** | Partial (zsh groups) | ✅ |
| **Machine-readable** | Partially | Fully |
| **Language** | Shell-specific | JSON/YAML |

### 5.3 What's Missing from Ecosystem

| Need | Existing Solution | Gap |
|------|-------------------|-----|
| CLI spec format | None complete | **CIDL fills this** |
| Spec registry | zsh-completions (partial) | **CIDL Registry fills this** |
| SDK generation | None | **CLI→SDK fills this** |
| Spec extraction | Partial (complgen) | **CIDL Extractor fills this** |

---

## 6. Success Metrics

| Metric | Target |
|--------|--------|
| Fields coverage vs ripgrep Flag trait | >95% |
| Extraction accuracy | >90% automated |
| Schema validation pass rate | 100% |
| SDK generation success from valid CIDL | 100% |
| Community-contributed CIDLs (6mo) | 50 |

---

## 7. Roadmap

### Phase 1: Core Schema
- [x] Draft JSON Schema
- [ ] Validation tooling
- [ ] ripgrep reference CIDL
- [ ] Documentation

### Phase 2: Extraction
- [ ] --help parser
- [ ] Completion script parsers
- [ ] AI-assisted extractor
- [ ] Manual review workflow

### Phase 3: Ecosystem
- [ ] CIDL Registry (see PRD-004)
- [ ] VS Code extension
- [ ] CLI tool (`cidl validate`, `cidl diff`)
- [ ] Web-based viewer

---

## 8. Appendices

### A. CompletionType Mapping

| CIDL CompletionType | zsh | fish | bash |
|--------------------|-----|------|------|
| `file` | `_files` | `-r -F` | `compgen -f` |
| `directory` | `_directories` | `-r -F -a '(__fish_complete_directories)'` | `compgen -d` |
| `executable` | `_command_names` | `-a '(__fish_complete_command)'` | `compgen -c` |
| `hostname` | `_hosts` | `-a '(__fish_print_hostnames)'` | `compgen -A hostname` |
| `username` | `_users` | `-a '(__fish_complete_users)'` | `compgen -u` |
| `pid` | `_pids` | `-a '(__fish_complete_pids)'` | `compgen -W "$(ps -eo pid=)"` |

### B. Type Mapping to Languages

| CIDL Type | Python | TypeScript | Go | Rust |
|-----------|--------|------------|-----|------|
| `switch` | `bool` | `boolean` | `bool` | `bool` |
| `string` | `str` | `string` | `string` | `String` |
| `integer` | `int` | `number` | `int64` | `i64` |
| `float` | `float` | `number` | `float64` | `f64` |
| `path` | `PathLike` | `string` | `string` | `PathBuf` |
| `enum` | `Literal[...]` | `"a" \| "b"` | `string` | `enum` |
| `regex` | `str` | `string \| RegExp` | `string` | `String` |
| `glob` | `str` | `string` | `string` | `String` |

# Phase 4: CLI Interface Definition Language (CIDL) Specification

## 1. Overview

CIDL (CLI Interface Definition Language) is a machine-readable specification format for describing CLI tool interfaces. It enables automated SDK generation while preserving semantic correctness.

### Design Goals

1. **Complete**: Describe all CLI behaviors needed for SDK generation
2. **Portable**: Language-agnostic, parseable by any toolchain
3. **Versioned**: Support CLI version tracking and compatibility
4. **Extensible**: Allow custom annotations without breaking parsers
5. **Validatable**: Schema-based validation of CIDL documents

---

## 2. CIDL Schema (JSON Schema)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://cli-to-sdk.dev/cidl/v1.schema.json",
  "title": "CIDL - CLI Interface Definition Language",
  "type": "object",
  "required": ["cidl_version", "cli", "commands"],
  "properties": {
    "cidl_version": {
      "type": "string",
      "pattern": "^1\\.\\d+\\.\\d+$",
      "description": "CIDL specification version"
    },
    "cli": {
      "$ref": "#/$defs/CLIMetadata"
    },
    "commands": {
      "type": "object",
      "additionalProperties": {
        "$ref": "#/$defs/Command"
      }
    },
    "types": {
      "type": "object",
      "additionalProperties": {
        "$ref": "#/$defs/TypeDefinition"
      }
    }
  },
  "$defs": {
    "CLIMetadata": {
      "type": "object",
      "required": ["name", "version", "binary"],
      "properties": {
        "name": { "type": "string" },
        "version": { "type": "string" },
        "binary": { "type": "string" },
        "description": { "type": "string" },
        "homepage": { "type": "string", "format": "uri" },
        "license": { "type": "string" }
      }
    },
    "Command": {
      "type": "object",
      "required": ["description"],
      "properties": {
        "description": { "type": "string" },
        "arguments": {
          "type": "array",
          "items": { "$ref": "#/$defs/Argument" }
        },
        "options": {
          "type": "array",
          "items": { "$ref": "#/$defs/Option" }
        },
        "stdin": { "$ref": "#/$defs/StdinSpec" },
        "stdout": { "$ref": "#/$defs/StdoutSpec" },
        "stderr": { "$ref": "#/$defs/StderrSpec" },
        "exit_codes": { "$ref": "#/$defs/ExitCodes" },
        "examples": {
          "type": "array",
          "items": { "$ref": "#/$defs/Example" }
        },
        "performance": { "$ref": "#/$defs/PerformanceHints" }
      }
    },
    "Argument": {
      "type": "object",
      "required": ["name", "type"],
      "properties": {
        "name": { "type": "string" },
        "type": { "type": "string" },
        "description": { "type": "string" },
        "required": { "type": "boolean", "default": true },
        "position": { "type": "integer" },
        "variadic": { "type": "boolean", "default": false },
        "default": {}
      }
    },
    "Option": {
      "type": "object",
      "required": ["name", "type"],
      "properties": {
        "name": { "type": "string" },
        "short": { "type": "string", "maxLength": 1 },
        "type": { "type": "string" },
        "description": { "type": "string" },
        "required": { "type": "boolean", "default": false },
        "default": {},
        "choices": { "type": "array" },
        "repeatable": { "type": "boolean", "default": false },
        "conflicts_with": { "type": "array", "items": { "type": "string" } },
        "requires": { "type": "array", "items": { "type": "string" } },
        "env_var": { "type": "string" },
        "affects_output": { "type": "boolean", "default": false }
      }
    },
    "StdinSpec": {
      "type": "object",
      "properties": {
        "supported": { "type": "boolean", "default": false },
        "required": { "type": "boolean", "default": false },
        "format": { "type": "string", "enum": ["text", "binary", "json", "lines"] },
        "description": { "type": "string" }
      }
    },
    "StdoutSpec": {
      "type": "object",
      "properties": {
        "modes": {
          "type": "object",
          "additionalProperties": { "$ref": "#/$defs/OutputMode" }
        },
        "default_mode": { "type": "string" }
      }
    },
    "OutputMode": {
      "type": "object",
      "properties": {
        "format": { "type": "string", "enum": ["text", "json", "jsonlines", "binary", "csv"] },
        "streaming": { "type": "boolean", "default": false },
        "schema": { "type": "string" },
        "triggered_by": { "type": "string" }
      }
    },
    "StderrSpec": {
      "type": "object",
      "properties": {
        "contains": {
          "type": "string",
          "enum": ["errors", "warnings", "progress", "mixed"]
        },
        "format": { "type": "string" }
      }
    },
    "ExitCodes": {
      "type": "object",
      "additionalProperties": { "type": "string" }
    },
    "Example": {
      "type": "object",
      "required": ["description", "command"],
      "properties": {
        "description": { "type": "string" },
        "command": { "type": "string" },
        "expected_exit": { "type": "integer" }
      }
    },
    "PerformanceHints": {
      "type": "object",
      "properties": {
        "parallelism": { "type": "string" },
        "cacheable": { "type": "array", "items": { "type": "string" } },
        "streaming_safe": { "type": "boolean" },
        "idempotent": { "type": "boolean" },
        "side_effects": { "type": "boolean", "default": false }
      }
    },
    "TypeDefinition": {
      "type": "object",
      "required": ["kind"],
      "properties": {
        "kind": { "type": "string", "enum": ["enum", "struct", "alias"] },
        "values": { "type": "array" },
        "fields": { "type": "object" },
        "base": { "type": "string" }
      }
    }
  }
}
```

---

## 3. CIDL for ripgrep

```yaml
cidl_version: "1.0.0"

cli:
  name: ripgrep
  version: "15.1.0"
  binary: rg
  description: "Recursively search directories for a regex pattern"
  homepage: "https://github.com/BurntSushi/ripgrep"
  license: "MIT OR Unlicense"

types:
  FileType:
    kind: enum
    values:
      - rust
      - python
      - js
      - ts
      - go
      - java
      - c
      - cpp
      - html
      - css
      - json
      - yaml
      - md
      - txt

  ColorChoice:
    kind: enum
    values:
      - never
      - auto
      - always
      - ansi

  SortBy:
    kind: enum
    values:
      - none
      - path
      - modified
      - accessed
      - created

  Match:
    kind: struct
    fields:
      type:
        type: string
        description: "Always 'match'"
      data:
        type: MatchData

  MatchData:
    kind: struct
    fields:
      path:
        type: PathInfo
      lines:
        type: LinesInfo
      line_number:
        type: integer
      absolute_offset:
        type: integer
      submatches:
        type: array[Submatch]

  PathInfo:
    kind: struct
    fields:
      text:
        type: string

  LinesInfo:
    kind: struct
    fields:
      text:
        type: string

  Submatch:
    kind: struct
    fields:
      match:
        type: MatchText
      start:
        type: integer
      end:
        type: integer

  MatchText:
    kind: struct
    fields:
      text:
        type: string

commands:
  search:
    description: "Search for a pattern in files"

    arguments:
      - name: pattern
        type: string
        description: "The regular expression pattern to search for"
        required: true
        position: 0

      - name: paths
        type: array[path]
        description: "Files or directories to search"
        required: false
        position: 1
        variadic: true
        default: ["."]

    options:
      # Output format options
      - name: json
        type: bool
        description: "Output results in JSON Lines format"
        default: false
        affects_output: true

      - name: count
        short: c
        type: bool
        description: "Only show count of matches per file"
        default: false
        affects_output: true
        conflicts_with: [json, files_with_matches]

      - name: files-with-matches
        short: l
        type: bool
        description: "Only show paths of files with matches"
        default: false
        affects_output: true
        conflicts_with: [json, count]

      - name: files-without-match
        type: bool
        description: "Only show paths of files without matches"
        default: false
        affects_output: true

      # Pattern options
      - name: regexp
        short: e
        type: string
        description: "Pattern to search for (can be repeated)"
        repeatable: true

      - name: file
        short: f
        type: path
        description: "File containing patterns to search for"
        repeatable: true

      - name: ignore-case
        short: i
        type: bool
        description: "Case insensitive search"
        default: false

      - name: smart-case
        short: S
        type: bool
        description: "Smart case (case insensitive unless uppercase present)"
        default: true

      - name: word-regexp
        short: w
        type: bool
        description: "Only match whole words"
        default: false

      - name: fixed-strings
        short: F
        type: bool
        description: "Treat pattern as literal string"
        default: false

      - name: multiline
        short: U
        type: bool
        description: "Enable multiline matching"
        default: false

      # Context options
      - name: context
        short: C
        type: integer
        description: "Show NUM lines before and after match"
        default: 0

      - name: before-context
        short: B
        type: integer
        description: "Show NUM lines before match"
        default: 0

      - name: after-context
        short: A
        type: integer
        description: "Show NUM lines after match"
        default: 0

      # File filtering options
      - name: type
        short: t
        type: FileType
        description: "Only search files of this type"
        repeatable: true

      - name: type-not
        short: T
        type: FileType
        description: "Exclude files of this type"
        repeatable: true

      - name: glob
        short: g
        type: string
        description: "Include/exclude files matching glob"
        repeatable: true

      - name: hidden
        type: bool
        description: "Search hidden files and directories"
        default: false

      - name: no-ignore
        type: bool
        description: "Don't respect ignore files"
        default: false

      - name: max-depth
        type: integer
        description: "Maximum directory depth to search"

      - name: max-filesize
        type: string
        description: "Maximum file size to search (e.g., 1M)"

      # Output control
      - name: line-number
        short: n
        type: bool
        description: "Show line numbers"
        default: true

      - name: no-line-number
        short: N
        type: bool
        description: "Don't show line numbers"
        default: false

      - name: color
        type: ColorChoice
        description: "When to use colors"
        default: auto

      - name: heading
        type: bool
        description: "Group matches by file"
        default: true

      - name: no-heading
        type: bool
        description: "Don't group matches by file"
        default: false

      - name: max-count
        short: m
        type: integer
        description: "Maximum matches per file"

      - name: sort
        type: SortBy
        description: "Sort results"
        default: none

      - name: null
        type: bool
        description: "Use NUL as line terminator"
        default: false
        affects_output: true

      # Performance options
      - name: threads
        short: j
        type: integer
        description: "Number of threads to use"
        env_var: RIPGREP_THREADS

      - name: mmap
        type: bool
        description: "Use memory maps when possible"

      - name: no-mmap
        type: bool
        description: "Never use memory maps"

    stdin:
      supported: true
      required: false
      format: text
      description: "Search stdin instead of files when no paths given"

    stdout:
      default_mode: text
      modes:
        text:
          format: text
          streaming: true
          triggered_by: null

        json:
          format: jsonlines
          streaming: true
          triggered_by: "--json"
          schema: "#/types/Match"

        files:
          format: lines
          streaming: true
          triggered_by: "-l"

        count:
          format: text
          streaming: true
          triggered_by: "-c"

    stderr:
      contains: errors
      format: text

    exit_codes:
      "0": "At least one match was found"
      "1": "No matches were found"
      "2": "An error occurred"

    examples:
      - description: "Search for 'TODO' in current directory"
        command: "rg TODO"
        expected_exit: 0

      - description: "Search with JSON output"
        command: "rg --json pattern ."
        expected_exit: 0

      - description: "Case insensitive search in Rust files"
        command: "rg -i -t rust 'fn main'"
        expected_exit: 0

      - description: "Count matches per file"
        command: "rg -c pattern"
        expected_exit: 0

    performance:
      parallelism: file-level
      cacheable:
        - compiled_regex
        - file_type_definitions
        - ignore_patterns
      streaming_safe: true
      idempotent: true
      side_effects: false

  files:
    description: "List files that would be searched"

    arguments:
      - name: paths
        type: array[path]
        description: "Directories to list"
        required: false
        position: 0
        variadic: true
        default: ["."]

    options:
      - name: type
        short: t
        type: FileType
        description: "Only list files of this type"
        repeatable: true

      - name: glob
        short: g
        type: string
        description: "Include/exclude files matching glob"
        repeatable: true

      - name: hidden
        type: bool
        description: "Include hidden files"
        default: false

      - name: null
        type: bool
        description: "Use NUL as line terminator"
        default: false

    stdout:
      default_mode: files
      modes:
        files:
          format: lines
          streaming: true

    exit_codes:
      "0": "Success"
      "2": "Error"

    performance:
      parallelism: directory-level
      streaming_safe: true
      idempotent: true
      side_effects: false

  type_list:
    description: "List supported file types"

    options: []

    stdout:
      default_mode: text
      modes:
        text:
          format: text
          streaming: false

    exit_codes:
      "0": "Success"

    performance:
      cacheable: [file_type_definitions]
      streaming_safe: false
      idempotent: true
      side_effects: false
```

---

## 4. CIDL Processing Pipeline

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  CLI Tool   │     │    CIDL     │     │   SDK Gen   │
│             │────▶│   Parser    │────▶│             │
│ --help, man │     │             │     │  Templates  │
└─────────────┘     └──────┬──────┘     └──────┬──────┘
                           │                    │
                           ▼                    ▼
                    ┌─────────────┐      ┌─────────────┐
                    │  Validated  │      │  Generated  │
                    │    CIDL     │      │    SDK      │
                    └─────────────┘      └─────────────┘
```

---

## 5. SDK Generation from CIDL

Given a CIDL definition, generate:

### Python SDK Structure

```
ripgrep_sdk/
├── __init__.py
├── types.py          # Generated from types section
├── client.py         # Generated from commands
├── _subprocess.py    # Tier A adapter
├── _daemon.py        # Tier B adapter (optional)
└── py.typed          # PEP 561 marker
```

### Generated Types (types.py)

```python
# Auto-generated from CIDL types section

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional
from pathlib import Path

class FileType(Enum):
    RUST = "rust"
    PYTHON = "python"
    JS = "js"
    # ... generated from CIDL

class ColorChoice(Enum):
    NEVER = "never"
    AUTO = "auto"
    ALWAYS = "always"
    ANSI = "ansi"

@dataclass
class Submatch:
    text: str
    start: int
    end: int

@dataclass
class Match:
    path: Path
    line_number: int
    line_content: str
    absolute_offset: int
    submatches: List[Submatch]
```

### Generated Client (client.py)

```python
# Auto-generated from CIDL commands section

from typing import Iterator, Optional, List, Union
from pathlib import Path
from .types import Match, FileType, ColorChoice
from ._subprocess import TierAAdapter

class Ripgrep:
    """ripgrep SDK client.

    Auto-generated from CIDL v1.0.0
    CLI version: 15.1.0
    """

    def __init__(self, binary: str = "rg"):
        self._adapter = TierAAdapter(binary)

    def search(
        self,
        pattern: str,
        paths: Union[str, Path, List[Union[str, Path]]] = ".",
        *,
        # Generated from CIDL options
        ignore_case: bool = False,
        smart_case: bool = True,
        word_regexp: bool = False,
        fixed_strings: bool = False,
        multiline: bool = False,
        context: int = 0,
        before_context: int = 0,
        after_context: int = 0,
        file_type: Optional[List[FileType]] = None,
        glob: Optional[List[str]] = None,
        hidden: bool = False,
        no_ignore: bool = False,
        max_depth: Optional[int] = None,
        max_count: Optional[int] = None,
        threads: Optional[int] = None,
    ) -> Iterator[Match]:
        """Search for a pattern in files.

        Args:
            pattern: The regular expression pattern to search for
            paths: Files or directories to search
            ignore_case: Case insensitive search
            # ... generated from CIDL descriptions

        Yields:
            Match objects for each match found

        Raises:
            RipgrepError: If an error occurs during search

        Examples:
            >>> rg = Ripgrep()
            >>> for match in rg.search("TODO", "."):
            ...     print(f"{match.path}:{match.line_number}")
        """
        args = self._build_args(
            pattern=pattern,
            paths=paths,
            ignore_case=ignore_case,
            # ... all options
        )

        for result in self._adapter.execute(args):
            if result.get('type') == 'match':
                yield Match.from_json(result)

    def _build_args(self, **kwargs) -> List[str]:
        """Build command-line arguments from kwargs."""
        args = ['--json']  # Always use JSON for parsing

        if kwargs.get('ignore_case'):
            args.append('-i')
        if kwargs.get('context'):
            args.extend(['-C', str(kwargs['context'])])
        # ... generated from CIDL options

        args.append(kwargs['pattern'])
        args.extend(str(p) for p in kwargs.get('paths', ['.']))

        return args
```

---

*Phase 4 Complete. Proceed to Phase 5: Performance Patterns.*

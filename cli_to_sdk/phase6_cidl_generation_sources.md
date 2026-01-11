# Phase 6: CIDL Generation Sources Analysis

## Executive Summary

This phase analyzes the sources available for automated CIDL (CLI Interface Definition Language) generation, evaluating their quality, coverage, and practical extraction strategies.

## 1. Source Analysis

### Source 1: Built-in Completion Generation (HIGH VALUE)

**Discovery**: ripgrep generates its own shell completions programmatically:

```bash
rg --generate complete-bash
rg --generate complete-zsh
rg --generate complete-fish
rg --generate complete-powershell
```

**Implementation Location**: `crates/core/flags/complete/`

The completions are generated from structured flag definitions in `crates/core/flags/defs.rs`:

```rust
pub(super) const FLAGS: &[&dyn Flag] = &[
    &Regexp,
    &File,
    &AfterContext,
    &BeforeContext,
    // ... 100+ flags
];
```

Each flag implements the `Flag` trait with methods:
- `name_long()` → `"after-context"`
- `name_short()` → `Some('A')`
- `name_negated()` → `Some("no-after-context")`
- `doc_short()` → `"Show NUM lines after each match."`
- `doc_long()` → Full documentation with roff formatting
- `doc_choices()` → `["value1", "value2"]` for enum options
- `doc_category()` → `Category::Output`, `Category::Search`, etc.
- `is_switch()` → boolean vs value-taking flag
- `update()` → How flag modifies state

**Extraction Value**: This is a goldmine. The structured `Flag` definitions contain:
- Complete option inventory
- Type information (switch vs value, choices)
- Documentation (short and long form)
- Categorization
- Negation patterns
- Dependencies/overrides (documented in `doc_long`)

**Many CLIs support this pattern**:
| Tool | Completion Flag |
|------|-----------------|
| ripgrep | `rg --generate complete-{bash,zsh,fish,powershell}` |
| kubectl | `kubectl completion {bash,zsh,fish,powershell}` |
| docker | `docker completion {bash,zsh,fish}` |
| gh | `gh completion -s {bash,zsh,fish,powershell}` |
| yq | `yq shell-completion {bash,zsh,fish,powershell}` |
| clusterctl | `clusterctl completion {bash,zsh,fish,powershell}` |

### Source 2: Centralized Completion Repositories (MEDIUM VALUE)

**Centralized repos exist** (analogous to @types/x for TypeScript):

| Repository | Shell | Coverage |
|------------|-------|----------|
| [zsh-users/zsh-completions](https://github.com/zsh-users/zsh-completions) | zsh | 400+ commands |
| bash-completion | bash | 200+ commands |
| fish-shell completions | fish | 300+ built-in |

**zsh-completions Structure**:
```
src/
├── _docker
├── _git
├── _npm
├── _cargo
├── _kubectl
└── ... hundreds more
```

Each completion file contains structured information about:
- Option names and shortcuts
- Argument types (file, directory, custom values)
- Subcommands and their options
- Value completions (e.g., `--type` → list of file types)

**Extraction Challenges**:
- Shell-specific syntax (zsh completion format is complex)
- Inconsistent quality across contributors
- May lag behind tool updates
- Documentation often missing (just completion, no descriptions)

### Source 3: --help Output (MEDIUM VALUE)

Nearly every CLI supports `--help`:

```bash
$ rg --help
ripgrep 14.1.1
Andrew Gallant <jamslam@gmail.com>

ripgrep (rg) recursively searches the current directory for a regex pattern.

USAGE:
    rg [OPTIONS] PATTERN [PATH ...]
    rg [OPTIONS] -e PATTERN ... [PATH ...]
    rg [OPTIONS] -f PATTERNFILE ... [PATH ...]
    ...
```

**Extraction Potential**:
- Option names (long and short forms)
- Basic descriptions
- Usage patterns
- Sometimes value examples

**Challenges**:
- Unstructured text requiring parsing
- Inconsistent formats across tools
- May not include all options
- Missing type information
- No machine-readable exit codes

### Source 4: Man Pages (LOW-MEDIUM VALUE)

Man pages provide comprehensive documentation:

```bash
man rg
# or
rg --generate man
```

**Content**:
- Complete option documentation
- Examples
- Exit codes (often)
- Environment variables
- Files (config locations)

**Challenges**:
- roff/troff format parsing
- Even less structured than --help
- Not all tools have man pages

### Source 5: Source Code Analysis (HIGH VALUE, HIGH EFFORT)

For open-source tools, the source contains authoritative definitions.

**ripgrep Example**:
- `crates/core/flags/defs.rs` - Flag definitions
- `crates/core/flags/lowargs.rs` - Argument types
- Exit codes in error handling

**Extraction Method**: Claude Agent SDK / AI Analysis
- Parse argument parser setup (clap, argparse, cobra, etc.)
- Extract type definitions
- Find exit code definitions
- Identify undocumented options

**Tools Using Common Argument Parsers**:
| Parser | Language | Examples |
|--------|----------|----------|
| clap | Rust | ripgrep, bat, fd, exa |
| argparse | Python | many Python CLIs |
| cobra | Go | kubectl, docker, gh |
| commander | Node.js | npm, many JS CLIs |
| click | Python | Flask, pip, many |

## 2. Hybrid Extraction Strategy

### The Multi-Source Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                     CIDL Generation Pipeline                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐        │
│  │ --generate   │   │   --help     │   │   Source     │        │
│  │ complete-*   │   │   Output     │   │   Code       │        │
│  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘        │
│         │                  │                   │                 │
│         ▼                  ▼                   ▼                 │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐        │
│  │   Parser:    │   │   Parser:    │   │  AI Agent:   │        │
│  │ Shell Script │   │    Text/     │   │ Claude Code  │        │
│  │  Extractor   │   │   Heuristic  │   │   SDK        │        │
│  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘        │
│         │                  │                   │                 │
│         └──────────────────┼───────────────────┘                 │
│                            ▼                                     │
│                  ┌──────────────────┐                           │
│                  │   Merger &       │                           │
│                  │   Validator      │                           │
│                  └────────┬─────────┘                           │
│                           ▼                                      │
│                  ┌──────────────────┐                           │
│                  │   CIDL Output    │                           │
│                  │   (JSON/YAML)    │                           │
│                  └──────────────────┘                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Priority Order

1. **Self-generating completions** (`--generate complete-*`, `completion` subcommand)
   - Highest quality, machine-readable
   - Check first: many modern CLIs support this

2. **Centralized completion repos**
   - Good fallback for popular tools
   - Parse zsh-completions/bash-completion

3. **--help parsing**
   - Universal availability
   - Use as supplement/validation

4. **Source code analysis via AI**
   - For open-source tools
   - Fill gaps in above sources
   - Validate inferred information

## 3. Practical Implementation

### Step 1: Detect Available Sources

```python
def detect_cidl_sources(command: str) -> dict:
    """Detect available CIDL generation sources for a command."""
    sources = {}

    # Check for built-in completion generation
    for shell in ['bash', 'zsh', 'fish', 'powershell']:
        for pattern in [
            f'--generate complete-{shell}',
            f'completion {shell}',
            f'completion -s {shell}',
            f'shell-completion {shell}',
        ]:
            try:
                result = subprocess.run(
                    [command] + pattern.split(),
                    capture_output=True, timeout=5
                )
                if result.returncode == 0 and result.stdout:
                    sources[f'builtin_{shell}'] = pattern
                    break
            except:
                continue

    # Check for --help
    try:
        result = subprocess.run([command, '--help'], capture_output=True)
        if result.returncode in (0, 1) and result.stdout:
            sources['help'] = True
    except:
        pass

    # Check centralized repos
    if zsh_completions_path(command).exists():
        sources['zsh_completions'] = True
    if bash_completions_path(command).exists():
        sources['bash_completions'] = True

    return sources
```

### Step 2: Parse Completion Scripts

```python
def parse_zsh_completion(content: str) -> dict:
    """Extract structured data from zsh completion script."""
    options = []

    # Match option definitions like:
    # '--after-context=[show NUM lines after each match]:number'
    # '-A[short form of after-context]'
    pattern = r"'(-{1,2}[\w-]+)(\[([^\]]*)\])?(:[^']*)?'"

    for match in re.finditer(pattern, content):
        opt = {
            'name': match.group(1),
            'description': match.group(3) or '',
            'takes_value': ':' in (match.group(4) or ''),
        }
        options.append(opt)

    return {'options': options}
```

### Step 3: AI-Assisted Gap Filling

For open-source projects, use Claude Agent SDK to:

```python
async def analyze_source_for_cidl(repo_path: str) -> dict:
    """Use AI to extract CLI definition from source code."""

    prompt = """
    Analyze this codebase to extract CLI interface definition:

    1. Find the argument parser setup (clap, cobra, argparse, etc.)
    2. Extract all commands and subcommands
    3. For each option, extract:
       - Long name, short name, aliases
       - Description
       - Value type (string, int, bool, enum with values)
       - Default value
       - Required/optional
    4. Find exit code definitions
    5. Find environment variable usage
    6. Find config file patterns

    Return as structured JSON matching CIDL schema.
    """

    # Use Claude Agent SDK to explore and analyze
    result = await agent.run(prompt, cwd=repo_path)
    return result.cidl
```

### Step 4: Merge and Validate

```python
def merge_cidl_sources(sources: List[dict]) -> dict:
    """Merge CIDL data from multiple sources, preferring higher-quality sources."""

    merged = {'options': {}, 'commands': {}}

    # Priority: builtin > centralized > help > inferred
    for source in sorted(sources, key=lambda s: s['priority'], reverse=True):
        for opt_name, opt_data in source.get('options', {}).items():
            if opt_name not in merged['options']:
                merged['options'][opt_name] = opt_data
            else:
                # Merge missing fields from lower-priority source
                for key, value in opt_data.items():
                    if key not in merged['options'][opt_name]:
                        merged['options'][opt_name][key] = value

    return merged
```

## 4. Coverage Estimates

Based on analysis of popular CLIs:

| Category | Has Built-in Completion | In zsh-completions | Needs AI Analysis |
|----------|------------------------|--------------------|--------------------|
| Modern Rust CLIs | ~80% | ~90% | ~10% |
| Go CLIs (Cobra) | ~70% | ~85% | ~15% |
| Python CLIs | ~40% | ~75% | ~30% |
| Legacy Unix tools | ~5% | ~95% | ~50% |
| Node.js CLIs | ~30% | ~60% | ~50% |

**Estimated Overall Coverage**:
- Source 1 (built-in): 40-50% of modern CLIs
- Source 1+2 (+ centralized): 70-80%
- Source 1+2+3 (+ help): 90-95%
- Source 1+2+3+4 (+ AI): 98-99%

## 5. Keeping CIDL Up-to-Date

### Automated Update Pipeline

```yaml
# .github/workflows/update-cidl.yml
name: Update CIDL definitions

on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly
  workflow_dispatch:

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Update tool versions
        run: |
          # Install latest versions of tracked tools
          cargo install ripgrep fd-find bat
          go install github.com/cli/cli/v2/cmd/gh@latest

      - name: Regenerate CIDLs
        run: |
          for tool in rg fd bat gh; do
            python scripts/generate_cidl.py $tool > cidl/$tool.yaml
          done

      - name: Check for changes
        run: |
          git diff --exit-code cidl/ || {
            echo "CIDL definitions changed"
            # Create PR or commit
          }
```

### Version-Aware CIDL

```yaml
# cidl/ripgrep.yaml
meta:
  tool: ripgrep
  version: "14.1.1"
  last_updated: "2025-01-11"
  sources:
    - type: builtin_completion
      command: "rg --generate complete-zsh"
    - type: help
      command: "rg --help"
    - type: source_analysis
      repo: "https://github.com/BurntSushi/ripgrep"
      commit: "e3cc4d2"

options:
  # ... full CIDL definition
```

## 6. Key Insights

### Insight 1: Self-Documenting CLIs Are Increasing

Modern CLI frameworks (clap 4.x, cobra, click) encourage structured option definitions that can generate:
- Shell completions
- Man pages
- --help text
- JSON schema

This trend makes CIDL extraction increasingly tractable.

### Insight 2: Completion Scripts Are More Structured Than --help

Completion scripts contain machine-readable patterns:
- Explicit option lists
- Value type hints (file, directory, choices)
- Subcommand trees
- Mutual exclusivity

### Insight 3: AI Fills the Long Tail

For the ~20% of CLIs without good built-in or centralized completions, AI-based source code analysis provides:
- One-time extraction with human review
- Handles legacy/unusual patterns
- Can infer from examples and tests

### Insight 4: The @types Analogy Is Valid

Like DefinitelyTyped for TypeScript, a community-maintained CIDL repository could:
- Aggregate CIDLs for popular tools
- Accept community contributions
- Run automated validation
- Generate SDKs for multiple languages

## 7. Recommended Architecture

```
cidl-registry/
├── registry/
│   ├── ripgrep/
│   │   ├── cidl.yaml
│   │   ├── versions/
│   │   │   ├── 14.1.1.yaml
│   │   │   └── 14.0.0.yaml
│   │   └── tests/
│   ├── fd/
│   ├── bat/
│   └── ...
├── extractors/
│   ├── builtin_completion.py
│   ├── zsh_completion.py
│   ├── help_parser.py
│   └── ai_extractor.py
├── generators/
│   ├── python_sdk/
│   ├── typescript_sdk/
│   └── rust_sdk/
└── validation/
    ├── schema.json
    └── test_runner.py
```

## References

- [zsh-users/zsh-completions](https://github.com/zsh-users/zsh-completions) - 400+ zsh completions
- [Homebrew bash-completion](https://formulae.brew.sh/formula/bash-completion) - bash completions framework
- [ripgrep flag definitions](https://github.com/BurntSushi/ripgrep/blob/master/crates/core/flags/defs.rs) - Structured flag system
- [clap derive macros](https://docs.rs/clap/latest/clap/_derive/) - Rust argument parsing with auto-completion
- [cobra](https://cobra.dev/) - Go CLI framework with completion generation

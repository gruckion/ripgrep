# PRD-004: CIDL Registry

## Product Requirements Document

**Version**: 1.0
**Date**: 2025-01-11
**Author**: Research Phase
**Status**: Conceptual Design
**Parent**: PRD-001 CLI→SDK System

---

## 1. Executive Summary

### 1.1 Purpose

Create a community-maintained registry of CIDL (CLI Interface Definition Language) specifications—the **DefinitelyTyped for CLI tools**. This registry provides the foundational data layer that enables automatic SDK generation for any CLI tool.

### 1.2 Analogy: DefinitelyTyped

| DefinitelyTyped | CIDL Registry |
|-----------------|---------------|
| TypeScript type definitions | CLI interface definitions |
| `@types/lodash` | `@cidl/ripgrep` |
| .d.ts files | .cidl.yaml files |
| npm install | pip install / npm install |
| tsc type checking | SDK generation |
| 8,000+ packages | Target: 200+ CLIs (12mo) |

### 1.3 Why a Registry?

**Problem**: Each CLI is its own island.

- No standardized way to describe CLI interfaces
- SDK authors reinvent argument parsing for each tool
- Completions, man pages, help text are inconsistent
- AI tools struggle to use CLIs reliably

**Solution**: Centralized, versioned, validated CIDL definitions.

```
Without Registry:                 With Registry:

CLI Tool ──?──> Your Code         CLI Tool ──> CIDL Registry ──> Generated SDK ──> Your Code
   │                                  │              │                   │
   └── Parse --help                   └── Extract    └── Validate        └── Type-safe
   └── Hope format stable                            └── Version         └── Documented
   └── No types                                      └── Community       └── Tested
```

---

## 2. Research Findings

### 2.1 Ecosystem Analysis

#### 2.1.1 Existing "Type Definition" Registries

| Registry | Domain | Entries | Model |
|----------|--------|---------|-------|
| **DefinitelyTyped** | TypeScript types | 8,000+ | GitHub + npm |
| **typeshed** | Python stubs | 500+ | GitHub + PyPI |
| **zsh-completions** | Zsh completions | 400+ | GitHub |
| **bash-completion** | Bash completions | 200+ | Linux packages |
| **APIs.guru** | OpenAPI specs | 2,000+ | GitHub |

#### 2.1.2 Key Success Factors from DefinitelyTyped

| Factor | How DT Does It | CIDL Registry Equivalent |
|--------|---------------|-------------------------|
| **Low barrier** | PR with .d.ts file | PR with .cidl.yaml file |
| **Automation** | dtslint, CI checks | cidl-lint, CI validation |
| **Ownership** | CODEOWNERS per package | CODEOWNERS per CLI |
| **Versioning** | Tracks library versions | Tracks CLI versions |
| **Discovery** | npm search | cidl search / web |
| **Quality** | Strict type checking | Schema validation |

#### 2.1.3 Learning from zsh-completions

| Aspect | zsh-completions | CIDL Registry Improvement |
|--------|----------------|---------------------------|
| Format | Shell script | Structured YAML/JSON |
| Validation | Manual | Automated schema validation |
| Extractable | Hard (parse shell) | Easy (JSON) |
| Multi-shell | Zsh only | Shell-agnostic (generate all) |
| SDK generation | No | Yes (primary purpose) |

### 2.2 CLI Landscape Analysis

#### 2.2.1 Popular CLI Categories

| Category | Examples | Count Estimate |
|----------|----------|----------------|
| Dev tools | git, docker, npm, cargo | 50+ |
| Cloud CLIs | aws, gcloud, az, kubectl | 20+ |
| Search/text | ripgrep, grep, awk, jq | 30+ |
| File management | rsync, tar, zip, find | 40+ |
| Network | curl, wget, ssh, nc | 30+ |
| System | ps, top, htop, systemctl | 50+ |
| Language tools | python, node, ruby, go | 20+ |
| **Total priority targets** | | **200+** |

#### 2.2.2 CLI Complexity Distribution

| Complexity | Options Count | Examples | % of CLIs |
|------------|--------------|----------|-----------|
| Simple | 1-10 | echo, cat, ls | 40% |
| Medium | 11-50 | curl, git (subcommands) | 35% |
| Complex | 51-100 | ripgrep, docker | 20% |
| Very Complex | 100+ | aws, kubectl | 5% |

### 2.3 Contribution Model Analysis

#### 2.3.1 Contribution Sources

| Source | Quality | Effort | Coverage |
|--------|---------|--------|----------|
| **Automated extraction** | Medium | Low | High (70%) |
| **Community PRs** | Variable | Medium | Medium |
| **AI-assisted** | Medium-High | Low | Gap-filling |
| **Official (CLI authors)** | High | Medium | Low initially |

#### 2.3.2 Maintenance Patterns

| Trigger | Action | Automation |
|---------|--------|------------|
| New CLI release | Re-extract, diff, PR | Fully automated |
| Community PR | Validate, review, merge | Semi-automated |
| Bug report | Investigate, fix | Manual |
| New CLI request | Extract, create | Semi-automated |

---

## 3. Requirements

### 3.1 Functional Requirements

#### 3.1.1 Registry Structure

```
cidl-registry/
├── registry/
│   ├── ripgrep/
│   │   ├── cidl.yaml           # Current version
│   │   ├── versions/
│   │   │   ├── 14.1.1.yaml
│   │   │   ├── 14.0.0.yaml
│   │   │   └── 13.0.0.yaml
│   │   ├── CHANGELOG.md
│   │   └── tests/
│   │       └── test_ripgrep.py
│   ├── docker/
│   │   ├── cidl.yaml
│   │   └── subcommands/
│   │       ├── build.yaml
│   │       ├── run.yaml
│   │       └── ...
│   ├── git/
│   ├── curl/
│   └── ...
├── tools/
│   ├── extract/              # Extraction scripts
│   ├── validate/             # Validation tooling
│   └── generate/             # SDK generators
├── schemas/
│   └── cidl-v1.json          # CIDL JSON Schema
└── .github/
    └── workflows/
        ├── validate.yml
        ├── update-check.yml
        └── publish.yml
```

#### 3.1.2 CLI Tool (`cidl`)

```bash
# Discovery
cidl search ripgrep           # Search registry
cidl info ripgrep             # Show CIDL details
cidl list --category=search   # List by category

# Extraction
cidl extract rg               # Extract CIDL from installed CLI
cidl extract rg --output=cidl.yaml

# Validation
cidl validate cidl.yaml       # Validate against schema
cidl lint cidl.yaml           # Lint for best practices
cidl diff old.yaml new.yaml   # Show changes

# Generation
cidl generate python ripgrep  # Generate Python SDK
cidl generate typescript ripgrep
cidl generate completions ripgrep bash

# Contribution
cidl init ripgrep             # Create new CIDL scaffold
cidl test ripgrep             # Run tests
cidl submit                   # Create PR
```

#### 3.1.3 Web Interface

| Feature | Description |
|---------|-------------|
| **Browse** | List all CIDLs with search/filter |
| **View** | Human-readable CIDL display |
| **Diff** | Compare versions |
| **Stats** | Contribution statistics |
| **Docs** | Generated documentation per CLI |

#### 3.1.4 API

```
GET  /api/v1/cidl                    # List all CIDLs
GET  /api/v1/cidl/{name}             # Get CIDL
GET  /api/v1/cidl/{name}/versions    # List versions
GET  /api/v1/cidl/{name}/{version}   # Get specific version
POST /api/v1/validate                # Validate CIDL
GET  /api/v1/search?q={query}        # Search
```

### 3.2 Quality Requirements

#### 3.2.1 Validation Levels

| Level | Checks | Required |
|-------|--------|----------|
| **Schema** | JSON Schema compliance | Yes |
| **Syntax** | Option name formats, types | Yes |
| **Semantic** | Conflict consistency, override cycles | Yes |
| **Extraction** | Can re-extract and match | Recommended |
| **Runtime** | Generated SDK works | Recommended |

#### 3.2.2 Quality Gates

```yaml
# .github/workflows/validate.yml
validation:
  required:
    - schema_valid: true
    - no_duplicate_options: true
    - all_types_valid: true
    - exit_codes_defined: true
  recommended:
    - output_schema_present: true
    - examples_present: true
    - long_descriptions: true
  warnings:
    - deprecated_without_message: warn
    - missing_categories: warn
```

### 3.3 Versioning Requirements

#### 3.3.1 Version Tracking

```yaml
# cidl.yaml
meta:
  name: ripgrep
  cli_version: "14.1.1"        # Version of the CLI tool
  cidl_version: "1.2.3"        # Version of this CIDL definition
  cidl_spec: "1.0"             # CIDL specification version
  last_extracted: "2025-01-11"
  extraction_sources:
    - "rg --help"
    - "rg --generate complete-zsh"
```

#### 3.3.2 Compatibility Matrix

```yaml
# versions/compatibility.yaml
ripgrep:
  cidl_versions:
    "1.2.3":
      cli_versions: ["14.1.0", "14.1.1"]
      sdk_versions:
        python: "0.3.0"
        typescript: "0.2.1"
    "1.2.0":
      cli_versions: ["14.0.0", "14.0.1", "14.0.2"]
      sdk_versions:
        python: "0.2.0"
```

### 3.4 Contribution Requirements

#### 3.4.1 Contribution Workflow

```
1. Fork repository
2. cidl init <cli-name>           # Create scaffold
3. cidl extract <cli-name>        # Auto-extract
4. Edit cidl.yaml                 # Fill gaps manually
5. cidl validate                  # Validate
6. cidl test                      # Run tests
7. Create PR
8. CI validation
9. Review
10. Merge
11. Auto-publish SDKs
```

#### 3.4.2 CODEOWNERS

```
# CODEOWNERS
/registry/ripgrep/    @burntsushi @cidl-maintainers
/registry/docker/     @docker @cidl-maintainers
/registry/git/        @gitster @cidl-maintainers
/registry/*/          @cidl-maintainers
```

---

## 4. Architecture

### 4.1 System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CIDL Registry                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐           │
│  │   GitHub    │────▶│   CI/CD     │────▶│   Package   │           │
│  │   Repo      │     │ (Actions)   │     │  Registries │           │
│  └─────────────┘     └─────────────┘     └─────────────┘           │
│         │                  │                    │                   │
│         │                  │                    ▼                   │
│         │                  │           ┌───────────────┐            │
│         │                  │           │ PyPI  │ npm   │            │
│         │                  │           │ @cidl/ripgrep │            │
│         │                  │           └───────────────┘            │
│         │                  │                                        │
│         ▼                  ▼                                        │
│  ┌─────────────┐     ┌─────────────┐                               │
│  │   Web UI    │     │    API      │                               │
│  │  (Browse,   │     │  (REST,     │                               │
│  │   Search)   │     │   GraphQL)  │                               │
│  └─────────────┘     └─────────────┘                               │
│                            │                                        │
│                            ▼                                        │
│                    ┌─────────────┐                                  │
│                    │   Search    │                                  │
│                    │   Index     │                                  │
│                    └─────────────┘                                  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Consumers                                    │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐               │
│  │  SDK Users  │   │   AI Tools  │   │ Completion  │               │
│  │   (pip,     │   │  (Claude,   │   │ Generators  │               │
│  │    npm)     │   │   GPT)      │   │             │               │
│  └─────────────┘   └─────────────┘   └─────────────┘               │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 CI/CD Pipeline

```yaml
# .github/workflows/cidl-ci.yml
name: CIDL CI

on:
  pull_request:
    paths:
      - 'registry/**'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Detect changed CIDLs
        id: changes
        run: |
          echo "cidls=$(git diff --name-only HEAD~1 | grep 'registry/.*/cidl.yaml' | cut -d/ -f2 | uniq)" >> $GITHUB_OUTPUT

      - name: Validate CIDLs
        run: |
          for cli in ${{ steps.changes.outputs.cidls }}; do
            cidl validate registry/$cli/cidl.yaml
            cidl lint registry/$cli/cidl.yaml
          done

      - name: Test SDK generation
        run: |
          for cli in ${{ steps.changes.outputs.cidls }}; do
            cidl generate python $cli --output=/tmp/sdk
            cd /tmp/sdk && pytest
          done

  publish:
    needs: validate
    if: github.event.pull_request.merged == true
    runs-on: ubuntu-latest
    steps:
      - name: Generate and publish SDKs
        run: |
          for cli in ${{ steps.changes.outputs.cidls }}; do
            cidl generate python $cli
            twine upload dist/*

            cidl generate typescript $cli
            npm publish
          done
```

### 4.3 Update Detection

```yaml
# .github/workflows/update-check.yml
name: Check for CLI Updates

on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly

jobs:
  check-updates:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        cli: [ripgrep, fd, bat, docker, kubectl]  # High-priority CLIs

    steps:
      - name: Install latest ${{ matrix.cli }}
        run: |
          # Install logic per CLI

      - name: Extract CIDL
        run: |
          cidl extract ${{ matrix.cli }} --output=new.yaml

      - name: Compare with registry
        run: |
          cidl diff registry/${{ matrix.cli }}/cidl.yaml new.yaml > diff.txt
          if [ -s diff.txt ]; then
            echo "Changes detected"
            # Create issue or PR
          fi
```

---

## 5. Prioritization

### 5.1 Launch CLIs (Top 50)

| Priority | Category | CLIs |
|----------|----------|------|
| **P0** | Search/Text | ripgrep, grep, awk, sed, jq, yq |
| **P0** | Dev Tools | git, docker, npm, cargo, pip |
| **P0** | Cloud | aws, gcloud, az, kubectl |
| **P1** | Network | curl, wget, ssh, scp, rsync |
| **P1** | File | tar, zip, find, fd, bat, eza |
| **P1** | System | ps, htop, systemctl, journalctl |
| **P2** | Languages | python, node, go, ruby, rustc |
| **P2** | Databases | psql, mysql, redis-cli, mongosh |

### 5.2 Complexity vs Impact

```
                    High Impact
                         │
    ┌────────────────────┼────────────────────┐
    │                    │                    │
    │  P1: Medium        │  P0: High Priority │
    │  fd, bat, eza      │  ripgrep, git,     │
    │  httpie            │  docker, kubectl   │
    │                    │  aws, curl         │
Low ├────────────────────┼────────────────────┤ High
Complexity               │                    Complexity
    │                    │                    │
    │  P3: Nice to Have  │  P2: Worth It      │
    │  echo, cat, ls     │  terraform, helm   │
    │  head, tail        │  ansible           │
    │                    │                    │
    └────────────────────┼────────────────────┘
                         │
                    Low Impact
```

---

## 6. Ecosystem Integration

### 6.1 Package Registry Integration

#### 6.1.1 Python (PyPI)

```
pip install cidl-ripgrep
```

```python
# Generated package structure
cidl_ripgrep/
├── __init__.py
├── client.py
├── types.py
├── errors.py
└── py.typed
```

#### 6.1.2 JavaScript/TypeScript (npm)

```
npm install @cidl/ripgrep
```

```typescript
// Generated package
import { Ripgrep, Match } from '@cidl/ripgrep';

const rg = new Ripgrep();
for await (const match of rg.search('pattern', 'path/')) {
  console.log(match);
}
```

### 6.2 AI Tool Integration

```yaml
# AI tool configuration
tools:
  - name: ripgrep
    cidl: https://cidl.dev/api/v1/cidl/ripgrep
    description: "Fast text search tool"
```

### 6.3 IDE Integration

| IDE | Integration |
|-----|-------------|
| VS Code | Extension for CIDL editing, validation |
| JetBrains | Plugin for generated SDK documentation |
| Vim/Neovim | cidl.vim for syntax highlighting |

---

## 7. Success Metrics

### 7.1 Registry Metrics

| Metric | 3mo | 6mo | 12mo |
|--------|-----|-----|------|
| CIDLs in registry | 20 | 50 | 200 |
| Contributors | 5 | 20 | 100 |
| GitHub stars | 100 | 500 | 2,000 |
| Weekly active extractions | 100 | 500 | 2,000 |

### 7.2 SDK Metrics

| Metric | 3mo | 6mo | 12mo |
|--------|-----|-----|------|
| PyPI downloads/month | 500 | 5,000 | 50,000 |
| npm downloads/month | 500 | 5,000 | 50,000 |
| SDK packages published | 10 | 30 | 100 |

### 7.3 Quality Metrics

| Metric | Target |
|--------|--------|
| CIDL validation pass rate | 100% |
| SDK generation success rate | 100% |
| User-reported bugs/month | <10 |
| Time to merge PR | <48h |

---

## 8. Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Low initial adoption | High | High | Focus on top 10 CLIs, write SDKs ourselves |
| CLI updates break CIDLs | High | Medium | Automated update detection, version pinning |
| Quality inconsistency | Medium | High | Strict validation, review process |
| Maintenance burden | High | Medium | Automation, community ownership |
| Legal/licensing issues | Low | High | Clear contribution license (MIT/Apache) |

---

## 9. Roadmap

### Phase 1: Foundation (Months 1-2)
- [ ] Repository structure
- [ ] CIDL JSON Schema
- [ ] Basic validation tooling
- [ ] First 10 CIDLs (ripgrep, git, docker, curl, ...)
- [ ] Simple web viewer

### Phase 2: Automation (Months 3-4)
- [ ] cidl CLI tool
- [ ] Automated extraction
- [ ] CI/CD pipeline
- [ ] SDK generation and publishing
- [ ] Update detection

### Phase 3: Community (Months 5-6)
- [ ] Contribution documentation
- [ ] PR templates
- [ ] Community guidelines
- [ ] First external contributors
- [ ] 50 CIDLs

### Phase 4: Scale (Months 7-12)
- [ ] API for programmatic access
- [ ] AI tool integrations
- [ ] IDE extensions
- [ ] 200 CIDLs
- [ ] Multi-language SDKs

---

## 10. Appendices

### A. Example Contribution

```yaml
# registry/fd/cidl.yaml
cidl: "1.0"

meta:
  name: fd
  version: "9.0.0"
  description: "A simple, fast and user-friendly alternative to find"
  homepage: "https://github.com/sharkdp/fd"
  license: "MIT OR Apache-2.0"

commands:
  - name: fd
    description: "Find entries in the filesystem"

    positional:
      - name: pattern
        description: "The search pattern (regex or literal)"
        required: false

      - name: path
        description: "The root directory for the search"
        required: false
        multiple: true
        default: "."

    options:
      - name: hidden
        short: H
        type: switch
        description: "Search hidden files and directories"

      - name: no-ignore
        short: I
        type: switch
        description: "Don't respect ignore files"

      - name: type
        short: t
        type: enum
        choices: [f, file, d, directory, l, symlink, s, socket, p, pipe, x, executable, e, empty, b, block-device, c, char-device]
        multiple: true
        description: "Filter by type"

      - name: extension
        short: e
        type: string
        multiple: true
        description: "Filter by file extension"

      - name: max-depth
        short: d
        type: integer
        description: "Maximum search depth"

exit_codes:
  - code: 0
    name: success
    description: "At least one match found"
  - code: 1
    name: no_match
    description: "No matches found"

output:
  formats: [text]
  default_format: text
```

### B. Comparison with DefinitelyTyped Workflow

| Step | DefinitelyTyped | CIDL Registry |
|------|-----------------|---------------|
| 1. Create | `npx dts-gen lodash` | `cidl init lodash` |
| 2. Edit | Edit index.d.ts | Edit cidl.yaml |
| 3. Test | `npm test` | `cidl test` |
| 4. Lint | `dtslint` | `cidl lint` |
| 5. PR | GitHub PR | GitHub PR |
| 6. Review | DT maintainers | CIDL maintainers |
| 7. Publish | Auto to npm @types | Auto to PyPI/npm @cidl |

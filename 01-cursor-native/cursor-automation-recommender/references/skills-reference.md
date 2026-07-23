# Cursor Skills — Reference

Skills are **procedural knowledge bundles** — a `SKILL.md` file plus supporting scripts, templates, and examples. Cursor supports Agent Skills in both the editor (Nightly as of early 2026) and the CLI, using the same `SKILL.md` format as Claude Code. This means skills are portable between the two tools.

## Rules vs Skills — The Core Distinction

| Rules | Skills |
|-------|--------|
| Declarative ("we use Drizzle") | Procedural ("how to add a migration") |
| Always or glob-attached | Loaded on-demand when relevant |
| Text-only | Can bundle scripts, templates, examples |
| Short (<300 lines) | Can be larger, include files |
| Injected into every matching request | Discovered via description matching |

**Heuristic**: If it's a fact → Rule. If it's a how-to with assets → Skill.

## Directory Layout

```
.cursor/
└── skills/
    └── <skill-name>/
        ├── SKILL.md          # Required — frontmatter + instructions
        ├── scripts/          # Optional — runnable scripts
        │   └── validate.sh
        ├── templates/        # Optional — file templates
        │   └── component.tsx
        └── examples/         # Optional — canonical examples
            └── good-example.ts
```

## SKILL.md Frontmatter

```yaml
---
name: skill-name
description: What the skill does AND when the agent should trigger it. Be specific — this is how the agent discovers the skill.
tools: Read, Glob, Grep, Bash    # Optional — scoped tool list
---
```

The `description` is critical: the agent uses it to decide whether to load the skill. Bad: "helps with tests". Good: "Generate unit tests for TypeScript functions when the user asks to add tests, cover a new function, or increase coverage. Includes test templates and fixture examples."

## Recommended Skills by Signal

### `api-doc` — API Documentation
**When**: API routes exist (`app/api/**`, `src/api/**`).
**Why as skill**: Bundles an OpenAPI template and a script that scans routes.

```
.cursor/skills/api-doc/
├── SKILL.md
├── templates/openapi-base.yaml
└── scripts/extract-routes.sh
```

SKILL.md frontmatter:
```yaml
---
name: api-doc
description: Generate or update OpenAPI documentation when the user asks to document the API, add a new endpoint to docs, or check for undocumented routes. Uses the project's OpenAPI template.
---
```

### `create-migration` — Database Migration
**When**: Prisma, Drizzle, or raw SQL migrations present.
**Why as skill**: Has a validation script that checks for destructive operations.

```yaml
---
name: create-migration
description: Create a database migration when the user asks to add, alter, or remove a table/column. Generates the migration file, validates against destructive patterns, and writes the rollback.
---
```

### `new-component` — Component Scaffolding
**When**: Component directory with a consistent structure.
**Why as skill**: Bundles the component template + story + test skeleton.

```
.cursor/skills/new-component/
├── SKILL.md
├── templates/
│   ├── Component.tsx
│   ├── Component.test.tsx
│   └── Component.stories.tsx
```

### `gen-test` — Test Generation
**When**: Test suite exists but coverage is low.
**Why as skill**: Includes example test patterns and mock fixtures.

### `pr-check` — PR Readiness
**When**: Team has a PR checklist in `.github/pull_request_template.md`.
**Why as skill**: Bundles a script that runs lint, test, type-check, and checks the PR template is filled.

### `release-notes` — Release Notes Generator
**When**: Tagged releases in git.
**Why as skill**: Includes a script that parses `git log` since last tag and groups by conventional commit type.

### `grind-until-green` — TDD Loop
**When**: Strong test culture, user wants agent to iterate autonomously.
**Why as skill**: Pairs with a `stop` hook that re-prompts until tests pass.

SKILL.md:
```yaml
---
name: grind-until-green
description: Iteratively implement a feature until all tests pass. Use when the user provides a failing test and asks to make it green, or says "keep going until tests pass".
---

# Grind Until Green

1. Run the test suite: `pnpm test`
2. If failing, analyze failures and patch code
3. Re-run tests
4. Repeat until green or 10 iterations

Pairs with the stop hook in `.cursor/hooks/keep-going.json` that re-prompts when the agent tries to stop with failing tests.
```

### `setup-dev` — Onboarding
**When**: Complex setup (multiple services, env vars, external deps).
**Why as skill**: Runs prereq checks and walks through setup.

## Invocation

Skills are triggered in two ways:

1. **Auto-discovery**: agent reads the description at session start, loads the skill when a matching task appears
2. **Manual**: `/skill-name` in chat

## Writing a Good Description

The description is how the agent finds your skill. Include:

- **What it does** — the action
- **When to use it** — trigger conditions
- **Key signals** — phrases the user might say

Example (bad): "Tests stuff."

Example (good): "Generate unit tests for TypeScript functions. Use when the user asks to 'add tests', 'write tests for', 'cover' a function, or mentions low coverage. Includes mock fixture patterns and the project's testing conventions."

## Skills with Hooks

Skills can reference hooks in the same `.cursor/` tree to enforce behavior:

```markdown
# grind-until-green/SKILL.md

This skill relies on `.cursor/hooks/keep-going.json`:

- A `stop` hook intercepts the agent trying to finish
- Checks test output
- If failing, injects a prompt to continue fixing
```

## Sharing Skills

- Commit `.cursor/skills/` to version control
- Skills are portable — they work in Claude Code with the same format
- Reference community skills in your team's onboarding doc

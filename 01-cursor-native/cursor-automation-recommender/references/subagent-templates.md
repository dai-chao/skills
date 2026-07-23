# Cursor Subagents — Templates

Subagents are independent agents with their own context, tools, and model. They run in parallel with the main agent and return focused results. Introduced in Cursor 2.4.

## Why Subagents?

- **Focused context**: the main agent's window stays clean
- **Parallelism**: research + implementation at once
- **Specialization**: dedicated model and tools per role
- **Cost**: smaller specialized agents can use cheaper models

Cursor ships default subagents for codebase research, terminal commands, and parallel work streams. You can add custom ones.

## Config Location

`.cursor/agents/<name>.md` — one agent per file.

## Subagent File Shape

```markdown
---
name: security-reviewer
description: Review code changes for security issues. Use when touching auth, payments, user input handling, or crypto.
tools: Read, Grep, Glob        # scoped tool list
model: claude-opus-4.7         # optional model override
---

# Security Reviewer

You are a security-focused code reviewer. Your job is to identify:

1. **Injection risks** — SQL, command, XSS, SSRF
2. **Auth flaws** — missing checks, IDOR, broken access control
3. **Secrets** — hardcoded keys, logged PII, insecure storage
4. **Cryptography** — weak algorithms, nonce reuse, timing attacks
5. **Dependency risks** — known CVEs in added packages

## How to Review

- Read the diff or file provided
- List findings as: `[severity] file:line — issue — suggested fix`
- Be specific and actionable
- Do not approve — only report

## Output Format

```
## Security Review

### Critical
- [none | findings]

### High
- [findings]

### Medium / Low
- [findings]

### Summary
[1-2 sentences]
```
```

## Recommended Subagents by Signal

### `codebase-researcher`
**Signal**: Large codebase (>500 files), onboarding, architectural questions.
**Purpose**: Explores the codebase in parallel while main agent works.
```yaml
---
name: codebase-researcher
description: Explore the codebase to answer questions about structure, patterns, and cross-file relationships. Use when the main agent needs background on "how does X work" or "where is Y implemented".
tools: Read, Grep, Glob
---
```

### `security-reviewer`
**Signal**: Auth code, payments, user input, crypto.
**Purpose**: Parallel security audit while feature is being built.

### `api-documenter`
**Signal**: API routes without OpenAPI spec.
**Purpose**: Generates/updates OpenAPI specs in the background.
```yaml
---
name: api-documenter
description: Generate OpenAPI documentation for API routes. Use after adding or modifying endpoints.
tools: Read, Write, Grep, Glob
---
```

### `performance-analyzer`
**Signal**: Performance-critical code (hot paths, DB queries, render loops).
**Purpose**: Identifies bottlenecks without derailing the main task.
```yaml
---
name: performance-analyzer
description: Analyze code for performance bottlenecks — N+1 queries, unnecessary re-renders, blocking I/O, inefficient algorithms. Use when working on hot paths or when the user mentions perf.
tools: Read, Grep, Glob, Bash
---
```

### `ui-reviewer`
**Signal**: Frontend heavy, accessibility requirements.
**Purpose**: Checks a11y, responsive patterns, component API consistency.
```yaml
---
name: ui-reviewer
description: Review React/Vue components for accessibility (ARIA, keyboard nav, contrast), responsive behavior, and consistency with the component library. Use after component creation or changes.
tools: Read, Grep, Glob
---
```

### `test-writer`
**Signal**: Low coverage, missing test files.
**Purpose**: Generates tests in parallel with feature work.
```yaml
---
name: test-writer
description: Write unit and integration tests for recently added code. Use after a feature is implemented to add coverage.
tools: Read, Write, Edit, Grep, Glob, Bash
---
```

### `debug-hypothesizer`
**Signal**: Bug-fixing session, unclear root cause.
**Purpose**: Generates hypotheses, adds log statements to test them.
```yaml
---
name: debug-hypothesizer
description: Generate and test hypotheses about bug root causes. Use when the cause of a bug is not obvious and reproducing it is expensive.
tools: Read, Edit, Grep, Glob, Bash
---
```

### `migration-runner`
**Signal**: Large refactor (e.g., class → hooks, JS → TS).
**Purpose**: Applies mechanical changes in parallel while main agent handles judgment calls.

### `docs-sync`
**Signal**: Docs drift (README out of date).
**Purpose**: Keeps README, CHANGELOG, and inline docs in sync with code.

## Writing Good Subagents

### Do
- **Narrow scope**: one clear responsibility
- **Specify output format**: agents produce more consistent output with a schema
- **Scope tools tightly**: `security-reviewer` should be `Read, Grep, Glob` — no `Write`
- **Use cheap models** for research/review roles; save premium models for main agent

### Don't
- **Overlap with main agent**: if the main agent does it well, no need for a subagent
- **Allow write tools on reviewers**: reviewers should report, not fix
- **Give all subagents the same description**: vague descriptions = no dispatch

## Invocation

- **Automatic**: the main agent dispatches to subagents when their description matches
- **Manual**: `@subagent-name` in chat, or `/subagent-name` slash command

## Parallelism

Cursor 3.0+ allows 1x–6x (up to 8x) parallel subagent runs. Useful for:
- `/best-of-n` — same task, multiple models, compare outputs
- Reviewing N files in parallel
- Multi-service monorepo tasks

## Sharing

Commit `.cursor/agents/` to version control — the team gets the same specialists.

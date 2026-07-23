# Cursor Rules — Reference

Rules are persistent instructions injected into the agent's context. They are the most impactful configuration in Cursor — good rules mean the AI generates code that matches your conventions on the first try.

## Formats

### Modern: `.cursor/rules/*.mdc` (recommended)
- One `.mdc` file per concern
- YAML frontmatter controls scoping and activation
- Supports `@file.ts` references to bundle code as context
- Can be nested: `apps/web/.cursor/rules/` for workspace-specific rules

### Legacy: `.cursorrules` (deprecated but still works)
- Single Markdown file at repo root
- Always injected on every request
- Migrate to `.cursor/rules/` for better scoping

## Rule Types (via frontmatter)

| Type | Frontmatter | Behavior |
|------|-------------|----------|
| **Always** | `alwaysApply: true` | Injected every request. Keep minimal. |
| **Auto Attached** | `globs: ["src/**/*.ts"]` | Loaded when matching files enter context |
| **Agent Requested** | `description: "..."` (no globs, no alwaysApply) | Agent pulls in when it thinks relevant |
| **Manual** | No description, no globs, no alwaysApply | Only loaded when `@rule-name` referenced |

## Directory Layout (recommended)

```
.cursor/
└── rules/
    ├── core.mdc              # Always — tech stack, non-negotiables (<300 lines)
    ├── typescript.mdc        # Auto Attached — *.ts, *.tsx
    ├── frontend.mdc          # Auto Attached — src/components/**, src/app/**
    ├── api.mdc               # Auto Attached — src/api/**, app/api/**
    ├── db.mdc                # Auto Attached — prisma/**, db/**
    ├── testing.mdc           # Auto Attached — *.test.*, *.spec.*
    ├── security.mdc          # Always — safety guardrails
    └── personal.mdc          # Gitignored — local overrides
```

## Templates

### core.mdc (Always)
```yaml
---
alwaysApply: true
description: "Core project conventions"
---
# [Project Name] — Core Rules

## Tech Stack
- [framework + version]
- [language + strict mode settings]
- [styling system]
- [ORM / data layer]
- [package manager — pnpm/npm/yarn]

## Non-Negotiables
- Use [X] not [Y] (e.g., Drizzle, not Prisma)
- [Import alias] = [src/]
- Named exports only — never default exports
- [Error handling pattern]

## Don'ts
- Never suggest [deprecated pattern]
- Never modify files in [generated dir]
```

### typescript.mdc (Auto Attached)
```yaml
---
description: "TypeScript conventions"
globs:
  - "**/*.ts"
  - "**/*.tsx"
---
# TypeScript Rules
- Strict mode — no `any`. Use `unknown` + type guards.
- Prefer `type` for unions, `interface` for object shapes that extend.
- All async functions must use try/catch.
- Use `satisfies` for config objects.
- Zod for runtime validation; derive types with `z.infer`.

## Error Handling Pattern
```typescript
try {
  const result = await op()
  return { data: result, error: null }
} catch (error) {
  logger.error('op failed', { error })
  return { data: null, error: error instanceof Error ? error.message : 'Unknown' }
}
```
```

### frontend.mdc (Auto Attached — Next.js example)
```yaml
---
description: "Next.js 15 App Router conventions"
globs:
  - "src/app/**"
  - "src/components/**"
---
# Frontend Rules
- App Router only — never suggest Pages Router
- Server Components by default; add `'use client'` only when needed
- Tailwind for styling — no inline styles, no CSS modules
- shadcn/ui for primitives — never modify `components/ui/*` directly
- Use `cn()` from `@/lib/utils` for conditional classes
- Loading states via `loading.tsx`; errors via `error.tsx`

## Reference
See @src/components/UserCard.tsx for the canonical component shape.
```

### api.mdc (Auto Attached)
```yaml
---
description: "API route conventions"
globs:
  - "app/api/**"
  - "src/api/**"
---
# API Rules
- Validate all inputs with Zod before use
- Return `{ data, error }` envelope — never throw to client
- Auth check first line of every handler
- Use `NextResponse.json()` for responses
- Log structured: `{ route, userId, duration }`
```

### testing.mdc (Auto Attached)
```yaml
---
description: "Testing conventions"
globs:
  - "**/*.test.ts"
  - "**/*.spec.ts"
  - "**/*.test.tsx"
---
# Testing Rules
- [Framework] (Jest/Vitest) with [test-library]
- Describe blocks per exported function
- Arrange-Act-Assert structure
- Mock at the module boundary, not internals
- No snapshot tests for logic — only for stable UI
```

### security.mdc (Always)
```yaml
---
alwaysApply: true
description: "Security guardrails"
---
# Security Rules
- Never suggest hardcoded secrets or API keys
- Never log request bodies containing PII
- Always validate/sanitize user input before DB or HTML
- Never build SQL with string concatenation — use parameterized queries
- Check auth before data access in every handler
```

## Writing Good Rules

### Do
- **Be specific and actionable**: "Use `pnpm` not `npm`" > "use the right package manager"
- **Show examples**: reference files with `@components/UserCard.tsx`
- **Explain the "why"** for non-obvious constraints (helps the AI reason about edge cases)
- **Scope narrowly**: don't put frontend rules in a rule that also matches backend files
- **Keep core.mdc short** (<300 lines) — every token costs

### Don't
- **Vague guidance**: "write clean code" is useless
- **Contradictions**: if two rules conflict, the AI will pick randomly
- **Dumping docs**: rules are not documentation — they are *enforcement*
- **Over-scope with `alwaysApply`**: makes every request more expensive

## Generating Rules

- `/Generate Cursor Rules` in chat — turns current conversation decisions into rules
- After correcting the AI 3+ times on the same mistake, write a rule for it
- Community starter packs: [awesome-cursorrules](https://github.com/PatrickJS/awesome-cursorrules), Agent Rules Builder

## Team Sharing

- Commit `.cursor/rules/` to version control
- Gitignore only personal overrides (`personal.mdc`)
- Team/Enterprise plans support admin-enforced Team Rules via dashboard

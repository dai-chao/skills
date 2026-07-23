---
name: cursor-automation-recommender
description: Analyze a codebase and recommend Cursor automations (rules, skills, hooks, subagents, custom modes, MCP servers, automations). Use when user asks for automation recommendations, wants to optimize their Cursor setup, mentions improving Cursor workflows, asks how to first set up Cursor for a project, or wants to know what Cursor features they should use.
tools: Read, Glob, Grep, Bash
---

# Cursor Automation Recommender

Analyze codebase patterns to recommend tailored Cursor automations across all extensibility options.

**This skill is read-only.** It analyzes the codebase and outputs recommendations. It does NOT create or modify any files. Users implement the recommendations themselves or ask Cursor separately to help build them.

## Output Guidelines

- **Recommend 1-2 of each type**: Don't overwhelm - surface the top 1-2 most valuable automations per category
- **If user asks for a specific type**: Focus only on that type and provide more options (3-5 recommendations)
- **Go beyond the reference lists**: The reference files contain common patterns, but use web search to find recommendations specific to the codebase's tools, frameworks, and libraries
- **Tell users they can ask for more**: End by noting they can request more recommendations for any specific category

## Automation Types Overview

| Type | Best For | Location |
|------|----------|----------|
| **Rules** | Persistent coding conventions, tech stack context, style guides | `.cursor/rules/*.mdc` |
| **Skills** | Packaged workflows, scripts, templates loaded on-demand | `.cursor/skills/<name>/SKILL.md` |
| **Hooks** | Automatic actions on agent lifecycle events (format, lint, block edits) | `.cursor/hooks/` |
| **Subagents** | Specialized reviewers/analyzers that run in parallel with focused context | `.cursor/agents/` |
| **Custom Modes** | Curated tool + model + prompt combos for specific workflows | Settings → Modes |
| **MCP Servers** | External tool integrations (databases, APIs, browsers, docs) | `.cursor/mcp.json` |
| **Automations** | Scheduled or event-triggered cloud agent runs | Cursor Dashboard |

> **Note**: Notepads were deprecated in Cursor 2.0. Use Rules for persistent context instead.

## Workflow

### Phase 1: Codebase Analysis

Gather project context:

```bash
# Detect project type and tools
ls -la package.json pyproject.toml Cargo.toml go.mod pom.xml 2>/dev/null
cat package.json 2>/dev/null | head -50

# Check dependencies for MCP server recommendations
cat package.json 2>/dev/null | grep -E '"(react|vue|angular|next|express|fastapi|django|prisma|supabase|stripe)"'

# Check for existing Cursor config
ls -la .cursor/ .cursorrules .cursorignore AGENTS.md 2>/dev/null
ls -la .cursor/rules/ .cursor/skills/ .cursor/hooks/ .cursor/agents/ 2>/dev/null

# Analyze project structure
ls -la src/ app/ lib/ tests/ components/ pages/ api/ 2>/dev/null
```

**Key Indicators to Capture:**

| Category | What to Look For | Informs Recommendations For |
|----------|------------------|----------------------------|
| Language/Framework | package.json, pyproject.toml, import patterns | Rules, hooks, MCP servers |
| Frontend stack | React, Vue, Angular, Next.js | Playwright MCP, frontend rules |
| Backend stack | Express, FastAPI, Django | API rules, doc tools |
| Database | Prisma, Supabase, raw SQL | Database MCP servers |
| External APIs | Stripe, OpenAI, AWS SDKs | context7 MCP for docs |
| Testing | Jest, pytest, Playwright configs | Test hooks, subagents |
| CI/CD | GitHub Actions, CircleCI | GitHub MCP server |
| Issue tracking | Linear, Jira references | Issue tracker MCP |
| Monorepo | pnpm workspaces, turbo, nx | Scoped rules per workspace |
| Existing `.cursorrules` (legacy) | Single root file | Suggest migration to `.cursor/rules/` |

### Phase 2: Generate Recommendations

Based on analysis, generate recommendations across all categories:

#### A. MCP Server Recommendations

See [references/mcp-servers.md](references/mcp-servers.md) for detailed patterns.

| Codebase Signal | Recommended MCP Server |
|-----------------|------------------------|
| Uses popular libraries (React, Express, etc.) | **context7** - Live version-specific documentation lookup |
| Frontend with UI testing needs | **Playwright** - Browser automation/testing |
| Uses Supabase | **Supabase MCP** - Direct database operations |
| PostgreSQL/MySQL database | **Postgres/MySQL MCP** - Query and schema tools |
| GitHub repository | **GitHub MCP** - Issues, PRs, actions |
| Uses Linear for issues | **Linear MCP** - Issue management |
| Uses Jira | **Atlassian MCP** - Ticket context |
| AWS infrastructure | **AWS MCP** - Cloud resource management |
| Uses Figma for design | **Figma MCP** - Design-to-code |
| Sentry error tracking | **Sentry MCP** - Error investigation |
| Uses Notion for docs | **Notion MCP** - Knowledge retrieval |
| Docker containers | **Docker MCP** - Container management |

> **⚠️ Cursor constraint**: Cursor has a ~40 active tool limit across all MCP servers combined. Recommend enabling only the tools you need per server, and prefer a few focused servers over many megaservers.

#### B. Rules Recommendations

See [references/rules-reference.md](references/rules-reference.md) for details.

Rules live in `.cursor/rules/*.mdc` (the modern format). Legacy `.cursorrules` still works but is deprecated.

**Rule types** (set via frontmatter):
- **Always** (`alwaysApply: true`) — injected every request. Use sparingly.
- **Auto Attached** (`globs:`) — loaded when matching files are in context.
- **Agent Requested** (`description:`) — agent pulls in when relevant.
- **Manual** — only when `@rule-name` is referenced explicitly.

| Codebase Signal | Rule File to Create | Type |
|-----------------|---------------------|------|
| Any project | **core.mdc** (tech stack, non-negotiables) | Always |
| TypeScript project | **typescript.mdc** (strict mode, no `any`, type guards) | Auto Attached (`**/*.ts`, `**/*.tsx`) |
| React/Next.js | **frontend.mdc** (component patterns, Server vs Client) | Auto Attached (`src/app/**`, `src/components/**`) |
| API routes | **api.mdc** (validation, error envelopes, auth) | Auto Attached (`src/api/**`, `app/api/**`) |
| Database project | **db.mdc** (migration rules, ORM conventions) | Auto Attached (`prisma/**`, `db/**`) |
| Test suite | **testing.mdc** (TDD loop, test naming, mocking) | Auto Attached (`**/*.test.*`, `**/*.spec.*`) |
| Security-sensitive | **security.mdc** (no hardcoded secrets, input validation) | Always |
| Monorepo | Per-workspace rules in `apps/*/`.cursor/rules/` | Auto Attached scoped |

#### C. Skills Recommendations

See [references/skills-reference.md](references/skills-reference.md) for details.

Skills live in `.cursor/skills/<name>/SKILL.md` (same format as Claude Code skills — portable). They are loaded **on-demand** when the agent decides they're relevant, keeping context clean.

> **Availability note**: Skills are currently in the Nightly channel for the editor; fully supported in Cursor CLI.

| Codebase Signal | Skill to Create | Why Skill (vs Rule) |
|-----------------|-----------------|---------------------|
| API routes | **api-doc** (OpenAPI template + script) | Procedural, not always needed |
| Database project | **create-migration** (validation script) | Bundles a runnable script |
| Test suite | **gen-test** (example tests + fixtures) | Needs templates/fixtures |
| Component library | **new-component** (templates + folder scaffolding) | Bundles files, not just text |
| PR workflow | **pr-check** (checklist + hook to block) | Has a hook integration |
| Releases | **release-notes** (git log parser script) | Procedural with tooling |
| TDD workflow | **grind-until-green** (hook loop until tests pass) | Long-running procedural loop |

#### D. Hooks Recommendations

See [references/hooks-patterns.md](references/hooks-patterns.md) for configurations.

Cursor supports these hook events (Cursor 2.4+): `sessionStart`, `sessionEnd`, `beforeSubmitPrompt`, `PreToolUse`, `PostToolUse`, `stop`. Config lives in `.cursor/hooks/` and is Claude Code-compatible.

| Codebase Signal | Recommended Hook | Event |
|-----------------|------------------|-------|
| Prettier configured | Auto-format on edit | PostToolUse (on Edit/Write) |
| ESLint/Ruff configured | Auto-lint on edit | PostToolUse |
| TypeScript project | Type-check on edit | PostToolUse |
| Tests directory exists | Run related tests | PostToolUse |
| `.env` files present | Block `.env` edits | PreToolUse |
| Lock files present | Block lock file edits | PreToolUse |
| Secret scanning | Reject prompts containing API keys | beforeSubmitPrompt |
| TDD workflow | Loop until tests pass | stop |

#### E. Subagent Recommendations

See [references/subagent-templates.md](references/subagent-templates.md) for templates.

Cursor 2.4+ supports custom subagents — independent agents with their own context, tools, and model. Define in `.cursor/agents/<name>.md`.

| Codebase Signal | Recommended Subagent | Runs In Parallel With |
|-----------------|---------------------|----------------------|
| Large codebase (>500 files) | **codebase-researcher** | Main agent exploration |
| Auth/payments code | **security-reviewer** | Feature work |
| API project | **api-documenter** | Endpoint implementation |
| Performance critical | **performance-analyzer** | Refactors |
| Frontend heavy | **ui-reviewer** (accessibility, responsive) | Component work |
| Needs more tests | **test-writer** | Feature work |
| Complex debugging | **debug-hypothesizer** | Bug fixes |

#### F. Custom Mode Recommendations

Custom Modes bundle a system prompt, tool allowlist, and model choice for a specific workflow. Configure in Cursor Settings → Modes.

| Codebase Signal | Recommended Mode |
|-----------------|------------------|
| Heavy refactor work | **Refactor Mode** — Plan Mode + read-heavy tools + Opus/high-effort model |
| Docs-first workflow | **Docs Mode** — Write-only to `docs/`, no terminal |
| Learning codebase | **Explain Mode** — Read-only, verbose explanations, no edits |
| Production fixes | **Hotfix Mode** — Tight tool set, mandatory test run, no new deps |

#### G. Automation Recommendations (Cloud Agents)

Cursor Automations trigger cloud agents on schedules or external events.

| Codebase Signal | Recommended Automation |
|-----------------|------------------------|
| Active GitHub repo | **Bugbot Autofix** — auto-proposes fixes on PR issues |
| Dependency-heavy | **Weekly dep-update agent** — scheduled patch bumps + tests |
| Issue backlog | **Linear/GitHub triage agent** — nightly label & triage |
| Flaky tests | **Nightly test-stabilizer** — identifies flakes, proposes fixes |
| Docs drift | **Weekly docs-sync agent** — regenerates API docs from code |

### Phase 3: Output Recommendations Report

Format recommendations clearly. **Only include 1-2 recommendations per category** — the most valuable ones for this specific codebase. Skip categories that aren't relevant.

```markdown
## Cursor Automation Recommendations

I've analyzed your codebase and identified the top automations for each category. Here are my top 1-2 recommendations per type:

### Codebase Profile
- **Type**: [detected language/runtime]
- **Framework**: [detected framework]
- **Key Libraries**: [relevant libraries detected]
- **Existing Cursor setup**: [none | legacy .cursorrules | .cursor/ present]

---

### 📐 Rules

#### [rule name].mdc
**Why**: [specific reason based on detected patterns]
**Where**: `.cursor/rules/[name].mdc`
**Type**: Always / Auto Attached / Agent Requested / Manual

```yaml
---
description: [short description]
globs:
  - "src/**/*.ts"
alwaysApply: false
---
# [Rule title]
- [concrete instruction]
- [concrete instruction]
```

---

### 🎯 Skills

#### [skill name]
**Why**: [specific reason — procedural, bundles scripts/templates]
**Where**: `.cursor/skills/[name]/SKILL.md`
**Invocation**: Auto / `/skill-name`

```yaml
---
name: [skill-name]
description: [what it does and when to use it]
---
```

---

### ⚡ Hooks

#### [hook name]
**Why**: [specific reason based on detected config]
**Event**: PreToolUse / PostToolUse / beforeSubmitPrompt / stop
**Where**: `.cursor/hooks/[name].json`

---

### 🤖 Subagents

#### [agent name]
**Why**: [specific reason based on codebase patterns]
**Where**: `.cursor/agents/[name].md`

---

### 🔌 MCP Servers

#### [server name]
**Why**: [specific reason based on detected libraries]
**Where**: `.cursor/mcp.json`

```json
{
  "mcpServers": {
    "[name]": {
      "command": "npx",
      "args": ["-y", "[package]"]
    }
  }
}
```

---

### 🎛️ Custom Modes

#### [mode name]
**Why**: [specific workflow reason]
**Where**: Cursor Settings → Modes → New Mode

---

### ☁️ Automations

#### [automation name]
**Why**: [specific reason]
**Where**: Cursor Dashboard → Automations

---

**Want more?** Ask for additional recommendations for any specific category (e.g., "show me more MCP server options" or "what other hooks would help?").

**Want help implementing any of these?** Just ask and I can help you set up any of the recommendations above.
```

## Decision Framework

### Rules vs Skills — Which to Use?
This is the most common confusion in Cursor. Quick heuristic:
- **Rules** = *always-known facts* ("we use Drizzle, not Prisma"). Declarative, short, always (or glob-attached) in context.
- **Skills** = *procedures with assets* ("how to add a new component, including the template file"). Dynamic, loaded on-demand, can bundle scripts/templates.

If it's text-only and short → Rule. If it bundles files, scripts, or is a multi-step workflow → Skill.

### When to Recommend MCP Servers
- External service integration (databases, APIs, design tools)
- Documentation lookup for libraries/SDKs (context7)
- Browser automation or E2E testing
- Team tool integration (GitHub, Linear, Slack)
- **Always warn about the 40-tool cap** if recommending 3+ servers

### When to Recommend Rules
- Project has conventions the AI keeps violating
- Specific tech choices (ORM, styling, package manager) to enforce
- File-type-specific patterns (only React components, only API routes)
- Security/safety guardrails that should always apply

### When to Recommend Skills
- Repeatable workflows with supporting files (templates, scripts)
- Procedural tasks the agent should "know how to do"
- Loops or agent harness patterns (e.g., grind-until-green)
- Cross-project portable procedures

### When to Recommend Hooks
- Repetitive post-edit actions (formatting, linting, type-checking)
- Protection rules (block sensitive file edits)
- Validation gates (tests must pass before stop)
- Secret scanning on prompts

### When to Recommend Subagents
- Large codebase where parallel exploration pays off
- Specialized expertise needed (security, performance, docs)
- Background quality checks that shouldn't pollute main context

### When to Recommend Custom Modes
- Team has distinct workflows that need different tool sets
- Want to enforce a model/tool combo for specific tasks
- Safety-critical operations need a locked-down environment

### When to Recommend Automations
- Team has a GitHub repo with active PRs
- Recurring manual tasks (triage, dep bumps, test stabilization)
- Off-hours work that benefits from cloud execution

---

## Configuration Tips

### Team Sharing

- **`.cursor/rules/`** — commit to repo; team gets same rules automatically
- **`.cursor/skills/`** — commit to repo; skills are portable with Claude Code
- **`.cursor/mcp.json`** — commit project-specific servers; use env vars for credentials
- **`.cursor/hooks/`** — commit to repo for team-wide enforcement
- **`.cursor/agents/`** — commit to repo for shared subagents
- **`.gitignore`**: exclude `.cursor/rules/personal.mdc` for local overrides

### Cursor CLI (Headless)

Recommend Cursor CLI for CI/automation pipelines:

```bash
# Pre-commit hook example
cursor-agent -p "fix lint errors in src/" --allowedTools Edit

# Resume a session
cursor-agent --resume=-1
```

### MCP Prerequisites

Before recommending MCP servers, check:
- **Node.js / npx available** — required for most MCP servers
- **Python available** — for Python-based servers
- **GitHub CLI (`gh`)** — makes GitHub MCP more capable
- **Read-only credentials** — recommend read-only DB users and scoped GitHub tokens

### `.cursorignore` Hygiene

If the project is large (>50K files) or has secrets, recommend adding a `.cursorignore`:

```
node_modules/
.env*
*.log
dist/
.next/
```

### Legacy Migration

If the project has a root `.cursorrules` file:
1. Flag it as deprecated
2. Suggest splitting into focused `.cursor/rules/*.mdc` files
3. Use `alwaysApply: true` on the core rule to preserve old behavior initially

### Pinning MCP Versions

Recommend pinning versions (`npx -y pkg@1.2.3` not `@latest`) — a compromised `latest` tag is a real supply-chain risk in the MCP ecosystem.

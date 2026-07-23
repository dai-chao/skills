# MCP Servers for Cursor — Reference

MCP servers in Cursor use the same protocol as Claude Code and Claude Desktop — servers are interchangeable. Cursor reads MCP configs from:

- **Project**: `.cursor/mcp.json` (check into repo)
- **Global**: `~/.cursor/mcp.json` (per-user)

## Important Constraints

- **~40 active tool cap** across all MCP servers combined. Exceed this and the agent silently loses access to some tools. Disable tools you don't use per server.
- **Token cost**: every connected server's full schema is injected at session boot. Prefer focused servers over megaservers.
- **Pin versions**: use `npx -y pkg@1.2.3`, not `@latest`, to avoid supply-chain attacks.
- **Least privilege**: read-only DB users, scoped GitHub tokens, etc.

## Base Config Shape

### stdio (most common)
```json
{
  "mcpServers": {
    "server-name": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-name"],
      "env": { "API_KEY": "${MY_API_KEY}" }
    }
  }
}
```

### Remote (HTTP/SSE)
```json
{
  "mcpServers": {
    "remote": {
      "url": "https://mcp.example.com/mcp",
      "headers": { "Authorization": "Bearer ${TOKEN}" }
    }
  }
}
```

## Recommended Servers by Signal

### Documentation — context7
**When**: Project uses popular libraries (React, Next, Express, Prisma, Stripe SDK, AWS SDK, etc.)
**Why**: Live version-specific docs — avoids hallucinated API signatures.
```json
{ "context7": { "command": "npx", "args": ["-y", "@upstash/context7-mcp"] } }
```

### Database — Postgres
**When**: `DATABASE_URL` present, `prisma/`, `drizzle/`, or raw SQL files detected.
**Why**: Schema-aware queries, natural-language SQL.
```json
{
  "postgres": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-postgres"],
    "env": { "DATABASE_URL": "postgresql://readonly:pass@host/db" }
  }
}
```
> Always recommend a **read-only** DB user unless the user explicitly wants writes.

### Database — Supabase
**When**: `@supabase/supabase-js` in deps or `supabase/` directory.
**Why**: Direct table queries, RPC calls, migrations.
```json
{
  "supabase": {
    "command": "npx",
    "args": ["-y", "@supabase/mcp-server-supabase@latest"],
    "env": { "SUPABASE_ACCESS_TOKEN": "${TOKEN}" }
  }
}
```

### Browser — Playwright
**When**: Frontend project, Playwright configured, or UI testing needed.
**Why**: Automated browser actions, E2E tests, visual verification.
```json
{
  "playwright": {
    "command": "npx",
    "args": ["-y", "@executeautomation/playwright-mcp-server"]
  }
}
```

### GitHub — GitHub MCP
**When**: `.git/` + GitHub remote.
**Why**: Issues, PRs, Actions, code search — without leaving Cursor.
```json
{
  "github": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-github"],
    "env": { "GITHUB_PERSONAL_ACCESS_TOKEN": "${GH_TOKEN}" }
  }
}
```

### Issue Tracking — Linear
**When**: References to Linear in code, commits, or docs.
**Why**: Pull ticket context directly into prompts.
```json
{
  "linear": { "url": "https://mcp.linear.app/sse" }
}
```

### Issue Tracking — Atlassian (Jira/Confluence)
**When**: Jira ticket IDs in commits (e.g., `ABC-1234`), Confluence docs.
**Why**: Ticket and doc context without tab-switching.

### Design — Figma
**When**: Frontend project, design tokens, mentions of Figma in README/PRs.
**Why**: Design-to-code, design token extraction.
```json
{
  "figma": {
    "command": "npx",
    "args": ["-y", "figma-developer-mcp", "--figma-api-key=${FIGMA_KEY}", "--stdio"]
  }
}
```

### Errors — Sentry
**When**: `@sentry/*` in deps.
**Why**: Pull stack traces, breadcrumbs, user context into bug-fix prompts.

### Infrastructure — AWS
**When**: AWS SDK deps, `serverless.yml`, CDK, Terraform with AWS provider.
**Why**: Resource inspection, log queries.

### Docs — Notion / Confluence / Google Drive
**When**: Team uses these for internal docs and references them in issues.
**Why**: Pull internal knowledge (design docs, RFCs) into prompts.

### Memory — Memory MCP
**When**: Long-running project, multi-session workflows.
**Why**: Knowledge-graph memory that persists across sessions.
```json
{
  "memory": { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-memory"] }
}
```

### Web Search — Brave / Exa
**When**: Research-heavy work, API integration tasks, new-library exploration.
**Why**: Real-time web data (complements context7 which is docs-only).

### Filesystem — Filesystem MCP
**When**: Need to access files outside the workspace (e.g., shared assets directory).
**Why**: Explicit read/write access to specific directories.
> Use sparingly — scope to specific directories only.

### Docker
**When**: `Dockerfile`, `docker-compose.yml` present, containerized dev.
**Why**: Container inspection, log tailing, exec without leaving Cursor.

## Recommendation Patterns

### Solo dev, small project
1 server: **context7** (docs for the libraries you use).

### Frontend team
3 servers: **context7** + **Playwright** + **Figma**.

### Full-stack web app
4 servers: **context7** + **Postgres/Supabase** + **GitHub** + **Sentry**.

### Infra-heavy
3 servers: **AWS** + **Docker** + **GitHub**.

## Debugging

- Check server status: Cursor Settings → Tools & MCP. Green = loaded, red = failed.
- Common failures: Node/Python not on PATH, missing env vars, Cursor not inheriting shell env (define explicitly in `env`).
- Launch Cursor with `--mcp-debug` (or equivalent) to surface errors.
- On macOS: grant Cursor Full Disk Access if server needs paths outside home dir.

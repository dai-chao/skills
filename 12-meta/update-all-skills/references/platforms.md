# Platforms & behavior

本 skill / 脚本按 **skills.sh 生态约定** 扫描并尽力更新各 Agent 上的 skills。未安装的平台自动跳过。

## Global skill roots（用户级）

| Agent | skills.sh id | Global path | Project path |
|-------|--------------|-------------|--------------|
| **Cursor** | `cursor` | `~/.cursor/skills/` | `.cursor/skills/` |
| **Claude Code** | `claude-code` | `~/.claude/skills/` | `.claude/skills/` |
| **Codex** | `codex` | `~/.codex/skills/`（含 `.system/` 托管） | `.agents/skills/` |
| **Hermes Agent** | `hermes` | `~/.hermes/skills/` | — |
| **Gemini CLI** | `gemini-cli` | `~/.gemini/skills/` | `.agents/skills/` |
| **Antigravity** | `antigravity` | `~/.gemini/antigravity/skills/` | `.agents/skills/` |
| **Antigravity CLI** | `antigravity-cli` | `~/.gemini/antigravity-cli/skills/` | `.agents/skills/` |
| **Trae** | `trae` | `~/.trae/skills/` | `.trae/skills/` |
| **Trae 国内版** | `trae-cn` | `~/.trae-cn/skills/` | `.trae/skills/` |
| **GitHub Copilot** | `github-copilot` | `~/.copilot/skills/` | `.agents/skills/` |
| **GitHub Copilot AppMod** | — | `~/.ghcp-appmod/skills/` | — |
| **OpenCode** | `opencode` | `~/.config/opencode/skills/` | `.agents/skills/` 或 `.opencode/skills/` |
| **Windsurf** | `windsurf` | `~/.codeium/windsurf/skills/` | `.windsurf/skills/` |
| **Crush** | `crush` | `~/.config/crush/skills/` | `.crush/skills/` |
| **Deep Agents** | `deepagents` | `~/.deepagents/agent/skills/` | `.agents/skills/` |
| **OpenClaw** | — | `~/.openclaw/skills/` | — |
| **通用共享** | — | `~/.agents/skills/` | `.agents/skills/` |

`~/.agents/skills/` 是多 Agent 共享目录（skills.sh / Agent Reach 常写这里；Cursor、Codex、Gemini、Copilot、OpenCode、Antigravity 等都会读）。

Never writes into `~/.cursor/skills-cursor/`（Cursor 内置，系统托管）。

## Project-level roots（仓库内）

脚本会在 `~/Desktop`、`~/Documents`、`~/Projects`、`~/dev`、`~/code`、`~/src` 以及当前 `$PWD` 下浅扫：

- `.cursor/skills/`
- `.claude/skills/`
- `.trae/skills/`
- `.agents/skills/`
- `.opencode/skills/`
- `.windsurf/skills/`
- `.crush/skills/`

若项目根有 `skills-lock.json`，会对该项目执行 `skills update -p -y`。

## Update channels（脚本实际做什么）

| Channel | Action |
|---------|--------|
| **skills.sh** | `skills` / `npx skills` → `update -g -y`（覆盖其 lock 跟踪、装到各 Agent 目录的包） |
| **Hermes** | `hermes skills check\|update`；默认再 `hermes update` 同步 bundled |
| **Claude Code** | `claude plugin marketplace update` + 已装 plugin 更新 + marketplace `git pull` |
| **Agent Reach** | 升级包 + `skill --install`（若已装） |
| **远端包** | 若目录存在：刷新 43chat / 43comic / 43farm / 43swap / 才虫 |
| **Git skills** | 对上表各 global root 下带 `.git` 的 skill 目录 `git pull --ff-only` |
| **Inventory** | 统计各 root 的 `SKILL.md` 数量；列出无法自动更新的本地拷贝 |

## CLI prerequisites（optional）

| Tool | Used for |
|------|----------|
| `npx` or `skills` | skills.sh global / project update（多 Agent） |
| `hermes` | Hermes hub + bundled sync |
| `claude` | Claude marketplace / plugins |
| `agent-reach` or `~/.agent-reach-venv` | Agent Reach 包 + skill 重注册 |
| `git` | marketplace / git-cloned skills |
| `curl` | remote skill packs |
| `python3` | JSON summary |

Missing tools are skipped, not fatal. Trae / Gemini / Windsurf 等若无独立 update CLI，依赖 **skills.sh update**、**git pull** 或远端刷新。

## Reports

- Text: `~/.cache/update-all-skills/last-report.txt`
- JSON: `~/.cache/update-all-skills/last-summary.json`

JSON fields: `ok`, `warn`, `fail`, `skip`, `counts`（按平台 root）, `results[]`.

## Limits

- 纯 `cp` 安装、无 hub / skills-lock / git / 已知 URL 的 skill **无法自动更新**，脚本只盘点。
- Claude plugins 在 marketplace 更名后可能报 “not found”；marketplace git pull 仍会刷新源码。
- 43* / 才虫 仅在 `~/.hermes/skills/` 下已有对应目录时才刷新。
- Codex `~/.codex/skills/.system/`、Cursor `skills-cursor/` 由产品托管，脚本不改。

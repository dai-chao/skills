---
name: update-all-skills
description: >-
  Updates all Agent Skills on the machine across Cursor, Claude Code, Hermes, Codex,
  Gemini CLI, Antigravity, Trae/Trae-CN, GitHub Copilot, OpenCode, Windsurf, Crush,
  Deep Agents, OpenClaw, skills.sh, Agent Reach, and remote packs (43*, 才虫).
  Use when the user says 更新skill、更新 skills、升级 skill、同步 skill、update skills、
  upgrade skills、refresh skills、update all skills, or asks to update/sync every installed skill.
---

# Update All Skills

刷新本机已安装的全部 Agent Skills（有 CLI / 远端 / git 源的尽量更新；纯本地拷贝会盘点并说明无法自动更新）。

## When to run

用户意图包含「更新 / 升级 / 同步 / 刷新」+「skill / skills」时，**必须**执行本 skill，不要只口头说明步骤。

## Steps

1. 定位本 skill 目录下的脚本：
   - `scripts/update-all-skills.sh`（相对本 SKILL.md）
2. 用 bash 执行（需要网络 + 写用户主目录；超时建议 ≥ 10 分钟）：

```bash
bash "<SKILL_DIR>/scripts/update-all-skills.sh"
```

将 `<SKILL_DIR>` 换成本 skill 的绝对路径（含 `SKILL.md` 的那一层）。

可选环境变量：

| 变量 | 默认 | 含义 |
|------|------|------|
| `SKIP_HERMES_AGENT_UPDATE=1` | 0 | 跳过 `hermes update`（只更新 hub skills，不升 Hermes 本体） |
| `NPM_REGISTRY` | `https://registry.npmjs.org` | `npx skills` 用的 npm registry |
| `REPORT_DIR` | `~/.cache/update-all-skills` | 报告输出目录 |

示例（跳过 Hermes Agent 本体）：

```bash
SKIP_HERMES_AGENT_UPDATE=1 bash "<SKILL_DIR>/scripts/update-all-skills.sh"
```

3. 脚本结束后读取：
   - `~/.cache/update-all-skills/last-report.txt`（人类可读）
   - `~/.cache/update-all-skills/last-summary.json`（机器可读）
4. 用中文向用户汇报：**成功 / 警告 / 失败 / 跳过** 计数，以及各平台关键变更（新增、已更新、已是最新、无法自动更新的本地 skill）。不要粘贴整份日志。

## What the script covers

按本机是否安装自动跳过缺失项。平台路径全表见 [references/platforms.md](references/platforms.md)（含 Trae、Gemini、Antigravity、Windsurf、OpenCode、Crush、Copilot 等）。

- **skills.sh**：`update -g -y`（多 Agent 共享安装）+ 带 `skills-lock.json` 的项目更新
- **Hermes / Claude / Agent Reach / 远端包 / git pull**：见 platforms.md「Update channels」
- **盘点**：扫描所有已知 global/project skill root；不改 Cursor `skills-cursor/`、Codex `.system/`

## Rules

- 默认**完整跑一遍**；仅当用户明确说「不要更新 Hermes / 只更新 Cursor」时再加对应环境变量或人工收窄。
- 不要修改 `~/.cursor/skills-cursor/`（Cursor 内置）。
- 脚本失败（exit ≠ 0）时，仍根据报告说明哪些成功、哪些失败，并给出可重试命令。
- 安装本 skill 给别人：把整个 `update-all-skills/` 目录复制到 `~/.cursor/skills/`（或 `npx skills add <repo> -g` 若已发布到仓库）。

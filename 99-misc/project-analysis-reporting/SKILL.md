---
name: project-analysis-reporting
description: Create polished, self-contained HTML reports and dashboards for business/project presentations, and discover/validate the user's current project portfolio from sessions and filesystem evidence.
version: 1.0
---

# Project Analysis & Reporting

Generate leadership-ready HTML reports from CSV/JSON data.

## User Preferences (this user)

- **Theme**: Clean light theme for business reports. White cards on `#f5f5f7` background, `#1d1d1f` text, `#e5e5ea` borders. NO dark gradients or neon accents for leadership-facing docs.
- **Format**: Single self-contained HTML file. No markdown. Include navigation, summary cards, charts (Chart.js), and collapsible detail tables.
- **Layout**: Spacious and breathable — generous whitespace, padding, gaps. User will call out "太紧凑了" when spacing is too tight.
- **Cards**: Product showcase cards show user-facing Chinese story text only.
- **Critical HTML safety**: When removing elements from HTML, never accidentally delete the `<div class="container">` wrapper — it causes full-width content stretch. Always verify container tags remain intact after deletions.

## Workflow

1. Parse source data (CSV/JSON) with Python
2. Compute aggregates (totals, groupings, distributions)
3. Build HTML with:
   - Header with title and subtitle
   - Summary stat cards (top grid)
   - Charts section (Chart.js via CDN)
   - Analysis/insights cards
   - Collapsible detail tables (date → user → records)
4. Make tables collapsible by default (click to expand)
5. Support print media query for PDF export

## Pitfalls

- Do NOT use dark gradient backgrounds for business reports — user explicitly dislikes
- Keep chart colors professional (orange `#ff6b35` as accent, not primary)
- Ensure `collapsed` class is on both trigger AND content for default-collapsed state
- Test toggle JS works correctly (stopPropagation on nested clicks)

## Templates

- `templates/html-report-template.html` — Known-good HTML/CSS scaffold with light theme, summary cards, charts, collapsible tables.
- `scripts/csv_to_html_report.py` — Full Python script: parses CSV → aggregates by date/user/model → generates complete self-contained HTML with Chart.js charts and data insights. Run directly or embed logic.

## Dark Theme Variant (Legacy)

A dark-themed variant of this reporting skill previously existed as `data-reporting-html`. It used:
- Dark gradient background (`linear-gradient(135deg, #1a1a2e, #16213e, #0f3460)`)
- Orange accent (`#ff6b35`) for highlights
- CSS-only distribution bars (no Chart.js)
- Glassmorphism cards with `backdrop-filter: blur`

**This user prefers the light theme** (see User Preferences above). The dark theme is documented here only for reference when working with users who explicitly request it. See `references/dark-theme-report-template.html` and `references/csv-html-report-example-dark.md` for the dark theme assets.

## Project Discovery

在生成报告之前，经常需要先确定用户当前在做什么项目。本节选自已合并的 `user-project-discovery`：从会话历史和文件系统中恢复、验证用户的项目组合。

### 何时使用

- 用户问 “what am I working on”、“最近项目”、“你知道我最近在做什么项目吗”
- 用户发来裸目录路径、GitHub URL 或只提项目名
- 用户纠正你之前关于项目的推断

### 工作流

1. 用 `session_search` 查找近期会话标题和预览。
2. 检查文件系统：README.md、package.json、go.mod、DESIGN.md、.git 目录等常见项目证据。
3. 交叉验证，不要假设同名项目就是同一个实现。
4. 把每个路径列出来并确认后再下结论。
5. 用 “It looks like…”、“Correct me if I’m wrong” 等低置信表达呈现结果。
6. 显式邀请纠正，然后问 “Which one should we focus on?” 或 “What do you want to do next?”

### 常见陷阱

- 不要只靠记忆；文件系统才是 ground truth。
- 不要把通用产品名（如 Agent Guard）默认映射到具体实现。
- 用户纠正或表达不满时，停止辩解，立即重新检查证据。
- 不要过度解释；这个用户偏好简洁回答。

## References

- `references/html-report-template.html` — Starter HTML/CSS scaffold with light theme, summary cards, charts, collapsible tables
- `scripts/csv_to_html_report.py` — Reusable CSV-to-HTML generator with auto column detection, aggregation, and leadership-ready output
- `references/dark-theme-report-template.html` — Dark theme HTML scaffold (from absorbed `data-reporting-html`)
- `references/csv-html-report-example-dark.md` — Full reproduction recipe from a real session (4035 records, 11 users, 7-day period) using dark theme

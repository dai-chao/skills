---
name: codebase-analysis
description: >
  Analyze a code repository (GitHub, GitLab, or local) and produce a structured
  technical review: architecture, scale, dependencies, test coverage, code
  quality, risks, and recommendations. Use when the user drops a repo URL or
  asks "analyze this repo / review this codebase / 分析一下这个仓库".
triggers:
  - repo-analysis: analyze this repo / review this codebase / 分析这个仓库 / 看一下这个仓库
  - github-url: github.com / gitlab.com / bare repo URL
  - codebase-review: architecture review / code review request on a whole repo
  - due-diligence: evaluate a library / should I use this project / is this worth using
metadata:
  priority: medium
  output_format: plain text in terminal-friendly sections
---

# Codebase Analysis Skill

## Goal
Produce a grounded, technical review of a repository without relying on the README
alone. The deliverable should tell the reader what the project is, how it is
built, where the risk lives, and what to do next.

## When to use
- User shares a GitHub/GitLab URL and says "analyze this repo" or "review this".
- User asks whether a library or project is worth adopting.
- User wants a quick architecture/overview of an unfamiliar codebase.
- User sends a bare URL and you infer the intent is to inspect the project.

## When NOT to use
- The user wants a code review of a single file or diff (use the relevant code-review skill).
- The user wants a specific bug fixed (load that bug-fix skill instead).
- The user only wants the latest release notes or README summary (use web_extract / terminal quick check).

## Step-by-step workflow

### 1. Fetch the repository
- Prefer `git clone --depth 1` to a local temporary directory.
- If GitHub CLI is not authenticated and the repo is public, clone with HTTPS is fine.
- If the repo is huge, you may `git clone --depth 1 --filter=blob:none` to save time.
- If the URL fails (private, rate-limited, or blocked), fall back to the GitHub API or ask the user for access.
- **If `web_extract` / `browser_navigate` are blocked or time out on GitHub**, fall back to `curl -sL <url>` to save the HTML, then parse it with `read_file` + `search_files`, or fetch raw files from `https://raw.githubusercontent.com/<owner>/<repo>/main/<path>`. Do not treat a single tool failure as unreachable.

### 1a. Terse URL handling (bare GitHub link / "分析这个仓库")

When the user drops only a GitHub URL or a short command like "分析这个仓库" without further context, do **not** ask what they want. Treat the URL as an implicit request for a structured repository analysis and start immediately:

1. Clone the repo shallowly to a temp directory.
2. Read README, `pyproject.toml` / `package.json` / `Cargo.toml` / `go.mod`, CI workflows.
3. Build a directory tree (depth 2–3) and count files/lines per top-level module.
4. Identify entry points, core abstractions, external integrations, and test/quality setup.
5. Return a concise, structured report with: overview, scale, architecture, integrations, tests, strengths, risks, and a verdict.

The output should be in Chinese (技术术语保留英文) unless the user wrote in English. Do not over-explain; lead with the most useful facts.

### 2. Entry-point reading
Read these files in order if they exist:
1. `README.md` — product positioning and quick-start.
2. `pyproject.toml` / `package.json` / `Cargo.toml` / `go.mod` — dependencies, scripts, metadata.
3. `CLAUDE.md` / `CONTRIBUTING.md` / `SECURITY.md` — project conventions for AI agents.
4. `CHANGELOG.md` / `HISTORY.md` — recent changes and pain points.
5. `LICENSE` — license type and implications.
6. `.github/workflows/` — CI matrix and quality gates.

### 3. Structural overview
- Build a directory tree (depth 2–3) to see the module layout.
- Count files and lines per top-level module/package: `find . -name "*.py" | xargs wc -l` (or equivalent).
- Identify the language, framework, and build system from the project files.

### 4. Core architecture
Locate and read the core implementation files:
- Entry points (CLI, server, main module).
- Core abstraction / routing logic.
- Configuration management.
- Plugin/channel/registry layer if present.
- Utilities and shared helpers.

For each, note: responsibilities, key classes/functions, coupling, and how data flows.

### 5. Platform / feature inventory
If the project integrates with external services or platforms, enumerate them:
- List each integration with its purpose and backend dependency.
- Note which are zero-config vs. require auth/key/cookie.
- Check how the project handles fallback or multi-backend routing.

### 6. Tests and quality
- List test files and count lines/cases.
- Read the CI workflow to see Python/Node/Go versions tested.
- Spot-check a few test files for coverage style (unit, mock, integration).
- Look for lint/type-check configuration (ruff, mypy, eslint, etc.).
- Note if tests are mostly mocked or exercise real dependencies.

### 7. Risks and recommendations
Always include at least these sections:
- **Strengths**: what the project does well.
- **Weaknesses / risks**: dependency fragility, large files, missing tests, auth complexity, maintenance burden.
- **Recommendations**: concrete next steps the user or maintainer could take.
- **Verdict**: whether the project is usable, experimental, or needs caution.

## Output format

Use plain text renderable in a terminal. Structure with clear headings:

```
Project
- Name, version, license, language, repo URL.

One-line summary

Scale
- Files, lines per module, languages.

Architecture
- Entry points, core classes, data flow.

Features / integrations
- Table or list of supported platforms and config needs.

Tests & quality
- Test file count, CI matrix, lint/type tools.

Strengths

Risks / open issues

Recommendations
```

Keep it concise but concrete. Mention actual file paths, command names, and line counts where possible so the user can verify.

## Pitfalls

- Do NOT rely solely on the README. READMEs market the project; the code tells the truth.
- Do NOT paste huge code blocks. Summarize and quote only the key line or signature.
- Do NOT fabricate architecture details. If you cannot infer a pattern, say so.
- Do NOT assume GitHub CLI is authenticated. Prefer `git clone` over `gh repo view` when auth is uncertain.
- If `web_extract` is blocked for a GitHub URL (common), fall back to clone immediately.
- Do NOT over-count code lines by including `.git`, vendored dependencies, or generated files.
- If the project has no tests, call it out explicitly rather than skipping the section.

## Support files
- `references/repo-analysis-checklist.md` — printable checklist covering metadata, structure, scale, architecture, dependencies, tests, risks, and verdict.

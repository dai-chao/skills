---
name: user-project-discovery
category: productivity
description: Recover and validate the user's current project portfolio when they ask about recent work, send bare paths, or refer to projects by name without context. Avoid guessing from memory alone; reconcile session history with filesystem evidence.
triggers:
  - User asks "what am I working on", "recent projects", "你知道我最近在做什么项目吗"
  - User sends bare directory paths, GitHub URLs, or repo links without an explicit goal
  - User mentions a project name ambiguously and expects shared context
  - User says a prior answer about their projects was wrong
steps:
  - Query the local session DB with session_search to find recent active sessions and their titles/previews.
  - Inspect the filesystem for project evidence including README.md, package.json, go.mod, DESIGN.md, .git directories, and directory names.
  - Cross-reference session titles with discovered directories. Do not assume a name maps to a specific implementation.
  - If the user provided paths, list them and inspect each one before drawing conclusions.
  - Present findings as a tentative, structured summary with confidence markers; explicitly invite correction.
  - After correction, update the mental model and ask what the user wants to do next with the corrected list.
pitfalls:
  - DO NOT assume a project name means the same thing across contexts. A name like Agent Guard could be a content safety guard, a runtime security tool, or a web landing page.
  - DO NOT rely solely on memory or session snippets; verify against actual files and READMEs.
  - DO NOT over-explain or ask "what do you want to do" when the user is terse; instead propose the most likely next action.
  - DO NOT ignore bare paths the user drops into the message; treat them as the primary source of truth.
  - When the user expresses frustration (e.g., "你怎么瞎说呢"), stop defending, immediately inspect the evidence they provided, and correct the summary.
---

# User Project Discovery

Use this skill when the user asks about their recent projects, sends bare paths, or references a project name without context. The goal is to reconstruct the current project portfolio from evidence, not from memory.

## Workflow

1. Search sessions first. Call `session_search()` to get recent session titles and previews. This gives clues but is not definitive.
2. Inspect the filesystem. Read READMEs, package files, DESIGN docs, and directory listings for common project locations (e.g., ~/Desktop, ~/Projects, ~/Code).
3. Cross-reference, don't assume. A project name in a session title may not match the actual codebase. Verify by reading the top-level docs.
4. Handle bare paths immediately. If the user sends paths, treat them as authoritative. List them, inspect each, and report back what they are.
5. Present with confidence markers. Phrases like "It looks like...", "The three projects on your Desktop are...", "Correct me if I'm wrong" signal that you're verifying, not asserting.
6. Invite correction explicitly. After summarizing, ask a concise follow-up like "Which one should we focus on?" or "What do you want to do next?"

## Common Pitfalls

- Name ambiguity. Generic or product names (e.g., Agent Guard) can map to multiple implementations. Always check the repo.
- Memory overconfidence. Session snippets are summaries, not ground truth. The filesystem is the ground truth.
- Ignoring terse corrections. When the user pushes back with a correction or frustration, stop and re-ground. Do not defend the wrong answer.
- Preamble bloat. This user prefers terse, no-preamble responses. Deliver the corrected answer fast.

## What to Capture

For each project, report:
- Location: absolute path
- Tech stack: Node.js, Go, Python, Electron, etc.
- Purpose: one-line summary from README or DESIGN
- Status: active / recently touched / stale
- Relationship: how it relates to other projects in the portfolio

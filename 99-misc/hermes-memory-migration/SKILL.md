---
name: hermes-memory-migration
description: Export and migrate Hermes Agent memory/profile files when switching machines or creating backups.
category: autonomous-ai-agents
tags: [hermes, memory, backup, migration, profile]
---

# Hermes Memory Migration

## When to use
- User is switching computers and wants to keep Hermes memory/profile.
- User asks for a "memory export", "backup", "core files", or "migrate my settings".
- User wants to know what files to copy from `~/.hermes`.

## What to export
The memory core consists of:
- `~/.hermes/memories/MEMORY.md` — agent's personal notes about environment, conventions, tool quirks.
- `~/.hermes/memories/USER.md` — user profile (preferences, role, style).
- `~/.hermes/SOUL.md` — optional persona file (if not empty).
- `~/.hermes/config.yaml` — model, tool, and provider settings.
- `~/.hermes/skills/` — custom skills.
- `~/.hermes/cron/` — scheduled jobs.

## Steps
1. Read `~/.hermes/memories/MEMORY.md` and `USER.md` (and `SOUL.md` if present).
2. Create a self-contained Markdown export on the user's desktop named `hermes-memory-core.md`.
3. Include the memory content, user content, and a migration guide.
4. Mention that credentials (API keys, tokens) are usually in `~/.config/`, `.env`, or keychain and should be migrated separately.

## Pitfalls
- Do NOT copy sensitive credentials into the export unless explicitly requested.
- The `memories/*.lock` files are runtime locks and should not be copied.
- If the new machine uses a different OS or home directory path, adjust the paths in the migration guide.

## References
- See `references/export-template.md` for the export file layout.

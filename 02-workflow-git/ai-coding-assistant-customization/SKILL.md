---
name: ai-coding-assistant-customization
description: Install, theme, and safely customize desktop AI coding assistants (Codex, Claude, Cursor, etc.) from GitHub repos on macOS. Covers local setup, theme switching, custom backgrounds, color overrides, and safe rollback.
version: 1.0.0
author: Hermes Agent
metadata:
  hermes:
    tags: [AI Coding Assistants, Desktop Customization, Theming, Codex, macOS, GitHub]
---

# AI Coding Assistant Customization

This skill covers the end-to-end workflow of installing, theming, and safely customizing desktop AI coding assistants from GitHub repositories on macOS. The primary example is Fei-Away/Codex-Dream-Skin, but the workflow applies to similar tools.

## Scope

- Clone and inspect third-party customization repos from GitHub URLs or bare repo links.
- Run installation scripts (shell, PowerShell, Node) with proper safety checks.
- Switch built-in presets and import custom backgrounds.
- Override theme colors via `theme.json`.
- Verify injection and capture screenshots for visual confirmation.
- Restore the official appearance when done.
- Diagnose common failures (app running, CDP port not ready, missing config, malformed images).

## When to Use

Use when the user:
- Drops a GitHub URL like `https://github.com/Fei-Away/Codex-Dream-Skin` without further explanation.
- Wants to install, try, or theme a local AI coding assistant app.
- Asks how to switch/restore/customize themes.
- Has cloned a repo and wants to run it.

## General Workflow

1. **Inspect the repo** — read README and platform-specific docs (e.g. `macos/README.md`, `windows/SKILL.md`).
2. **Pre-flight checks** — verify the target app is installed, locate its bundle, and close it before running installers that modify config.
3. **Run tests if available** — e.g. `cd macos && npm test` or `macos/scripts/doctor-macos.sh`.
4. **Install** — prefer the repo's entry script (e.g. `scripts/install-dream-skin-macos.sh --no-launch`).
5. **Start** — launch the app with the customizer's CDP/debug port and verify the injector is alive.
6. **Switch themes** — use the provided switcher script.
7. **Import custom backgrounds** — use the image loader/customizer script, not raw file copies.
8. **Verify** — run the verification script and/or take a screenshot.
9. **Restore** — use the official restore script to revert to the stock appearance.

## Safety Boundaries

- Never modify the target app's `.app`, `app.asar`, `WindowsApps`, or code signature.
- Prefer tools that use local loopback CDP (127.0.0.1) and validate the listener belongs to the target app.
- Close the target app before installers that back up `config.toml`.
- Keep custom backgrounds UI-free: no window chrome, sidebars, cards, buttons, text, or watermarks.
- Recommended master size for backgrounds: `2560 × 1440` (16:9), ≤ 16 MB, ≤ 16384 px per side.
- Respect portrait/likeness rights before distributing custom themes.

## Common Commands (Codex Dream Skin on macOS)

```bash
# Install to ~/.codex/codex-dream-skin-studio
cd /path/to/Codex-Dream-Skin/macos
./scripts/install-dream-skin-macos.sh --no-launch

# Start with CDP
~/.codex/codex-dream-skin-studio/scripts/start-dream-skin-macos.sh --port 9341 --prompt-restart

# Switch built-in preset
~/.codex/codex-dream-skin-studio/scripts/switch-theme-macos.sh --id preset-romantic-rose

# Import custom background
~/.codex/codex-dream-skin-studio/scripts/load-image-theme-macos.sh \
  --file "/path/to/image.png" \
  --name "My Theme" \
  --appearance auto \
  --focus-x 0.72 --focus-y 0.45 \
  --safe-area left --task-mode banner

# Verify and screenshot
~/.codex/codex-dream-skin-studio/scripts/verify-dream-skin-macos.sh \
  --screenshot "$HOME/Desktop/Codex Verification.png"

# Restore official appearance
~/.codex/codex-dream-skin-studio/scripts/restore-dream-skin-macos.sh --restore-base-theme --restart-codex
```

## Theme Color Overrides

To override the automatically derived accent palette, add a `colors` object to the active theme's `theme.json` (e.g. `~/Library/Application Support/CodexDreamSkinStudio/theme/theme.json`):

```json
{
  "colors": {
    "accent": "#E25563",
    "accentAlt": "#F07A86",
    "secondary": "#F3A8AF",
    "highlight": "#C93D4C",
    "line": "rgba(226,85,99,0.24)"
  }
}
```

After editing, the injector's watcher should pick up the change on the next route or reload; otherwise restart the injector.

## Troubleshooting

| Symptom | Likely Cause | Fix |
|--------|--------------|-----|
| "Close Codex before installation" | Target app is running | Quit the app and rerun installer |
| "Theme not found" | Wrong preset ID or custom theme not seeded | Check `themes/` directory for valid IDs |
| Start script times out | CDP port not ready or injector hung | Check logs in `~/Library/Application Support/CodexDreamSkinStudio/`; if injector state exists, try `verify` or full restart |
| `fetch failed` / `rejected non-Codex target` | Normal transient check; should resolve on retry | Run verify again |
| Background has UI/chrome embedded | Uploaded a screenshot instead of a pure wallpaper | Generate a UI-free `2560×1440` image and re-import |
| Colors don't change after editing `theme.json` | Watcher didn't notice | Reload Codex route or restart the injector |

## References

- See `references/codex-dream-skin.md` for the full Codex Dream Skin case study with exact paths, IDs, and prompt templates.

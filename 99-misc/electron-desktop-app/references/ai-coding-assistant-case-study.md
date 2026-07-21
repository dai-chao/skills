# Codex Dream Skin Case Study

Session: 2026-07-17. User: Fei-Away/Codex-Dream-Skin, installed on macOS for official Codex Desktop (ChatGPT.app bundle id `com.openai.codex`).

## Installation Paths

- Source clone: `/Users/chao/Desktop/Codex-Dream-Skin`
- Engine install: `~/.codex/codex-dream-skin-studio`
- State / themes / logs: `~/Library/Application Support/CodexDreamSkinStudio`
- Active theme: `~/Library/Application Support/CodexDreamSkinStudio/theme/theme.json`
- Theme library: `~/Library/Application Support/CodexDreamSkinStudio/themes/`
- Desktop launchers: `~/Desktop/Codex Dream Skin*.command`

## Verified Environment

- macOS host
- Codex Desktop installed as `/Applications/ChatGPT.app` (bundle id `com.openai.codex`)
- Bundled signed Node.js: `/Applications/ChatGPT.app/Contents/Resources/cua_node/bin/node` (v24.14.0)
- Codex version: `26.715.21425`
- Default CDP port: `9341`

## Built-in Presets (macOS)

| ID | Name |
|----|------|
| preset-midnight-aurora | 午夜极光 |
| preset-romantic-rose | 桥本有菜 |
| preset-amber-dusk | 琥珀黄昏 |
| preset-forest-mist | 森野薄雾 |
| preset-cyber-neon | 赛博霓虹 |
| preset-sakura-dawn | 樱粉晨曦 |

Switch command:

```bash
~/.codex/codex-dream-skin-studio/scripts/switch-theme-macos.sh --id <preset-id>
```

## Custom Background Import

User imported a self-generated `1672 × 941` PNG named "财神打工版" via:

```bash
~/.codex/codex-dream-skin-studio/scripts/load-image-theme-macos.sh \
  --file "/Users/chao/Downloads/7022a06b-e937-489e-92e0-e2e29f05d618.png" \
  --name "财神打工版" \
  --appearance auto \
  --focus-x 0.72 --focus-y 0.45 \
  --safe-area left \
  --task-mode banner
```

The script normalizes the image to a `2560 × 1440` derived JPEG. Custom images must be UI-free (no window chrome, sidebars, cards, text, logos, watermarks).

## Theme Color Overrides

Active `theme.json` supports explicit `colors`:

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

These override the image-derived adaptive palette. Changes are picked up by the watcher or after a route reload/injector restart.

## Verification & Restore

```bash
# Verify and screenshot
~/.codex/codex-dream-skin-studio/scripts/verify-dream-skin-macos.sh \
  --screenshot "$HOME/Desktop/Codex Dream Skin Verification.png"

# Restore official appearance
~/.codex/codex-dream-skin-studio/scripts/restore-dream-skin-macos.sh \
  --restore-base-theme --restart-codex
```

## Notes from This Session

- `web_extract` and browser tools failed to fetch GitHub due to timeout/network; `curl` worked directly.
- Installation required Codex to be closed first to avoid `config.toml` being rewritten while the app was running.
- Initial `start-dream-skin-macos.sh` command timed out at 120s but the injector actually launched and wrote `state.json`; subsequent `switch-theme` and `verify` commands worked via the hot CDP path.
- The user's `theme.json` at the time only contained adaptive `art` fields; explicit color overrides require manually adding the `colors` object.

## References

- Upstream repo: https://github.com/Fei-Away/Codex-Dream-Skin
- macOS README: `macos/README.md` in the cloned repo
- Concept prompts: `docs/background-generation-prompts.md` (incl. 财神打工版 prompt)
- Reference prompt guide: `docs/reference-background-prompt-guide.md`

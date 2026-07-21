---
name: macos-development
description: "Develop on macOS: Electron app building, computer-use desktop automation, and local browser fallback controls."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [macOS, Electron, Desktop Automation, Browser Control, Build, Sign]
    related_skills: [macos-apps]
---

# macOS Development

## When to Use This Skill

Trigger when the user wants to:
- Build, package, sign, or troubleshoot Electron apps on macOS
- Drive the macOS desktop in the background (screenshots, clicks, keyboard)
- Control the user's local Safari/Chrome on macOS via terminal

## Section 1: Electron macOS Build

Build, package, sign, and troubleshoot Electron apps on macOS.

```bash
# Install dependencies
npm install
npm run build

# Package for macOS
npx electron-builder --mac

# Sign the app
codesign --deep --force --verify --verbose --sign "Developer ID" MyApp.app
```

See [references/electron-macos-build.md](references/electron-macos-build.md) for full details.

## Section 2: macOS Computer Use

Drive the macOS desktop in the background — screenshots, clicks, keyboard input.

```python
# Take screenshot
import subprocess
subprocess.run(['screencapture', '-x', 'screenshot.png'])
```

See [references/macos-computer-use.md](references/macos-computer-use.md) for full details.

## Section 3: Local Browser Fallback

Control the user's local Safari/Chrome on macOS via terminal.

```bash
# Open URL in Safari
open -a Safari "https://example.com"

# Control Chrome via AppleScript
osascript -e 'tell application "Google Chrome" to open location "https://example.com"'
```

See [references/local-browser-fallback.md](references/local-browser-fallback.md) for full details.

## Common Pitfalls

1. **Electron signing**: Notarization requires Apple Developer account
2. **Local testing without signing**: Set `CSC_IDENTITY_AUTO_DISCOVERY=false` to skip code signing for local builds. This falls back to ad-hoc signing (`identityName=- identityHash=none`), which is fine for local use but triggers Gatekeeper on other machines.
3. **Code signing identity failure**: If you see `this identity cannot be used for signing code`, the certificate's private key is missing. Either skip signing (see #2) or re-download the cert from Apple Developer.
4. **Electron download timeout**: Set `ELECTRON_MIRROR="https://npmmirror.com/mirrors/electron/"` or retry — electron-builder caches downloads and usually succeeds on second attempt.
5. **Computer use permissions**: Screen recording needs user approval in System Preferences
6. **Browser control**: AppleScript may fail if browser is not already running
7. **macOS version differences**: APIs change between macOS versions; test on target version

## Related Skills

- [electron-desktop-app](skill://electron-desktop-app) — General Electron app scaffolding, IPC patterns, security best practices, and cross-platform packaging

## References

- `references/electron-macos-build.md` — Full macOS build details
- `references/electron-codesign-troubleshooting.md` — Common codesign errors and workarounds
- `references/codex-dream-skin-install.md` — Codex Dream Skin Studio (macOS theme injection) install, switch, verify, and restore notes

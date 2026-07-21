---
name: electron-macos-build
description: |
  Build, package, sign, and troubleshoot Electron apps on macOS.
  Covers electron-builder, codesign, notarization, Apple certs,
  ad-hoc signing, and common failure modes on Darwin arm64/x64.
version: 1.0.0
platforms: [macos]
metadata:
  hermes:
    tags: [electron, macos, codesign, electron-builder, desktop, apple]
    category: software-development
    related_skills: [macos-computer-use]
---

# Electron macOS Build & Sign

Building Electron apps on macOS involves electron-builder, Apple code signing,
and notarization. This skill covers the common failure modes and workarounds.

## Quick Fixes

### Codesign identity failure: "this identity cannot be used for signing code"

**Symptom:**
```
Apple Development: user@example.com (TEAM_ID): this identity cannot be used for signing code
```

**Cause:** The certificate is in Keychain but the corresponding private key
is missing (created on another machine, deleted, or not exported with the cert).

**Fix 1 — Skip signing for local testing:**
```bash
CSC_IDENTITY_AUTO_DISCOVERY=false npm run pack
# or
CSC_IDENTITY_AUTO_DISCOVERY=false npm run dist
```

This falls back to ad-hoc signing (`identityName=- identityHash=none`),
which is fine for local use but will trigger Gatekeeper on other machines.

**Fix 2 — Use a different valid identity:**
```bash
# List valid identities
security find-identity -v -p codesigning

# Specify a known-good one
CSC_NAME="Apple Development: Your Name (TEAM_ID)" npm run pack
```

**Fix 3 — Re-download the private key:**
Go to Apple Developer → Certificates → download the cert again and import
into Keychain Access. Ensure the key icon appears next to the cert.

### Electron download timeout (GitHub releases)

**Symptom:**
```
dial tcp 20.205.243.166:443: connect: operation timed out
```

**Fix:** electron-builder caches downloads. The retry mechanism usually
succeeds on the second attempt. If it keeps failing, set a mirror:
```bash
export ELECTRON_MIRROR="https://npmmirror.com/mirrors/electron/"
npm run pack
```

Or pre-download the zip to the cache:
```bash
# Cache location
~/Library/Caches/electron/
```

### Desktop backend fails to start (blank chat / "Could not connect")

**Symptom:** Desktop opens but shows blank content or connection errors.

**Common cause 1 — Model not configured:**
`~/.hermes/config.yaml` has empty `model: {}`. Desktop spawns the backend
but it cannot serve requests without a default model.

**Fix:**
```bash
hermes config set model.default kimi/kimi-k2.6
hermes config set model.provider kimi
```

**Common cause 2 — Hermes CLI not found:**
Desktop falls through to bootstrap mode. Check `~/.hermes/logs/desktop.log`
for `[bootstrap] no Hermes install found`.

**Fix:** Ensure `hermes` is on PATH and the venv at
`~/.hermes/hermes-agent/venv` exists.

### Notarization skipped

**Symptom:**
```
skipped macOS notarization reason=notarize options were unable to be generated
```

**Cause:** Notarization requires Apple Developer credentials:
- `APPLE_API_KEY` + `APPLE_API_KEY_ID` + `APPLE_API_ISSUER`
- Or `APPLE_ID` + `APPLE_APP_SPECIFIC_PASSWORD` + `APPLE_TEAM_ID`

**Fix:** Set env vars or configure in electron-builder. For local testing,
notarization is not needed — ad-hoc signing is sufficient.

## Hermes Desktop Specifics

Hermes Desktop is an Electron app that wraps the Hermes Agent backend.
Its config and data live in platform-specific paths:

### macOS paths

| File | Path |
|------|------|
| Connection config | `~/Library/Application Support/Hermes/connection.json` |
| Update config | `~/Library/Application Support/Hermes/updates.json` |
| Active profile | `~/Library/Application Support/Hermes/active-profile.json` |
| Default project dir | `~/Library/Application Support/Hermes/project-dir.json` |
| UI state (Local Storage) | `~/Library/Application Support/Hermes/Local Storage/leveldb/` |
| Electron prefs | `~/Library/Application Support/Hermes/Preferences` |
| Logs | `~/.hermes/logs/desktop.log` |
| Bootstrap marker | `~/.hermes/hermes-agent/.hermes-bootstrap-complete` |

### Backend modes

Hermes Desktop can run in two modes:

1. **Local backend** — Desktop spawns `hermes_cli.main dashboard` as a
   subprocess. Requires a working Hermes CLI install with venv.
2. **Remote gateway** — Connects to a remote Hermes Gateway via WebSocket.
   Config stored in `connection.json` with `url`, `authMode` (`token` or
   `oauth`), and optional `token`.

### Build commands

```bash
cd apps/desktop

# Dev mode (hot reload)
npm run dev

# Pack without distribution (local test)
npm run pack

# Full distribution (dmg + zip)
npm run dist

# Skip signing for local test
CSC_IDENTITY_AUTO_DISCOVERY=false npm run pack
```

### Configuring the Desktop app

When the user says "configure desktop" or "配置 desktop", they typically
mean one of:

1. **Set up the backend connection** — local Hermes agent or remote gateway
2. **Configure model/API keys** — these live in `~/.hermes/config.yaml` and
   `.env`, shared with CLI
3. **UI preferences** — stored in Local Storage (theme, pane states, etc.)
4. **Language / 汉化** — switch UI language via `display.language`

**Proactive config reading:** When asked about Desktop config, immediately
read the relevant files rather than asking the user. Check:
- `~/Library/Application Support/Hermes/connection.json`
- `~/Library/Application Support/Hermes/active-profile.json`
- `~/.hermes/config.yaml`
- `~/.hermes/.env`

### Switching UI language

Hermes Desktop supports `en`, `zh`, `zh-hant`, `ja`. To switch:

```bash
hermes config set display.language zh
```

Then restart Desktop. The locale is read from `config.display.language`
on boot. Translation files are at `apps/desktop/src/i18n/{en,zh,zh-hant,ja}.ts`.

## General electron-builder macOS config

```json
{
  "build": {
    "mac": {
      "category": "public.app-category.developer-tools",
      "entitlements": "electron/entitlements.mac.plist",
      "entitlementsInherit": "electron/entitlements.mac.inherit.plist",
      "gatekeeperAssess": false,
      "hardenedRuntime": true,
      "target": ["dmg", "zip"]
    }
  }
}
```

## References

- `references/electron-builder-codesign-errors.md` — Common codesign errors and fixes
- `references/hermes-desktop-backend-config.md` — Hermes Desktop backend config, startup failures, and diagnosis

# Hermes Desktop Backend Configuration

Hermes Desktop connects to a Hermes Agent backend. When the backend is
misconfigured, the Desktop app may appear to start but show no content,
or show "Could not connect" errors.

## Common failure: model not configured

**Symptom:** Desktop starts but the chat area is blank or shows
"No model configured". The backend process starts but cannot serve
requests.

**Root cause:** `~/.hermes/config.yaml` has empty `model: {}`

```yaml
# BROKEN — model section is empty
model: {}
providers: {}
```

**Fix:** Set a default model and provider:

```bash
hermes config set model.default kimi/kimi-k2.6
hermes config set model.provider kimi
```

Verify:
```bash
hermes config show | grep -A2 "Model:"
# Should show: Model: {'default': 'kimi/kimi-k2.6', 'provider': 'kimi'}
```

**Note:** The `hermes` CLI must be on PATH and have a working venv.
Desktop uses `findOnPath('hermes')` to locate it.

## Backend connection modes

### 1. Local backend (default)

Desktop spawns `hermes dashboard` as a subprocess. Requirements:
- `hermes` CLI on PATH
- Working Python venv at `~/.hermes/hermes-agent/venv`
- Valid `~/.hermes/config.yaml` with model configured
- API keys in `~/.hermes/.env`

The backend listens on:
- WebSocket: `127.0.0.1:9120` (random port in 9120-9199 range)
- HTTP API: `127.0.0.1:8642`

### 2. Remote gateway

Connect to a remote Hermes Gateway. Config stored in:
`~/Library/Application Support/Hermes/connection.json`

Example:
```json
{
  "url": "https://gateway.example.com",
  "authMode": "token",
  "token": "..."
}
```

## Diagnosing backend startup

Check the desktop log:
```bash
tail -f ~/.hermes/logs/desktop.log
```

Key log lines:
- `[boot] Resolving Hermes backend` — starting backend detection
- `[boot] Starting Hermes backend via existing Hermes CLI` — found CLI
- `[boot] Hermes backend is ready` — success
- `[bootstrap] no Hermes install found` — CLI not found, will bootstrap

Check backend process:
```bash
# Find the hermes backend process
pgrep -f "hermes_cli.main" | xargs ps -o pid,command

# Check ports
lsof -Pan -i | grep -E "(9120|8642)"
```

## Desktop data files (macOS)

| File | Purpose |
|------|---------|
| `~/Library/Application Support/Hermes/connection.json` | Remote gateway config |
| `~/Library/Application Support/Hermes/updates.json` | Update channel/branch |
| `~/Library/Application Support/Hermes/active-profile.json` | Hermes profile override |
| `~/Library/Application Support/Hermes/project-dir.json` | Default project directory |
| `~/Library/Application Support/Hermes/Local Storage/leveldb/` | UI state (nanostores) |
| `~/.hermes/logs/desktop.log` | Desktop boot log |
| `~/.hermes/hermes-agent/.hermes-bootstrap-complete` | Bootstrap marker |

## Localization (i18n)

Hermes Desktop has built-in translations. Supported locales:
- `en` — English (default)
- `zh` — 简体中文
- `zh-hant` — 繁體中文
- `ja` — 日本語

**Switch language:**
```bash
hermes config set display.language zh
```

Then restart Desktop. The setting is read from `config.display.language`
in `~/.hermes/config.yaml` on boot.

Translation files live in the source:
```
apps/desktop/src/i18n/
  en.ts      — English source strings
  zh.ts      — Simplified Chinese
  zh-hant.ts — Traditional Chinese
  ja.ts      — Japanese
```

## Proactive checks when user asks about Desktop

When the user says "configure desktop" or "desktop not working":

1. **Read config first** — check `~/.hermes/config.yaml` for `model.default`
2. **Check API keys** — `~/.hermes/.env` for the provider's key
3. **Check backend status** — `pgrep -f hermes_cli.main` + port listeners
4. **Check desktop log** — `~/.hermes/logs/desktop.log` for boot errors
5. **Check data files** — `~/Library/Application Support/Hermes/*.json`

Do not ask the user "what's wrong" — read these files proactively.

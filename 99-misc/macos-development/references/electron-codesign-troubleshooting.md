# Electron macOS Code Signing Troubleshooting

## "this identity cannot be used for signing code"

**Symptom:**
```
Apple Development: user@example.com (TEAM_ID): this identity cannot be used for signing code
```

**Cause:** The certificate is in Keychain but the corresponding private key is missing (created on another machine, deleted, or not exported with the cert).

**Fix 1 — Skip signing for local testing:**
```bash
CSC_IDENTITY_AUTO_DISCOVERY=false npm run pack
# or
CSC_IDENTITY_AUTO_DISCOVERY=false npm run dist
```

This falls back to ad-hoc signing (`identityName=- identityHash=none`), which is fine for local use but will trigger Gatekeeper on other machines.

**Fix 2 — Use a different valid identity:**
```bash
# List valid identities
security find-identity -v -p codesigning

# Specify a known-good one
CSC_NAME="Apple Development: Your Name (TEAM_ID)" npm run pack
```

**Fix 3 — Re-download the private key:**
Go to Apple Developer → Certificates → download the cert again and import into Keychain Access. Ensure the key icon appears next to the cert.

## First-Run Gatekeeper (Unsigned Apps)

After building with `CSC_IDENTITY_AUTO_DISCOVERY=false`, the app will show "cannot be opened" on first launch.

**User workaround:**
System Settings → Privacy & Security → Security → "Open Anyway"

Or right-click the app → "Open" → confirm dialog.

## Notarization Skipped

```
skipped macOS notarization reason=notarize options were unable to be generated
```

Notarization requires Apple Developer credentials. For local testing, notarization is not needed — ad-hoc signing is sufficient.

## Electron Download Timeout

```
dial tcp ...:443: connect: operation timed out
```

**Fix:** Set a mirror or retry:
```bash
export ELECTRON_MIRROR="https://npmmirror.com/mirrors/electron/"
npm run pack
```

Or pre-download to `~/Library/Caches/electron/`.

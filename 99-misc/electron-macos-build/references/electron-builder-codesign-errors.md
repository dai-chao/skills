# Common electron-builder Codesign Errors on macOS

## "this identity cannot be used for signing code"

**Full error:**
```
Command failed: codesign --sign "Apple Development: ..." --force --timestamp --options runtime ...
Apple Development: user@example.com (TEAM_ID): this identity cannot be used for signing code
```

**Diagnosis:**
```bash
# List all identities
security find-identity -v -p codesigning

# Check if private key exists for a specific cert
security find-identity -v -p codesigning | grep TEAM_ID
# Then open Keychain Access and look for the key icon next to the cert
```

**Fixes:**
1. `CSC_IDENTITY_AUTO_DISCOVERY=false` — skip signing entirely
2. `CSC_NAME="..."` — specify a different valid identity
3. Re-download cert + private key from Apple Developer portal

## "The specified item could not be found in the keychain"

**Cause:** The cert was deleted from Keychain or the identity hash changed.

**Fix:** Re-import the certificate or specify a different one.

## "errSecInternalComponent"

**Cause:** codesign tool internal error, often after macOS update.

**Fix:**
```bash
# Reset codesigning
security delete-keychain ~/Library/Keychains/login.keychain-db
# Then re-import certs or let Xcode re-create
```

## Ad-hoc signing fallback

When `CSC_IDENTITY_AUTO_DISCOVERY=false`, electron-builder uses:
```
codesign --sign - --force ...
```

The `-` means "ad-hoc sign" — no identity needed. The app will:
- Run fine on the build machine
- Be blocked by Gatekeeper on other machines
- Not be notarized

This is the correct mode for local development and CI test builds.

## Electron download failures

**Timeout from GitHub:**
```
dial tcp 20.205.243.166:443: connect: operation timed out
```

**Retry:** electron-builder automatically retries once after clearing cache.

**Mirror (China):**
```bash
export ELECTRON_MIRROR="https://npmmirror.com/mirrors/electron/"
```

**Pre-download:**
```bash
# Download manually and place in cache
curl -L -o ~/Library/Caches/electron/electron-v40.9.3-darwin-arm64.zip \
  https://github.com/electron/electron/releases/download/v40.9.3/electron-v40.9.3-darwin-arm64.zip
```

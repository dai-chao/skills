---
name: macos-apps
description: "Automate macOS built-in apps: Notes, Reminders, Messages, FindMy via CLI tools and AppleScript."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [macOS, Apple, Notes, Reminders, Messages, FindMy, Automation, CLI]
    related_skills: [macos-computer-use, electron-macos-build, local-browser-fallback]
---

# macOS Built-in App Automation

Control macOS native apps via command-line tools and AppleScript. All skills in this family require macOS and various Apple permissions.

## Common Prerequisites

- macOS with the target app installed
- Homebrew for CLI tool installation
- Apple permissions (varies by app — see each section)

## Apple Notes

Manage Apple Notes via the `memo` CLI.

```bash
brew tap antoniorodr/memo && brew install antoniorodr/memo/memo
```

**Operations:**
```bash
memo list                    # List all notes
memo list --folder "Work"    # Filter by folder
memo search "keyword"        # Search notes
memo create "Title" --body "Content" --folder "Work"
memo edit "Title" --body "New content"
memo delete "Title"
memo export "Title" --format markdown --output ./note.md
memo folders                 # List folders
memo create-folder "New Folder"
```

**Limitations:** No image/attachment editing via CLI.

**Permissions:** Automation permission for Notes.app.

---

## Apple Reminders

Manage Apple Reminders via `remindctl`.

```bash
brew install steipete/tap/remindctl
remindctl authorize  # One-time permission grant
```

**Operations:**
```bash
remindctl lists                              # List reminder lists
remindctl list "Personal"                     # Show reminders in a list
remindctl add "Buy milk" --list "Personal" --due "2024-12-25 14:00"
remindctl add "Call dentist" --alarm "2024-12-25 09:00"
remindctl complete "Buy milk" --list "Personal"
remindctl delete "Buy milk" --list "Personal"
```

**Date formats:** `--due "YYYY-MM-DD HH:MM"` (no alarm), `--alarm "YYYY-MM-DD HH:MM"` (with notification).

**Output formats:** `--format json`, `--format plain`, `--quiet`.

**Permissions:** Reminders.app permission.

**Pitfall:** Pre-v1.2.0 `folder.alias` (singular) silently fails. Use `folder.aliases` (plural) in TOML config.

---

## iMessage / SMS

Send and receive iMessages via `imsg` CLI.

```bash
brew install steipete/tap/imsg
```

**Operations:**
```bash
imsg chats                    # List recent chats
imsg history "+1234567890"   # View chat history by phone number
imsg send "+1234567890" "Hello!"
imsg send --file ./photo.jpg "+1234567890" "Check this out"
imsg watch                    # Watch for new messages (JSON output)
```

**Service selection:** `--service imessage` (blue), `--service sms` (green), `--service auto` (default).

**Safety rules:**
- Always confirm recipient before sending
- Never send spam or unsolicited messages
- Respect the user's contact privacy

**Permissions:** Full Disk Access, Automation permission for Messages.app.

---

## FindMy

Track Apple devices and AirTags. **No native CLI exists** — uses AppleScript + screenshots + vision analysis.

**Prerequisites:**
- macOS with FindMy.app
- iCloud signed in
- Screen Recording permission
- Optional: `peekaboo` for UI automation

**Workflow:**
1. Open FindMy.app via AppleScript: `osascript -e 'tell application "FindMy" to activate'`
2. Take screenshot and analyze with `vision_analyze`
3. For AirTag tracking over time, record location snapshots periodically

**Pitfalls:**
- Updates stop when FindMy is minimized
- No programmatic API — entirely vision-dependent
- Screen Recording permission required for screenshots

---

## Common Patterns

### Permission Troubleshooting

If a tool fails with permission errors:
1. Open **System Settings → Privacy & Security**
2. Check the relevant permission category (Automation, Full Disk Access, Screen Recording)
3. Ensure the terminal/IDE running Hermes is listed and enabled
4. Restart the target app after granting permission

### AppleScript Fallback

When CLI tools fail, AppleScript can often control the UI directly:

```applescript
osascript -e 'tell application "Notes" to make new note with properties {name:"Backup", body:"Content"}'
osascript -e 'tell application "Reminders" to make new reminder with properties {name:"Task", due date:current date + 1 * days}'
```

### Safety Rules (All Apps)

- Never modify or delete data without user confirmation
- Respect privacy — messages, notes, and location data are sensitive
- Always verify recipient before sending messages
- Report permission issues clearly so the user can fix them

## Pitfalls

- **All tools are macOS-only** — they will not work on Linux or Windows
- **Permissions are gated by Apple** — no workaround without user interaction
- **CLI tools may break after macOS updates** — check `brew update` if a tool stops working
- **FindMy has no native API** — vision-based extraction is inherently fragile
- **iMessage requires Full Disk Access** — this is a broad permission; explain why it's needed
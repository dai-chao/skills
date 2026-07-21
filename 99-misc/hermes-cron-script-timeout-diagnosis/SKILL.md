---
name: hermes-cron-script-timeout-diagnosis
title: Diagnose Hermes Cron Script Timeouts
description: Systematic workflow for investigating "Script timed out after Ns" errors from Hermes cron jobs that execute data-collection or long-running scripts.
tags: [hermes, cron, timeout, debugging, ops]
---

# Diagnose Hermes Cron Script Timeouts

Use this when a Hermes cron job fails with `Script timed out after 120s: /path/to/script.py` (or similar).

## Core Insight

A timeout usually means one of two things:

1. **The script is a daemon** (infinite loop, long-running listener) being run as a periodic cron task.
2. **The script is genuinely stuck** on a blocking call (network I/O, database lock, unbounded computation).

Always determine which case you are in before attempting a fix.

## Diagnostic Steps

### 1. Read the script

Identify its lifecycle model:

- Does it have `while True:` or an infinite event loop?
- Does it call `time.sleep(...)` in a reconnect loop?
- Does it open a long-lived network connection (SSE, WebSocket, streaming HTTP)?
- Does it ever call `sys.exit(0)` or return naturally?

> If the script is designed to run forever, it should not be executed by a cron runner with a timeout. Move it to a background service (`nohup`, `launchd`, `systemd`, `screen`, etc.).

### 2. Check the Hermes cron job configuration

```bash
cat ~/.hermes/cron/jobs.json | jq '.jobs[] | select(.id == "JOB_ID")'
```

Look for:

- `schedule`: how often it runs (`every 1m`, `every 10m`, etc.)
- `script`: the script path
- `no_agent`: whether it runs directly (true) or through an agent (false)
- `enabled_toolsets`: e.g., `["terminal"]`

### 3. Inspect recent cron outputs

```bash
ls -lt ~/.hermes/cron/output/JOB_ID/
```

Read the most recent `.md` file. It contains:

- The exact error message
- The prompt passed to the runner
- The response produced

### 4. Check script-specific logs

If the script writes its own logs, tail them:

```bash
tail -n 100 ~/.local/share/APP/sse_events.log
```

Look for patterns like:

- Rapid reconnect loops (`connected → closed → reconnecting` every few seconds)
- Auth errors before the timeout
- No output at all (indicates the script is blocked before logging)

### 5. Check running processes

```bash
ps aux | grep SCRIPT_NAME | grep -v grep
```

Look for:

- Multiple overlapping instances (process leak)
- A single very old instance that survived previous timeouts
- Stale bash wrapper processes left behind by the runner

Also inspect what the process is actually doing:

```bash
lsof -p PID | grep -E "IPv|TCP|REG"
```

- An open network socket (`IPv4`, `ESTABLISHED`) with no recent log writes suggests the process is **stuck in a blocking read** (e.g., `socket.recv()`, SSE `read()`)
- A connection to `localhost:7897` or similar often indicates traffic is routing through a local proxy (Clash, V2Ray, etc.), which can introduce its own timeouts or buffering issues

**Check the parent process** — Hermes runner orphans:

```bash
ps -o pid,ppid,command -p PID
```

- If the parent is the Hermes gateway (`...hermes_cli.main gateway run`), the process was spawned by cron but **survived the timeout kill**. This is a known leak pattern: the runner kills the bash wrapper, but the Python grandchild survives.
- If you see a bash wrapper (`/bin/bash -lic set +m; python3 ...`) with a Python grandchild, the wrapper may be dead/unresponsive while the child lives on.

**Correlate PIDs with logs:**

```bash
grep "pid" ~/.local/share/APP/script.log | tail -20
```

- If the log contains `pid` fields, match them against `ps` start times. A stable old PID + a new PID producing rapid reconnects strongly indicates a **server-side single-connection limit** (see findings table below).

### 6. Beware of terminal truncation when reading scripts

Tools like `sed` or `cat` may truncate very long lines with `...` in the terminal output, making a valid file look corrupted.

```bash
# If a line looks truncated or suspicious, verify raw bytes:
sed -n '15p' /path/to/script.py | hexdump -C
# or
python3 -m py_compile /path/to/script.py
```

### 7. Correlate timestamps

Compare:

- Cron `last_run_at` from `jobs.json`
- Script log timestamps
- Process start times from `ps`

Hermes cron logs are usually UTC; `ps` start times are local. Be aware of timezone when correlating.

## Common Findings & Fixes

| Finding | Fix |
|---------|-----|
| Script is an infinite-loop daemon | **Option A**: Remove from cron; run as background service (`launchd` plist on macOS, `systemd` on Linux, or `nohup`). **Option B**: Keep in cron but set `repeat: 1` (run once per trigger) + long schedule interval (`every 5m` or longer) + add pidfile lock inside script to prevent duplicate instances. |
| SSE/streaming connection drops immediately | Investigate auth, headers, rate limiting, **server-side concurrent connection limits**, or network path with `curl -v -N` |
| Multiple PIDs in script logs | Cron is starting overlapping instances; add a pidfile/lockfile or switch to a single background service |
| Script has no logs and just hangs | Add verbose logging around the suspected blocking call; set explicit socket/read timeouts |
| Process has open socket but no log writes for hours | Process is likely stuck in a blocking read (e.g., SSE `read()` behind a proxy). Kill it and add lower-level read timeouts |
| Need periodic polling but script runs too long | Refactor to a short-lived task with a `--max-runtime 55` flag that exits gracefully before cron timeout |
| **Rapid reconnect loop + old stable PID still running** | **Server-side single-connection limit** (e.g., SSE/WebSocket per-account limit). New instances are dropped immediately. Kill all instances, then run as a single background service |
| **HTTP 200 then immediate disconnect** | **Proxy or server concurrency limit**, not auth failure. Check `lsof` for proxy connections (e.g., `localhost:7897`). Test with `curl -v -N` directly |
| **Bash wrapper survived timeout, child still running** | Hermes runner leak. Kill the entire process tree manually. Do not rely on cron timeout cleanup for daemon scripts |
| **no_agent script with infinite loop in cron** | This is a process leak waiting to happen. If the script loops forever, cron will start a new instance every tick while the old one keeps running. Either: (1) make the script single-run and let cron restart it, or (2) move to a dedicated background process. Never combine `while True` with `no_agent: true` and short cron intervals without a pidfile. |

## Pitfalls

- **Do not** simply increase the cron timeout to "fix" a daemon script. It will still be killed eventually and may leak processes.
- **Do not** assume the timeout is the only problem. A script stuck in a rapid reconnect loop may time out *and* waste resources; both issues need fixing.
- **Do not** trust truncated terminal output when inspecting scripts. A line displayed as `CREDENTIALS_PATH=os.pat...on")` may be perfectly valid; verify with `hexdump -C` or `py_compile`.
- When checking logs, distinguish between the **cron runner output** (`~/.hermes/cron/output/`) and the **script's own log file** (often under `~/.local/share/`).
- A log file with a recent `mtime` but stale content is a strong signal that the writing process is hung, not dead.
- **Beware of server-side single-connection limits.** If logs show `connected → closed → reconnecting` in a tight loop but `curl -v -N` works fine from the shell, the server may be rejecting *duplicate* connections from overlapping cron instances while allowing the first one. Always check if an older PID is still alive.
- **Proxies can drop SSE bodies immediately.** A local proxy (Clash, V2Ray, etc.) on `localhost:7897` may return HTTP 200 and then immediately close the stream when it detects a duplicate connection or hits its own buffer limit. Do not mistake this for an auth error.
- **Hermes runner timeout cleanup is not guaranteed for daemon scripts.** A `no_agent: true` script with a bash wrapper and Python grandchild may survive the 120s timeout kill. Treat any daemon script in cron as a probable process leak.
- **If you must run a daemon script via cron, add a pidfile.** The script should check `~/.local/share/APP/sse_listener.pid` on startup. If the file exists and the process is alive, exit immediately. This prevents the zombie-process pileup that occurs when cron starts overlapping instances.
- **For SSE listeners specifically:** The `IncompleteRead` error from `urllib` is normal when the server drops the connection. The script should catch this, log it, and reconnect. Do not treat it as a fatal error requiring manual intervention.

## Verification

After applying a fix:

1. Confirm no new timeout errors appear in `~/.hermes/cron/output/JOB_ID/`.
2. Confirm process count is stable (`ps aux | grep ...`).
3. Confirm script logs show healthy behavior (e.g., sustained connection, real events being processed).

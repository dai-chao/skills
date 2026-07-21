---
name: language-debugging
description: "Debug Python and Node.js applications: pdb, debugpy, node inspect, Chrome DevTools Protocol."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [debugging, python, nodejs, pdb, debugpy, node-inspect, cdp, breakpoints, dap]
    related_skills: [systematic-debugging, test-driven-development]
---

# Language Debugging

Breakpoint-driven debugging for Python and Node.js from the terminal. Covers local interactive REPLs, remote/headless attach, post-mortem analysis, and programmatic DevTools Protocol scripting.

## When to Use

- A test fails and the traceback doesn't reveal why a value is wrong
- You need to step through a function and watch state mutate
- A long-running process (gateway, daemon, TUI) misbehaves and can't be restarted
- Post-mortem: an exception fired and you want to inspect locals at the crash site
- A subprocess / child process is the actual bug site

**Don't use for:** things `print()` / `console.log` / `logging.debug` solve in under a minute.

---

## Python Debugging (pdb + debugpy)

### Three Tools

| Tool | When |
|---|---|
| **`breakpoint()` + pdb** | Local, interactive, simplest. Add in source, run normally, get REPL at that line. |
| **`python -m pdb`** | Launch script under pdb with no source edits. |
| **`debugpy`** | Remote / headless / attach to already-running process. DAP protocol, scriptable. |

**Start with `breakpoint()`.** It's the cheapest thing that works.

### pdb Quick Reference

Inside any pdb prompt `(Pdb)`:

| Command | Action |
|---|---|
| `h` / `h cmd` | help |
| `n` | next line (step over) |
| `s` | step into |
| `r` | return from current function |
| `c` | continue |
| `unt N` | continue until line N |
| `j N` | jump to line N (same function only) |
| `l` / `ll` | list source around current line / full function |
| `w` | where (stack trace) |
| `u` / `d` | move up / down in the stack |
| `p expr` / `pp expr` | print / pretty-print expression |
| `display expr` | auto-print expr on every stop |
| `b file:line` | set breakpoint |
| `tbreak file:line` | one-shot breakpoint |
| `interact` | drop into full Python REPL in current scope (Ctrl+D to exit) |
| `q` | quit |

`interact` is the most powerful — you can import anything, inspect complex objects, call methods. Use `!x = 42` from the `(Pdb)` prompt to mutate locals.

### Recipes

**Local breakpoint:**
```python
def compute(x, y):
    result = some_helper(x)
    breakpoint()           # drops into pdb here
    return result + y
```
Don't forget to remove before committing: `rg -n 'breakpoint\(\)' --type py`

**Launch under pdb (no source edits):**
```bash
python -m pdb path/to/script.py arg1 arg2
```

**Debug a pytest test:**
```bash
pytest tests/foo.py::test_bar --pdb -p no:xdist  # xdist + pdb = hang
```

**Post-mortem:**
```python
import pdb, sys
try:
    run_the_thing()
except Exception:
    pdb.post_mortem(sys.exc_info()[2])
```

**Remote debug with debugpy:**
```python
import debugpy
debugpy.listen(("127.0.0.1", 5678))
debugpy.wait_for_client()
debugpy.breakpoint()
```

Or launch with: `python -m debugpy --listen 127.0.0.1:5678 --wait-for-client your_script.py`

**Attach to running process:**
```bash
python -m debugpy --listen 127.0.0.1:5678 --pid <pid>
```

May need: `echo 0 | sudo tee /proc/sys/kernel/yama/ptrace_scope`

**Agent-friendly remote-pdb (simpler than DAP):**
```bash
pip install remote-pdb
```
```python
from remote_pdb import set_trace
set_trace(host="127.0.0.1", port=4444)
```
Then: `nc 127.0.0.1 4444` — gives a `(Pdb)` prompt exactly as if local.

### Python Pitfalls

1. **pdb under pytest-xdist silently hangs.** Always use `-p no:xdist` or `-n 0`.
2. **`breakpoint()` in CI / non-TTY hangs.** Never commit it.
3. **`PYTHONBREAKPOINT=0`** disables all breakpoints. Check the env.
4. **`debugpy.listen` blocks only with `wait_for_client()`.** Without it, execution continues before attach.
5. **Attach to PID fails on hardened kernels.** Fix `ptrace_scope` or launch under debugpy from start.
6. **Threads:** pdb only debugs current thread. Use `debugpy` for multithreaded.
7. **asyncio:** `await` inside pdb requires Python 3.13+ or `interact` mode tricks.
8. **Forking:** pdb does not follow forks. Each child needs its own `breakpoint()`.

---

## Node.js Debugging (node inspect + CDP)

### Two Tools

| Tool | When |
|---|---|
| **`node inspect`** | Built-in, zero install, CLI REPL. Best for quick poking. |
| **CDP via `chrome-remote-interface`** | Scriptable from Node/Python. Best for automation, non-interactive agent loops. |

**Prefer `node inspect` first.** It's always available.

### `node inspect` Quick Reference

```bash
node inspect path/to/script.js        # pause on first line
node --inspect-brk script.js          # same, but run normally after attach
node --inspect script.js              # listen but don't pause
```

At the `debug>` prompt:

| Command | Action |
|---|---|
| `c` / `cont` | continue |
| `n` / `next` | step over |
| `s` / `step` | step into |
| `o` / `out` | step out |
| `sb('file.js', 42)` | set breakpoint at line 42 |
| `sb('functionName')` | break on function entry |
| `cb('file.js', 42)` | clear breakpoint |
| `bt` | backtrace |
| `list(5)` | show 5 lines around current position |
| `repl` | drop into JS REPL in current scope (Ctrl+C to exit) |
| `exec expr` | evaluate expression once |
| `restart` | restart script |
| `kill` | kill script |
| `.exit` | quit debugger |

### Attaching to a Running Process

```bash
kill -SIGUSR1 <pid>        # enable inspector on existing process
node inspect -p <pid>      # attach by PID
# or:
curl -s http://127.0.0.1:9229/json/list | jq -r '.[0].webSocketDebuggerUrl'
node inspect ws://127.0.0.1:9229/<uuid>
```

### TypeScript / tsx

```bash
node --inspect-brk --import tsx script.ts
node --inspect-brk -r tsx/cjs script.ts
```

### Programmatic CDP Scripting

```bash
npm i -g chrome-remote-interface
```

```javascript
const CDP = require('chrome-remote-interface');
(async () => {
  const client = await CDP({ port: 9229 });
  const { Debugger, Runtime } = client;
  Debugger.paused(async ({ callFrames, reason }) => {
    const top = callFrames[0];
    console.log(`PAUSED: ${reason} @ ${top.url}:${top.location.lineNumber + 1}`);
    // Walk scopes
    for (const scope of top.scopeChain) {
      if (scope.type === 'local' || scope.type === 'closure') {
        const { result } = await Runtime.getProperties({
          objectId: scope.object.objectId, ownProperties: true
        });
        for (const p of result) {
          console.log(`  ${scope.type}.${p.name} =`, p.value?.value);
        }
      }
    }
    await Debugger.resume();
  });
  await Runtime.enable(); await Debugger.enable();
  await Debugger.setBreakpointByUrl({ urlRegex: '.*app\\.tsx$', lineNumber: 119 });
  await Runtime.runIfWaitingForDebugger();
})();
```

### Heap Snapshots & CPU Profiles

```javascript
// CPU profile for 5 seconds
await client.Profiler.enable();
await client.Profiler.start();
await new Promise(r => setTimeout(r, 5000));
const { profile } = await client.Profiler.stop();
fs.writeFileSync('/tmp/cpu.cpuprofile', JSON.stringify(profile));

// Heap snapshot
await client.HeapProfiler.enable();
const chunks = [];
client.HeapProfiler.addHeapSnapshotChunk(({ chunk }) => chunks.push(chunk));
await client.HeapProfiler.takeHeapSnapshot({ reportProgress: false });
fs.writeFileSync('/tmp/heap.heapsnapshot', chunks.join(''));
```

### Node.js Pitfalls

1. **Wrong line numbers in TS source.** Breakpoints hit emitted JS. Enable sourcemaps (`node --enable-source-maps`) or break in `dist/*.js`.
2. **`--inspect` vs `--inspect-brk`.** `--inspect` doesn't pause — script races past breakpoints if you attach too late.
3. **Port collisions.** Default is 9229. Use `--inspect=0` for random port, then read from `/json/list`.
4. **Child processes.** `--inspect` on parent does NOT inspect children. Use `NODE_OPTIONS='--inspect-brk'` to propagate.
5. **Background kills.** `Ctrl+C` out of `node inspect` while target is paused leaves target paused. `cont` first or `kill` explicitly.
6. **Security.** `--inspect=0.0.0.0` exposes arbitrary code execution. Always bind to `127.0.0.1`.

---

## Shared Verification Checklist

- [ ] Debugger port is listening: `ss -tlnp | grep 5678` (Python) or `curl -s http://127.0.0.1:9229/json/list` (Node)
- [ ] First breakpoint actually hits (check `PYTHONBREAKPOINT=0`, xdist, `--inspect-brk`)
- [ ] `where` / `bt` / `w` shows the expected call stack
- [ ] Post-debug cleanup: no stray `breakpoint()` / `set_trace()` / `debugger;` in committed code
- [ ] Source listing at pause shows the right file (Node: check sourcemap issues)
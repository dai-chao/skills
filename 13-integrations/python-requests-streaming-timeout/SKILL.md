---
name: python-requests-streaming-timeout
description: |
  Handle timeouts reliably when streaming with Python's `requests` library
  (SSE, long-polling, chunked responses). Covers why `response.close()` from
  a thread often fails to break `iter_lines()`, and how to use `signal.SIGALRM`
  or socket-level timeouts as robust alternatives.
metadata:
  version: "1.0.0"
---

# Python `requests` Streaming Timeout Pitfalls

## The Trap

You set up an SSE or streaming listener with `requests`:

```python
response = requests.get(url, headers=headers, stream=True, timeout=(10, 60))
```

Then you try to enforce a max runtime with `threading.Timer`:

```python
timer = Timer(110, response.close)
timer.start()

for line in response.iter_lines(decode_unicode=True):
    ...
```

**This does NOT work reliably.** `response.close()` from another thread does **not**
interrupt the blocking socket `recv()` that `iter_lines()` is waiting on. The main
thread hangs past the timer, and the process gets killed by an external watchdog
(e.g., cron 120 s timeout).

## Evidence

- `iter_lines()` stays blocked in `urllib3` → `socket.recv()`
- `Response.close()` sets internal flags but does not wake the socket
- `finally:` blocks may never execute if the process is SIGKILL'd

## Robust Solutions

### Option 1: `signal.SIGALRM` (Unix / macOS)

Best for scripts that run on Unix-like systems and need a hard deadline:

```python
import signal

class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException()

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(RUNTIME_SECONDS)   # e.g., 55

try:
    for raw_line in response.iter_lines(decode_unicode=True):
        if raw_line is None:
            continue
        # process line ...
except TimeoutException:
    pass
finally:
    signal.alarm(0)             # cancel alarm
    try:
        response.close()
    except Exception:
        pass
```

**Why this works:** `SIGALRM` delivers an exception into the main thread's
execution context, forcibly unwinding the stack even during a blocking read.

### Option 2: Socket-level read timeout

Use a short read timeout and let it raise naturally; catch and reconnect:

```python
# timeout=(connect_seconds, read_seconds)
response = requests.get(url, stream=True, timeout=(10, 30))

try:
    for line in response.iter_lines(decode_unicode=True):
        ...
except requests.exceptions.ReadTimeout:
    pass
finally:
    response.close()
```

**Trade-off:** You only get woken when the *next* read timeout fires, so average
latency to exit is `read_timeout / 2`.

### Option 3: Migrate to `httpx` or `aiohttp`

Modern HTTP clients support true cancellation:

```python
import httpx

with httpx.Client() as client:
    with client.stream("GET", url, headers=headers, timeout=30) as response:
        for line in response.iter_lines():
            ...
```

`httpx` streams can be cancelled with `asyncio` timeouts or `threading` +
`response.close()` much more reliably than `requests`.

## Cron / Scheduler Design Notes

If the streaming script is triggered by a cron-like scheduler:

1. **Runtime must be shorter than the scheduling interval.**
   - Example: run for 50–55 s, schedule every 60 s.
   - This prevents overlapping instances and resource leaks.

2. **Always leave headroom below the scheduler's hard kill timeout.**
   - If the scheduler kills at 120 s, aim to exit by 110 s at the latest.

3. **Log both start and end.**
   - If the log only ever shows start lines, the script is hanging — exactly the
     symptom of the `response.close()` trap.

## Checklist

- [ ] Do NOT rely on `Timer(response.close)` to stop `requests.iter_lines()`.
- [ ] Use `signal.SIGALRM`, short read timeouts, or a modern async client.
- [ ] Ensure `RUNTIME < SCHEDULE_INTERVAL < HARD_KILL_TIMEOUT`.
- [ ] Verify logs show both connection start and clean disconnect.

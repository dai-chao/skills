---
name: js-tdz-init-order
description: Avoid JavaScript Temporal Dead Zone (TDZ) blackscreens in ES modules by correctly ordering init calls relative to let/const declarations.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [javascript, es-module, tdz, threejs, blackscreen, debugging]
    related_skills: [systematic-debugging, threejs-browser-game-prototype]
---

# JavaScript TDZ Init-Order Trap

## The Trap

In an ES module (`<script type="module">` or `.js` module), placing `init()` / `animate()` calls at the top of the file while `let`/`const` variables are declared further down causes a **Temporal Dead Zone (TDZ)** error.

The function executes synchronously, reaches a helper that references the not-yet-initialized `let` variable, and throws:

```
Cannot access 'inspectObj' before initialization
```

Because this often happens inside `requestAnimationFrame`-driven render loops or event handlers (`click`, `keydown`, etc.), the exception kills the animation or interaction before anything is drawn → **black screen**.

## When It Happens

- You add new `let`/`const` variables in the middle or bottom of a module.
- Your `init(); animate();` (or `main();`) calls are near the top of the file.
- The init/animate chain synchronously calls a function that closes over the later variable.

Common in: Three.js games, Canvas apps, p5.js sketches, vanilla JS modules.

## Quick Diagnosis

1. Open browser DevTools → Console.
2. Look for `ReferenceError` or `Cannot access 'X' before initialization`.
3. Check the line number of the thrown error vs. the line number of the variable declaration.
4. If the error line is **before** the declaration line in the same module scope → TDZ.

## Fix

**Option A — Move init calls to the bottom (preferred):**

```javascript
// ❌ BAD: init runs before inspectObj is declared
init();
animate();

let inspectObj = null;   // ← never reached because init() threw
```

```javascript
let inspectObj = null;
// ... rest of module ...

init();   // ✅ GOOD: all let/const are initialized
animate();
```

**Option B — Hoist the declaration above the init call:**

```javascript
let inspectObj = null;
init();
animate();
```

## Prevention

- Always keep `init()` / `main()` / `animate()` calls at the **very end** of the module.
- If a linter is available, TDZ errors are usually caught statically, but runtime-only code paths (callbacks inside `requestAnimationFrame`) may evade static analysis.
- When reviewing a module, scan for top-level function calls that precede `let`/`const` declarations.

## Real-World Example

```javascript
// main.js
init();          // starts loop immediately
animate();

function animate() {
    updateInspect();   // references inspectObj
    requestAnimationFrame(animate);
}

// ... hundreds of lines later ...
let inspectObj = null;   // TDZ! animate() accessed this before it was initialized
```

Moving `init(); animate();` to the file bottom fixes the blackscreen instantly.

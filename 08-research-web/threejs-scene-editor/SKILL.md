---
title: Three.js In-Browser Scene Editor
description: Add interactive drag/rotate editing to a Three.js scene using TransformControls, allowing real-time furniture positioning and coordinate export to console. Solves the painful workflow of guessing hardcoded positions in code.
name: threejs-scene-editor
trigger:
  - Setting up a Three.js scene with many placed models
  - User wants to rearrange 3D objects without editing code
  - Need to export final positions/rotations from browser to code
  - Using PointerLockControls (FPS camera) alongside editor needs
---

# Three.js In-Browser Scene Editor

## Goal
Let the user click, drag, and rotate loaded models directly in the browser, then export all coordinates as JSON via the console so the developer can paste them back into the source code.

## When to Use
- Scene setup phase with many hardcoded model positions (escape rooms, interior design, levels)
- User complains furniture/placement looks messy or wants to tweak layout
- You want to avoid the edit-save-refresh-guess cycle for coordinates

## Steps

### 1. Import TransformControls
```js
import { TransformControls } from 'three/addons/controls/TransformControls.js';
```

### 2. Declare Globals
```js
let transformControl;
let isEditMode = false;
```

### 3. Initialize in `init()`
Create after renderer, before PointerLockControls. Attach `dragging-changed` listener to disable FPS controls while dragging so they don't fight.

```js
transformControl = new TransformControls(camera, renderer.domElement);
transformControl.addEventListener('dragging-changed', function (event) {
    controls.enabled = !event.value;
});
scene.add(transformControl);
transformControl.visible = false;
```

### 4. Toggle Edit Mode (KeyE)
When entering edit mode: unlock PointerLockControls so the mouse is free. When exiting: detach TransformControls and re-lock FPS camera.

**Also prevent PointerLockControls from re-locking automatically while editing.** `PointerLockControls` listens for clicks on its domElement and calls `lock()` whenever it sees a click while unlocked. This silently re-locks the mouse the instant the user tries to drag a TransformControls gizmo, breaking the drag. Override `controls.lock()` to ignore requests during edit mode:

```js
// After creating controls = new PointerLockControls(camera, document.body);
const originalLock = controls.lock.bind(controls);
controls.lock = function() {
    if (isEditMode) return;
    originalLock();
};
```

Then handle KeyE:

```js
case 'KeyE':
    e.preventDefault();
    isEditMode = !isEditMode;
    if (isEditMode) {
        controls.unlock();
        transformControl.visible = true;
        showMessage('Edit mode: click model to select, T toggle translate/rotate, ESC/E exit');
    } else {
        transformControl.detach();
        transformControl.visible = false;
        controls.lock();
    }
    break;
```

### 5. Toggle Translate / Rotate (KeyT)
Only active while in edit mode.

```js
case 'KeyT':
    if (isEditMode) {
        e.preventDefault();
        const mode = transformControl.mode === 'translate' ? 'rotate' : 'translate';
        transformControl.setMode(mode);
        showMessage('Mode: ' + mode);
    }
    break;
```

### 6. Model Selection via Raycaster
In your click handler (or `onInteract`), branch on `isEditMode`. Cast against the whole scene, **filter out TransformControls and its internal gizmos first** (clicking the gizmo itself causes an infinite recursion/stack overflow), then recurse up the parent chain until you hit either the scene root or an object marked as furniture.

```js
if (isEditMode) {
    raycaster.setFromCamera(new THREE.Vector2(0, 0), camera);
    const hits = raycaster.intersectObjects(scene.children, true);
    // CRITICAL: exclude TransformControls and its handles from selection
    const validHits = hits.filter(h => {
        let p = h.object;
        while (p) {
            if (p === transformControl) return false;
            p = p.parent;
        }
        return true;
    });
    if (validHits.length > 0) {
        let obj = validHits[0].object;
        while (obj.parent && obj.parent !== scene && !obj.userData.isFurniture) {
            obj = obj.parent;
        }
        if (obj.userData.isFurniture) {
            transformControl.detach();
            transformControl.attach(obj);
            console.log('Selected:', obj.name || obj.userData.source, obj.position, obj.rotation, obj.scale);
        }
    }
    return;
}
```

### 7. Mark Every Loaded Model as Furniture
When a GLTF model loads, tag it so the raycaster and exporter know it's a placed object. Also store the source filename for identification.

```js
const model = gltf.scene;
model.traverse(c => {
    if (c.isMesh) {
        c.castShadow = false;   // keep perf reasonable
        c.receiveShadow = true;
    }
});
model.userData.isFurniture = true;
model.userData.source = pathOrFilename;  // e.g. 'chair.glb'
```

### 8. Export Function
Expose a global function the user can run in the browser console after arranging everything.

```js
window.exportPositions = function () {
    const list = [];
    scene.traverse((obj) => {
        if (obj.userData.isFurniture) {
            list.push({
                name: obj.name || obj.userData.source || 'unnamed',
                position: [obj.position.x, obj.position.y, obj.position.z],
                rotation: [obj.rotation.x, obj.rotation.y, obj.rotation.z],
                scale: [obj.scale.x, obj.scale.y, obj.scale.z]
            });
        }
    });
    console.log(JSON.stringify(list, null, 2));
    return list;
};
```

User copies the console JSON and sends it to you; you paste the coordinates back into the code.

## Pitfalls
- **PointerLockControls re-locks on every click while unlocked**: When you click a TransformControls gizmo after `controls.unlock()`, PointerLockControls sees the click and calls `lock()` again, instantly breaking the drag. **Do NOT** try to fix this with `renderer.domElement.addEventListener('mousedown', e => e.stopPropagation(), true)` in capture phase — that will also block TransformControls' own mousedown handler, making gizmos completely undraggable. The clean fix is overriding `controls.lock()` to no-op during edit mode (see Step 4).
- **Raycaster hits the TransformControls gizmo itself**: If you intersect against `scene.children` without filtering, clicking a translation arrow or rotation ring can select the gizmo group, causing `transformControl.attach(gizmo)` which triggers `Maximum call stack size exceeded` inside `updateMatrixWorld`. Always filter out hits whose parent chain includes `transformControl` before choosing the object to attach.
- **PointerLockControls locked mouse prevents clicking**: Always `controls.unlock()` before enabling edit mode.
- **TransformControls and PointerLockControls fight over mouse**: Use the `dragging-changed` event to temporarily `controls.enabled = !event.value`.
- **Raycaster hits a Mesh inside a Group**: The while-loop (`while obj.parent && obj.parent !== scene && !obj.userData.isFurniture`) walks up to the furniture root. Without this you try to attach a single mesh instead of the whole model group.
- **Models lack identification**: If you don't set `userData.source` or `name`, the export list is full of "unnamed". Set the filename or a human-readable name at load time.
- **Scene.children raycaster is broad**: It will hit lights, helpers, terrain, walls. The `isFurniture` guard prevents attaching the floor or sky. Do not fall back to `obj.parent === scene` as a selection criterion — that catches walls, terrain, and lights too.
- **Blocker overlay blocks clicks after unlock**: If you have a "click to start" blocker that appears on `unlock()`, it will cover the canvas and intercept all mouse events, preventing TransformControls from working. Hide the blocker when entering edit mode.
- **WASD movement stops in edit mode**: The animate loop may guard movement with `if (controls.isLocked)`. After `controls.unlock()`, WASD stops working. Change the guard to `if (controls.isLocked || isEditMode)` so the player can still walk around while editing.
- **Re-attaching the same object causes flicker**: In the click handler, guard against re-attaching the already-selected object: `if (transformControl.object === obj) return;`.

## Variations

### A. Distance limit
Add a max distance check (e.g. `hits[0].distance > 5`) if you only want to select nearby objects.

### B. Grid snap
After dragging, round positions to 0.5 or 1.0 units for clean level design.

### C. Arrow-key micro-adjustment
For precise alignment, let arrow keys nudge the selected object while in edit mode, keeping WASD for camera movement:

```js
case 'ArrowUp':
    if (isEditMode && transformControl.object) {
        e.preventDefault();
        transformControl.object.position.z -= 0.05;
    } else {
        moveForward = true;
    }
    break;
// ... repeat for ArrowDown/Left/Right
```

### D. Full localStorage persistence (auto-restore on reload)
Instead of manually copying console JSON, auto-save to `localStorage` and restore positions on every page load. This supports multiple instances of the same model (e.g., 60 fence segments) using a per-source counter.

**Export side:**
```js
window.exportPositions = function () {
    const list = [];
    scene.traverse((obj) => {
        if (obj.userData.isFurniture) {
            list.push({
                name: obj.name || obj.userData.source || 'unnamed',
                source: obj.userData.source || '',
                position: [obj.position.x, obj.position.y, obj.position.z],
                rotation: [obj.rotation.x, obj.rotation.y, obj.rotation.z],
                scale: [obj.scale.x, obj.scale.y, obj.scale.z]
            });
        }
    });
    const json = JSON.stringify(list, null, 2);
    console.log(json);
    try {
        localStorage.setItem('three_positions', json);
    } catch (e) { console.error('localStorage save failed', e); }
    return list;
};
```

**Restore side:**
```js
const savedPositions = (() => {
    try { const raw = localStorage.getItem('three_positions'); return raw ? JSON.parse(raw) : null; }
    catch (e) { return null; }
})();
const placementCounters = {};

function applySavedPosition(model, source) {
    if (!savedPositions || !source) return;
    if (!placementCounters[source]) placementCounters[source] = 0;
    const idx = placementCounters[source]++;
    const matches = savedPositions.filter(p => p.source === source || p.name === source);
    if (idx < matches.length) {
        const p = matches[idx];
        model.position.set(...p.position);
        model.rotation.set(...p.rotation);
        model.scale.set(...p.scale);
    }
}
```

Call `applySavedPosition(model, path)` inside every loader callback (`GLTFLoader.load`, `placeModel`, `placeKenney`) after `scene.add(model)` and position calculation.

**For manually-created primitives** (placeholder boxes, procedural furniture), batch-mark them and restore by `name`:

```js
const manualFurniture = [table, sofa, bed, fridge, ...];
manualFurniture.forEach(obj => {
    if (!obj) return;
    obj.userData.isFurniture = true;
    if (savedPositions) {
        const p = savedPositions.find(sp => sp.name === obj.name);
        if (p) {
            obj.position.set(...p.position);
            obj.rotation.set(...p.rotation);
            obj.scale.set(...p.scale);
        }
    }
});
```

### E. Default positions from JSON file + localStorage override (large scenes)
For scenes with 200+ objects, inlining JSON into the JS bundle is impractical. Store defaults in `assets/default-positions.json` and load via `fetch`. localStorage acts as an optional user override layer.

Make `init()` async and load coordinates before any model placement:

```js
let savedPositions = null;

async function init() {
    try {
        const resp = await fetch('assets/default-positions.json');
        const defaultPositions = await resp.json();
        const custom = localStorage.getItem('three_positions');
        savedPositions = custom ? JSON.parse(custom) : defaultPositions;
    } catch (e) {
        console.error('Failed to load default positions', e);
        const custom = localStorage.getItem('three_positions');
        savedPositions = custom ? JSON.parse(custom) : null;
    }

    scene = new THREE.Scene();
    // ... rest of init
}
```

Workflow:
1. Developer arranges scene, runs `exportPositions()` → saves JSON to `assets/default-positions.json`
2. User loads page → gets default layout
3. User tweaks in edit mode, runs `exportPositions()` → saved to localStorage
4. Refresh → localStorage overrides defaults
5. Clear localStorage to revert to defaults

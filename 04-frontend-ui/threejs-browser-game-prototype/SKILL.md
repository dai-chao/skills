---
name: threejs-browser-game-prototype
description: Rapidly prototype a browser-based 3D game with Three.js using CDN (no build tools), including first-person controls, collision detection, raycaster interactions, and asset optimization pipelines.
trigger: When building a 3D web game, Three.js prototype, or browser-based interactive 3D experience without a build step.
---

# Three.js Browser Game Prototyping

## 1. Project Setup (No Build Tools)

Use CDN imports via `importmap` so the project runs by simply opening `index.html` with a local server.

```html
<script type="importmap">
{
    "imports": {
        "three": "https://unpkg.com/three@0.160.0/build/three.module.js",
        "three/addons/": "https://unpkg.com/three@0.160.0/examples/jsm/"
    }
}
</script>
```

Structure:
```
project/
├── index.html
├── main.js
├── style.css
└── assets/
    ├── textures/
    ├── sounds/
    └── models/
```

Serve with `python3 -m http.server 8000` or VS Code Live Server.

## 2. First-Person Controller + AABB Collision

Avoid physics engines for simple scenes. Use `PointerLockControls` with custom AABB collision.

```javascript
import { PointerLockControls } from 'three/addons/controls/PointerLockControls.js';

const colliders = []; // { minX, maxX, minY, maxY, minZ, maxZ, disabled }
const PLAYER_RADIUS = 0.4;

function addBoxCollider(x, y, z, sx, sy, sz, name = null) {
    colliders.push({
        minX: x - sx / 2, maxX: x + sx / 2,
        minY: y - sy / 2, maxY: y + sy / 2,
        minZ: z - sz / 2, maxZ: z + sz / 2,
        disabled: false,
        name: name
    });
}

function checkCollision(x, y, z) {
    for (const c of colliders) {
        if (c.disabled) continue;
        if (x + PLAYER_RADIUS > c.minX && x - PLAYER_RADIUS < c.maxX &&
            y > c.minY && y < c.maxY &&
            z + PLAYER_RADIUS > c.minZ && z - PLAYER_RADIUS < c.maxZ) {
            return c;
        }
    }
    return null;
}

// In animation loop:
const forward = new THREE.Vector3();
camera.getWorldDirection(forward);
forward.y = 0; forward.normalize();
const right = new THREE.Vector3();
right.crossVectors(forward, new THREE.Vector3(0, 1, 0)).normalize();

const moveDir = new THREE.Vector3(0,0,0);
if (moveForward) moveDir.add(forward);
if (moveBackward) moveDir.sub(forward);
if (moveRight) moveDir.add(right);
if (moveLeft) moveDir.sub(right);

if (moveDir.lengthSq() > 0) {
    moveDir.normalize();
    const mx = moveDir.x * speed * delta;
    const mz = moveDir.z * speed * delta;
    const py = camera.position.y;
    if (!checkCollision(camera.position.x + mx, py, camera.position.z)) camera.position.x += mx;
    if (!checkCollision(camera.position.x, py, camera.position.z + mz)) camera.position.z += mz;
}
```

Pitfall: Do NOT use `controls.moveRight()` with world-space offsets. Calculate movement vectors manually and set `camera.position` directly.

## 3. Raycaster Interaction System

Center-screen raycast (crosshair-based) for first-person games.

```javascript
const raycaster = new THREE.Raycaster();
raycaster.setFromCamera(new THREE.Vector2(0, 0), camera);
const hits = raycaster.intersectObjects(interactables, true);

if (hits.length > 0 && hits[0].distance < 2.5) {
    let obj = hits[0].object;
    while (obj.parent && !obj.userData.type) obj = obj.parent;
    // interact with obj.userData.type
}
```

Store interaction metadata on `userData`:
```javascript
mesh.userData = { type: 'door', label: '门' };
```

### Inspectable Object System (Zoom-to-View)
A reusable "examine" mechanic: click an object to smoothly fly it to the camera, click again to return it and trigger pickup.

```javascript
let inspectObj = null;
let inspectOriginal = { pos: null, quat: null, scale: null };
let inspectTarget = { pos: null, quat: null, scale: null };
let inspectProgress = 0;
const INSPECT_DURATION = 0.5;

function startInspect(obj, text) {
    inspectObj = obj;
    controls.unlock();
    gameState.isInspecting = true;
    inspectOriginal.pos = obj.position.clone();
    inspectOriginal.quat = obj.quaternion.clone();
    inspectOriginal.scale = obj.scale.clone();

    const offset = new THREE.Vector3(0, 0, -0.45);
    offset.applyQuaternion(camera.quaternion);
    inspectTarget.pos = camera.position.clone().add(offset);
    inspectTarget.quat = camera.quaternion.clone();
    inspectTarget.scale = obj.scale.clone().multiplyScalar(4);

    inspectProgress = 0;
    showInspectUI(text);
}

function updateInspect(delta) {
    if (!inspectObj) return;
    inspectProgress += delta / INSPECT_DURATION;
    if (inspectProgress > 1) inspectProgress = 1;
    const ease = 1 - Math.pow(1 - inspectProgress, 3);
    inspectObj.position.lerpVectors(inspectOriginal.pos, inspectTarget.pos, ease);
    inspectObj.quaternion.slerpQuaternions(inspectOriginal.quat, inspectTarget.quat, ease);
    inspectObj.scale.lerpVectors(inspectOriginal.scale, inspectTarget.scale, ease);
}

function endInspect() {
    if (!inspectObj) return;
    // Animate back (simplified: direct lerp back over a few frames)
    inspectObj.position.copy(inspectOriginal.pos);
    inspectObj.quaternion.copy(inspectOriginal.quat);
    inspectObj.scale.copy(inspectOriginal.scale);
    inspectObj = null;
    gameState.isInspecting = false;
    hideInspectUI();
    controls.lock();
}
```

**Pitfall — Flat Objects (e.g., paper notes):**
The code above copies `camera.quaternion`, which works for cubes but fails for flat objects like a paper note (`BoxGeometry(0.25, 0.01, 0.18)`). The thin Y-axis faces the camera, making it invisible. Fix by rotating so the XZ plane (the wide face) points at the camera:

```javascript
function startInspect(obj, text) {
    // ...save original state...
    const targetPos = new THREE.Vector3(0, -0.05, -0.5);
    targetPos.applyQuaternion(camera.quaternion);
    targetPos.add(camera.position);

    const dummy = new THREE.Object3D();
    dummy.position.copy(targetPos);
    dummy.lookAt(camera.position);
    dummy.rotateX(Math.PI / 2); // Y-axis now points at camera
    inspectTarget.quat = dummy.quaternion.clone();

    inspectTarget.scale = obj.scale.clone().multiplyScalar(5);
    inspectTarget.pos = targetPos;
    // ...rest of setup...
}
```

In `onInteract()`, check `gameState.isInspecting` first so a second click closes the inspection. Add `updateInspect(delta)` in the animation loop. Any object with `userData.inspectable = true` can use this system.

## 4. Puzzle State Machine

Keep game state in a plain object, not scattered across meshes.

```javascript
const gameState = {
    hasNote: false,
    boxOpened: false,
    hasKey: false,
    doorOpened: false
};
```

Each interaction checks state before acting. This makes debugging and extending trivial.

## 5. PBR Texture Loading

Use a helper to keep material setup clean.

```javascript
const texLoader = new THREE.TextureLoader();
function loadMat(paths, overrides = {}) {
    const mat = new THREE.MeshStandardMaterial({
        map: paths.color ? texLoader.load(paths.color) : null,
        roughnessMap: paths.roughness ? texLoader.load(paths.roughness) : null,
        normalMap: paths.normal ? texLoader.load(paths.normal) : null,
        ...overrides
    });
    if (mat.map) mat.map.colorSpace = THREE.SRGBColorSpace;
    return mat;
}
```

Source textures from [ambientCG](https://ambientcg.com) (CC0). Download the Zip which contains `_Color.jpg`, `_Roughness.jpg`, `_NormalGL.jpg`.

### Batch Downloading from ambientCG via curl
ambientCG blocks raw curl without a User-Agent. Use this Python pattern:

```python
import urllib.request, zipfile, shutil, os

def download_ambient(name, out_dir):
    url = f"https://ambientcg.com/get?file={name}_1K-JPG.zip"
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    })
    zip_path = f"/tmp/{name}.zip"
    with urllib.request.urlopen(req, timeout=30) as resp:
        with open(zip_path, 'wb') as f:
            f.write(resp.read())
    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall(out_dir)
    # Flatten subdirectories
    for sub in os.listdir(out_dir):
        subpath = os.path.join(out_dir, sub)
        if os.path.isdir(subpath):
            for f in os.listdir(subpath):
                shutil.move(os.path.join(subpath, f), os.path.join(out_dir, f))
            os.rmdir(subpath)
    os.remove(zip_path)
```

### Kenney.nl GLB Models — Full Workflow
Kenney assets are CC0, low-poly, and include ready-to-use `.glb` files. This is the fastest way to populate a Three.js scene with trees, furniture, rocks, etc.

**Step 1 — Browse and reveal the direct download link**
Visit `https://kenney.nl/assets/<kit-name>` (e.g. `nature-kit`, `furniture-kit`). Click **Download** → a donation dialog pops up. Click **"Continue without donating..."** to reveal the raw `.zip` URL (e.g. `https://kenney.nl/media/pages/assets/nature-kit/.../kenney_nature-kit.zip`).

**Step 2 — Download with curl**
```bash
curl -L -o kenney_nature-kit.zip "<direct-zip-url>"
```

**Step 3 — Extract and inspect**
Kenney ZIPs often extract **without a top-level folder** — files scatter into the current directory (`models/`, `Isometric/`, `Side/`, etc.). Always list before copying:
```bash
unzip -q kenney_nature-kit.zip
ls models/GLTF\ format/ | head -20
```

**Step 4 — Copy to project assets**
Move only the `.glb` files your project needs into the loader's search path:
```bash
cp models/GLTF\ format/*.glb assets/models/Models/GLTF\ format/
```
Cleanup the leftover folders (`Side/`, `Isometric/`, `models/FBX format/`, etc.) to keep the project tidy.

**Step 5 — Load in code**
Reuse the existing `placeKenney` helper (or equivalent) to batch-place models. Kenney Nature Kit contains 300+ files covering trees, flowers, grass, rocks, fences, bridges, campfires, cacti, and paths.

**Example — rich garden with Kenney Nature Kit:**
```javascript
// ========== 花园自然景观 ==========
// 大树（分散在花园外围）
const bigTrees = [
    ['tree_default.glb', -12, -8, 2.0, 3.0],
    ['tree_detailed.glb', 20, -6, 2.0, 3.0],
    ['tree_oak.glb', -10, 15, 2.5, 3.5],
    ['tree_fat.glb', 22, 12, 2.5, 3.0],
    ['tree_tall.glb', -15, 0, 1.5, 3.5],
    ['tree_thin.glb', 18, 18, 1.2, 2.5],
];
bigTrees.forEach(([f, x, z, w, h]) =>
    placeKenney(f, new THREE.Vector3(w, h, w), new THREE.Vector3(x, 0, z), null, Math.random() * Math.PI * 2));

// 松树
const pines = [
    ['tree_pineDefaultA.glb', -6, -8, 1.5, 2.5],
    ['tree_pineRoundA.glb', -12, 8, 1.2, 2.0],
    ['tree_pineTallA.glb', -5, 18, 1.5, 3.0],
];
pines.forEach(([f, x, z, w, h]) =>
    placeKenney(f, new THREE.Vector3(w, h, w), new THREE.Vector3(x, 0, z), null, Math.random() * Math.PI * 2));

// 花圃
for (let i = 0; i < 6; i++) {
    const fx = ['flower_redA.glb', 'flower_redB.glb', 'flower_redC.glb'][i % 3];
    placeKenney(fx, new THREE.Vector3(0.25, 0.3, 0.25),
        new THREE.Vector3(-9 + (i % 3) * 0.4, 0, 10 + Math.floor(i / 3) * 0.4), null, Math.random() * 0.5);
}

// 草丛（随机散布，避开房子内部）
const grassFiles = ['grass.glb', 'grass_large.glb', 'grass_leafs.glb'];
for (let i = 0; i < 30; i++) {
    const f = grassFiles[Math.floor(Math.random() * grassFiles.length)];
    const x = (Math.random() - 0.5) * 45;
    const z = (Math.random() - 0.5) * 45;
    if (x > -5 && x < 15 && z > -5 && z < 15) continue; // 跳过房子
    placeKenney(f, new THREE.Vector3(0.5, 0.5, 0.5), new THREE.Vector3(x, 0, z), null, Math.random() * Math.PI * 2);
}

// 灌木丛
const bushes = [
    ['plant_bush.glb', -9, 6, 0.8],
    ['plant_bushLarge.glb', 19, -5, 1.0],
    ['plant_bushSmall.glb', -11, 18, 0.6],
];
bushes.forEach(([f, x, z, s]) =>
    placeKenney(f, new THREE.Vector3(s, s, s), new THREE.Vector3(x, 0, z), null, Math.random() * Math.PI * 2));

// 石头
placeKenney('rock_largeA.glb', new THREE.Vector3(2, 1.5, 2), new THREE.Vector3(-14, 0, 10), null);
placeKenney('rock_largeB.glb', new THREE.Vector3(2.5, 2, 2.5), new THREE.Vector3(19, 0, -8), null);
for (let i = 0; i < 15; i++) {
    const rocks = ['rock_smallA.glb', 'rock_smallB.glb', 'rock_smallC.glb'];
    const f = rocks[Math.floor(Math.random() * rocks.length)];
    const x = (Math.random() - 0.5) * 40;
    const z = (Math.random() - 0.5) * 40;
    if (x > -4 && x < 14 && z > -4 && z < 14) continue;
    placeKenney(f, new THREE.Vector3(0.6, 0.4, 0.6), new THREE.Vector3(x, 0, z), null, Math.random() * Math.PI * 2);
}

// 树桩、原木、蘑菇
placeKenney('stump_old.glb', new THREE.Vector3(0.8, 0.8, 0.8), new THREE.Vector3(-7, 0, 16), null);
placeKenney('log.glb', new THREE.Vector3(1, 0.4, 0.4), new THREE.Vector3(-8, 0, 14), null);
placeKenney('mushroom_red.glb', new THREE.Vector3(0.3, 0.3, 0.3), new THREE.Vector3(-9, 0, 14), null);

// 木栅栏
for (let i = -15; i <= 25; i += 1.2) {
    placeKenney('fence_simple.glb', new THREE.Vector3(1, 0.8, 0.15), new THREE.Vector3(i, 0, -12), null);
    placeKenney('fence_simple.glb', new THREE.Vector3(1, 0.8, 0.15), new THREE.Vector3(i, 0, 22), null);
}
for (let i = -12; i <= 22; i += 1.2) {
    placeKenney('fence_simple.glb', new THREE.Vector3(0.15, 0.8, 1), new THREE.Vector3(-15, 0, i), null);
    placeKenney('fence_simple.glb', new THREE.Vector3(0.15, 0.8, 1), new THREE.Vector3(25, 0, i), null);
}
placeKenney('fence_gate.glb', new THREE.Vector3(1.2, 0.9, 0.2), new THREE.Vector3(2, 0, 22), null);

// 木桥、营火、仙人掌
placeKenney('bridge_wood.glb', new THREE.Vector3(2, 1, 1.5), new THREE.Vector3(5, 0, 18), null);
placeKenney('campfire_logs.glb', new THREE.Vector3(1, 0.5, 1), new THREE.Vector3(-5, 0, 18), null);
placeKenney('campfire_stones.glb', new THREE.Vector3(1.2, 0.3, 1.2), new THREE.Vector3(-5, 0, 18), null);
placeKenney('cactus_short.glb', new THREE.Vector3(0.5, 0.8, 0.5), new THREE.Vector3(20, 0, 20), null);

// 石头小径
for (let i = 0; i < 8; i++) {
    placeKenney('path_stone.glb', new THREE.Vector3(0.6, 0.1, 0.6),
        new THREE.Vector3(2 + i * 0.6 + (Math.random() - 0.5) * 0.2, 0, 17 + i * 0.4), null, Math.random() * 0.3);
}
```

### UV Alignment for Segmented Walls
When a wall is split into segments (e.g., around a door), BoxGeometry UVs reset to 0-1 per mesh, breaking texture continuity. Fix by computing world-space UVs for the +z face:

```javascript
function alignWallUV(geometry, position, size, totalW, totalH) {
    const posAttr = geometry.attributes.position;
    const uvAttr = geometry.attributes.uv;
    const hd = size.z / 2;
    for (let i = 0; i < posAttr.count; i++) {
        const x = posAttr.getX(i), y = posAttr.getY(i), z = posAttr.getZ(i);
        if (Math.abs(z - hd) < 0.001) { // +z face only
            const wx = x + position.x;
            const wy = y + position.y;
            uvAttr.setXY(i, (wx + totalW / 2) / totalW, wy / totalH);
        }
    }
    uvAttr.needsUpdate = true;
}
```

## 6. Asset Optimization Pipeline

### Images (macOS)
Batch resize 8K textures down to 1K/2K for web using native `sips`:
```bash
cd assets/textures
find . -type f \( -name "*.jpg" -o -name "*.png" \) | while read f; do
    sips -Z 1024 "$f" --out "$f.tmp" && mv "$f.tmp" "$f"
done
```

### Audio
Use `ffmpeg` to compress WAV to MP3 for web:
```bash
cd assets/sounds
for f in *.wav; do
    ffmpeg -i "$f" -codec:a libmp3lame -q:a 4 "${f%.wav}.mp3"
done
rm *.wav
```

## 7. Web Audio API for Game Sounds

Use `AudioContext` + `decodeAudioData` for low-latency playback.

```javascript
const audioCtx = new (window.AudioContext || window.webkitAudioContext));
const sounds = {};

async function loadSounds(files) {
    await Promise.all(Object.entries(files).map(async ([name, url]) => {
        const buf = await fetch(url).then(r => r.arrayBuffer());
        sounds[name] = await audioCtx.decodeAudioData(buf);
    }));
}

function playSound(name, volume = 1.0) {
    if (!sounds[name]) return;
    const src = audioCtx.createBufferSource();
    src.buffer = sounds[name];
    const gain = audioCtx.createGain();
    gain.gain.value = volume;
    src.connect(gain).connect(audioCtx.destination);
    src.start(0);
}
```

Resume context on user interaction (required by browsers):
```javascript
blocker.addEventListener('click', () => {
    if (audioCtx.state === 'suspended') audioCtx.resume();
    controls.lock();
});
```

### Footsteps
Trigger footsteps at intervals while moving, not every frame:

```javascript
let lastFootstepTime = 0;
const FOOTSTEP_INTERVAL = 0.45;

if (moveDir.lengthSq() > 0) {
    // ...collision & movement...
    const now = performance.now() / 1000;
    if (now - lastFootstepTime > FOOTSTEP_INTERVAL) {
        lastFootstepTime = now;
        playSound('footstep', 0.35);
    }
}
```

## 8. GLTF Model Integration (Preserving Animation)

When replacing placeholder boxes with GLTF models while keeping existing animations (e.g., door rotation), attach the model as a child of the original mesh and hide the original geometry.

```javascript
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

function hideMesh(obj) {
    obj.traverse(c => {
        if (c.isMesh && c.material) {
            (Array.isArray(c.material) ? c.material : [c.material]).forEach(m => {
                m.transparent = true; m.opacity = 0; m.depthWrite = false;
            });
        }
    });
}

// Door: model follows parent rotation automatically
gltfLoader.load('door.gltf', (gltf) => {
    const model = gltf.scene;
    // Compute scale to fit target size
    const box = new THREE.Box3().setFromObject(model);
    const size = new THREE.Vector3(); box.getSize(size);
    const scale = Math.min(targetW / size.x, targetH / size.y, targetD / size.z);
    model.scale.setScalar(scale);
    
    doorMesh.add(model);
    // Shift so model's left edge aligns with parent's origin (hinge)
    const center = new THREE.Vector3(); box.getCenter(center);
    model.position.set(0.5 * targetW - center.x * scale, -center.y * scale, -center.z * scale);
    
    hideMesh(doorMesh); // Original box becomes invisible collision/animation proxy
});
```

For static replacements (table, safe), add to scene directly and swap the `interactables` reference:

```javascript
const idx = interactables.indexOf(oldSafeGroup);
if (idx > -1) interactables[idx] = newModel;
```

### Door Group Rotation Pattern (Robust)
When a door has an external GLTF model attached as a sibling of the placeholder mesh, wrap BOTH in a `THREE.Group`. Store `baseRot` (closed angle) and `openRot` on `userData`, then animate the **group's** rotation. This keeps the external model and the proxy mesh aligned.

```javascript
function createDoor(name, x, y, z, rotY, width, height, thickness, mat, isLocked) {
    const group = new THREE.Group();
    group.position.set(x, y, z);
    group.rotation.y = rotY;

    const geo = new THREE.BoxGeometry(width, height, thickness);
    geo.translate(width / 2, height / 2, 0);
    const mesh = new THREE.Mesh(geo, mat);
    mesh.name = '_door_mesh';
    group.add(mesh);

    group.userData = {
        type: 'door',
        isLocked: isLocked,
        isOpen: false,
        colliderIndex: colliders.length,
        baseRot: rotY,
        openRot: rotY - Math.PI / 2
    };
    scene.add(group);
    interactables.push(group);

    // Collider based on orientation
    if (rotY === 0 || Math.abs(rotY - Math.PI) < 0.1) {
        colliders.push({ minX: x, maxX: x + width, minZ: z - thickness/2 - 0.05, maxZ: z + thickness/2 + 0.05, disabled: false });
    } else {
        colliders.push({ minX: x - thickness/2 - 0.05, maxX: x + thickness/2 + 0.05, minZ: z, maxZ: z + width, disabled: false });
    }
    return group;
}

function toggleDoor(doorGroup) {
    const data = doorGroup.userData;
    const isOpen = data.isOpen;
    data.isOpen = !isOpen;
    const startRot = doorGroup.rotation.y;
    const targetRot = isOpen ? data.baseRot : data.openRot;

    let t = 0;
    function step() {
        t += 0.03;
        if (t > 1) t = 1;
        const ease = 1 - Math.pow(1 - t, 3);
        doorGroup.rotation.y = startRot + (targetRot - startRot) * ease;
        if (t < 1) requestAnimationFrame(step);
        else {
            const ci = data.colliderIndex;
            if (ci !== undefined && colliders[ci]) colliders[ci].disabled = data.isOpen;
        }
    }
    step();
}
```

Load the external door model as a child of the group, then hide only `_door_mesh` so the visual model remains:

```javascript
gltfLoader.load('door.gltf', (gltf) => {
    const model = gltf.scene;
    // ...scale & position...
    doorGroup.add(model);
    const oldMesh = doorGroup.getObjectByName('_door_mesh');
    if (oldMesh) hideMesh(oldMesh);
});
```

### CanvasTexture for In-World Readable Text
For escape-room notes, letters, or signs, generate a `CanvasTexture` on the fly instead of relying on DOM overlays. This makes text readable even when the object is not in "inspect mode."

```javascript
function createNoteTexture(text) {
    const canvas = document.createElement('canvas');
    canvas.width = 512;
    canvas.height = 256;
    const ctx = canvas.getContext('2d');

    // Aged paper background
    ctx.fillStyle = '#f5e6c8';
    ctx.fillRect(0, 0, 512, 256);

    // Handwritten text
    ctx.fillStyle = '#3d2817';
    ctx.font = 'bold 120px "Comic Sans MS", cursive, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.save();
    ctx.translate(256, 128);
    ctx.rotate((Math.random() - 0.5) * 0.1); // slight slant
    ctx.fillText(text, 0, 0);
    ctx.restore();

    const tex = new THREE.CanvasTexture(canvas);
    tex.colorSpace = THREE.SRGBColorSpace;
    return tex;
}
```

Apply to only the **top face** of a thin `BoxGeometry` using a multi-material array. BoxGeometry face order is: `+x, -x, +y, -y, +z, -z`.

```javascript
const noteTex = createNoteTexture('739');
const paperBaseMat = loadMat(TEX.paper);
const noteMat = new THREE.MeshStandardMaterial({ map: noteTex, roughness: 0.9 });

const paperMesh = new THREE.Mesh(
    new THREE.BoxGeometry(0.25, 0.01, 0.18),
    [paperBaseMat, paperBaseMat, noteMat, paperBaseMat, paperBaseMat, paperBaseMat]
);
```

**Pitfall:** If you apply the text texture to all faces of a thin box, the text will be stretched and visible on the edges. Always use a multi-material array so only the large face (index 2 for `+y`) shows the text.

### Batch Integrating Downloaded Sketchfab/GLTF Models
When a user drops multiple ZIPs of downloaded models (often from Sketchfab) into a project, they typically contain `scene.gltf` + `scene.bin` + `textures/`. These models often have inconsistent scales and some ZIPs are multi-model collections (one GLTF containing 20+ separate furniture meshes). A systematic workflow is needed to inspect, scale, and place them correctly.

#### Step 1: Inspect ZIPs before extracting
```bash
for f in *.zip; do echo "=== $f ==="; unzip -l "$f" 2>/dev/null | head -20; done
```
Look for `scene.gltf`, `scene.bin`, and a `textures/` folder.

#### Step 2: Parse GLTF structure and compute bounding boxes (Python)
Before writing placement code, determine the real-world scale of each model. Sketchfab exports often use meters, centimeters, or arbitrary units.

```python
import json, struct, os, numpy as np

def get_mesh_bboxes(gltf_path):
    with open(gltf_path, 'r') as f:
        data = json.load(f)
    accessors = data.get('accessors', [])
    meshes = data.get('meshes', [])
    buffer_views = data.get('bufferViews', [])
    buffers = data.get('buffers', [])
    base_dir = os.path.dirname(gltf_path)
    bin_path = os.path.join(base_dir, buffers[0]['uri'])
    with open(bin_path, 'rb') as bf:
        bin_data = bf.read()

    def read_accessor(acc_idx):
        acc = accessors[acc_idx]
        bv = buffer_views[acc['bufferView']]
        byte_offset = bv.get('byteOffset', 0) + acc.get('byteOffset', 0)
        count = acc['count']
        type_str = acc['type']
        component_type = acc['componentType']
        ctype = {5126: 'f', 5123: 'H', 5121: 'B'}.get(component_type)
        csize = {5126: 4, 5123: 2, 5121: 1}.get(component_type)
        if not ctype: return None
        num = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}.get(type_str, 1)
        stride = bv.get('byteStride', num * csize)
        arr = []
        for i in range(count):
            off = byte_offset + i * stride
            arr.append(struct.unpack_from('<' + ctype * num, bin_data, off))
        return np.array(arr)

    results = []
    for mi, mesh in enumerate(meshes):
        name = mesh.get('name', f'mesh_{mi}')
        verts = []
        for prim in mesh.get('primitives', []):
            pos_idx = prim.get('attributes', {}).get('POSITION')
            if pos_idx is None: continue
            acc = accessors[pos_idx]
            if 'min' in acc and 'max' in acc:
                verts.append(np.array(acc['min']))
                verts.append(np.array(acc['max']))
            else:
                v = read_accessor(pos_idx)
                if v is not None:
                    verts.append(v.min(axis=0))
                    verts.append(v.max(axis=0))
        if verts:
            verts = np.array(verts)
            size = verts.max(axis=0) - verts.min(axis=0)
            results.append((name, size))
    return results
```

Run this on every `scene.gltf` to discover which models need drastic scaling. Typical findings:
- **Bed model**: bounding box 20m wide → needs `scale = 2.2 / 20 = 0.11`
- **Book pile**: bounding box 1100 units wide → needs `scale = 0.25 / 1100 ≈ 0.0002`
- **Staircase**: bounding box 300+ units → needs `scale ≈ 0.01`
- **Multi-model collection** (e.g., `furniture_a`): 27 meshes, each 0.1–4m → usable as-is with minor scaling

#### Step 3: Choose scaling strategy
**Do NOT** use "fit in box" (`Math.min(x, y, z)`) for models that must preserve real-world proportions (beds, chairs, tables). It will flatten them.

Use **target-width uniform scaling** instead:
```javascript
const scale = targetWidth / size.x;  // e.g., targetWidth = 2.2 for a double bed
model.scale.setScalar(scale);
```

For multi-mesh collections where individual items have different natural sizes, set a per-item `targetScale` based on the mesh's bounding box:
```javascript
const maxDim = Math.max(size.x, size.y, size.z);
const scale = desiredRealWorldSize / maxDim;
```

#### Step 4: Handle multi-mesh collections
Some GLTFs contain an entire furniture kit in one file (e.g., chair + 3 tables + lamp in `classic_furniture`). If placed as one group, they stack at the origin.

**Strategy A — Place as a group** (acceptable for a pre-arranged set):
```javascript
loadAndPlace('models/classic_furniture/scene.gltf', 2.0, new THREE.Vector3(-3, 0, 0));
```

**Strategy B — Split meshes to different rooms** (necessary for asset packs):
Load once, traverse meshes, clone by name, and place independently. The original GLTF nodes usually have identity transforms, so mesh local coordinates ≈ world coordinates.

```javascript
gltfLoader.load('models/furniture_a/scene.gltf', (gltf) => {
    const root = gltf.scene;
    root.traverse(c => { if (c.isMesh) { c.castShadow = true; c.receiveShadow = true; } });

    const placements = [
        { match: 'storage_g',   pos: [13, 0, 1],   scale: 0.8 },
        { match: 'storage_c',   pos: [-3, 0, -3],  scale: 0.8 },
        { match: 'equipment_a', pos: [-3, 0.8, 9], scale: 0.4 },
    ];

    root.traverse((child) => {
        if (!child.isMesh) return;
        const name = child.name.toLowerCase();
        const cfg = placements.find(p => name.includes(p.match));
        if (cfg) {
            const clone = child.clone();
            clone.traverse(c => { if (c.isMesh) { c.castShadow = true; c.receiveShadow = true; } });

            const box = new THREE.Box3().setFromObject(child);
            const size = new THREE.Vector3(); box.getSize(size);
            const s = cfg.scale;
            clone.scale.set(s, s, s);
            clone.position.set(
                cfg.pos[0] - box.min.x * s,
                cfg.pos[1] - box.min.y * s,
                cfg.pos[2] - box.min.z * s
            );
            scene.add(clone);
            child.visible = false;  // hide original so it doesn't stack at root
        }
    });

    // Remaining unclaimed items go to a storage corner
    root.position.set(18, 0, 8);
    root.scale.setScalar(0.8);
    scene.add(root);
});
```

**Pitfall — clone does not deep-clone geometry/material references:**
`child.clone()` shares geometry and material with the original. This is usually fine for rendering, but if you later mutate the clone's material (e.g., change color), the original will also change. For static placement this is harmless.

**Pitfall — mesh nested inside Group nodes:**
If the GLTF has `Group → Group → Mesh` hierarchies, the Mesh's `.position` may be `(0,0,0)` relative to its parent Group, but the Group itself may have a transform. In Sketchfab exports, parent transforms are usually identity, but always verify with the Python inspector first. If parents have non-zero transforms, use `child.updateWorldMatrix(true, false)` and `child.getWorldPosition()` before detaching.

#### Step 5: Auto-grounding helper
All loaded models should sit on the floor, not float or sink. Compute the bounding box minimum Y and offset:

```javascript
function loadAndPlace(path, targetWidth, pos, rotY = 0) {
    gltfLoader.load(path, (gltf) => {
        const model = gltf.scene;
        model.traverse(c => { if (c.isMesh) { c.castShadow = true; c.receiveShadow = true; } });

        const box = new THREE.Box3().setFromObject(model);
        const size = new THREE.Vector3(); box.getSize(size);
        const scale = targetWidth / size.x;
        model.scale.setScalar(scale);

        const center = new THREE.Vector3(); box.getCenter(center);
        scene.add(model);
        model.position.set(
            pos.x - center.x * scale,
            pos.y - box.min.y * scale,  // critical: align bottom to floor
            pos.z - center.z * scale
        );
        model.rotation.y = rotY;
    });
}
```

### Placeholder-to-Model Swap Pattern
When prototyping, build collision proxies with `BoxGeometry` first, give them a name (e.g. `name = '_placeholder_sofa'`), then load the external model and hide the placeholder:

```javascript
const ph = scene.getObjectByName('_placeholder_sofa');
if (ph) ph.visible = false;
```

This keeps AABB colliders intact while showing the detailed model.

## 8a. Procedural Terrain Generation (When Downloads Fail)

When Sketchfab or other model sites block remote browsers with bot detection, or when you need infinite, customizable background terrain, generate it programmatically with **Perlin noise + Fractal Brownian Motion (FBM)**. This avoids external dependencies entirely.

### Perlin Noise Implementation
Use a compact 2D/3D Perlin implementation (no external libraries needed):

```javascript
class PerlinNoise {
    constructor() {
        this.p = new Uint8Array(512);
        const perm = [151,160,137,91,90,15,131,13,201,95,96,53,194,233,7,225,
            140,36,103,30,69,142,8,99,37,240,21,10,23,190,6,148,247,120,234,
            75,0,26,197,62,94,252,219,203,117,35,11,32,57,177,33,88,237,149,
            56,87,174,20,125,136,171,168,68,175,74,165,71,134,139,48,27,166,
            77,146,158,231,83,111,229,122,60,211,133,230,220,105,92,41,55,46,
            245,40,244,102,143,54,65,25,63,161,1,216,80,73,209,76,132,187,208,
            89,18,169,200,196,135,130,116,188,159,86,164,100,109,198,173,186,
            3,64,52,217,226,250,124,123,5,202,38,147,118,126,255,82,85,212,207,
            206,59,227,47,16,58,17,182,189,28,42,223,183,170,213,119,248,152,2,
            44,154,163,70,221,153,101,155,167,43,172,9,129,22,39,253,19,98,108,
            110,79,113,224,232,178,185,112,104,218,246,97,228,251,34,242,193,
            238,210,144,12,191,179,162,241,81,51,145,235,249,14,239,107,49,192,
            214,31,181,199,106,157,184,84,204,176,115,121,50,45,127,4,150,254,
            138,236,205,93,222,114,67,29,24,72,243,141,128,195,78,66,215,61,156,180];
        for (let i = 0; i < 256; i++) this.p[i] = this.p[i + 256] = perm[i];
    }
    fade(t) { return t * t * t * (t * (t * 6 - 15) + 10); }
    lerp(t, a, b) { return a + t * (b - a); }
    grad(hash, x, y, z) {
        const h = hash & 15;
        const u = h < 8 ? x : y;
        const v = h < 4 ? y : h === 12 || h === 14 ? x : z;
        return ((h & 1) === 0 ? u : -u) + ((h & 2) === 0 ? v : -v);
    }
    noise(x, y, z = 0) {
        const X = Math.floor(x) & 255, Y = Math.floor(y) & 255, Z = Math.floor(z) & 255;
        x -= Math.floor(x); y -= Math.floor(y); z -= Math.floor(z);
        const u = this.fade(x), v = this.fade(y), w = this.fade(z);
        const A = this.p[X] + Y, AA = this.p[A] + Z, AB = this.p[A + 1] + Z;
        const B = this.p[X + 1] + Y, BA = this.p[B] + Z, BB = this.p[B + 1] + Z;
        return this.lerp(w, this.lerp(v, this.lerp(u, this.grad(this.p[AA], x, y, z),
            this.grad(this.p[BA], x - 1, y, z)),
            this.lerp(u, this.grad(this.p[AB], x, y - 1, z),
            this.grad(this.p[BB], x - 1, y - 1, z))),
            this.lerp(v, this.lerp(u, this.grad(this.p[AA + 1], x, y, z - 1),
            this.grad(this.p[BA + 1], x - 1, y, z - 1)),
            this.lerp(u, this.grad(this.p[AB + 1], x, y - 1, z - 1),
            this.grad(this.p[BB + 1], x - 1, y - 1, z - 1))));
    }
}

function fbm(noise, x, y, octaves = 6, persistence = 0.5, lacunarity = 2.0) {
    let total = 0, frequency = 1, amplitude = 1, maxValue = 0;
    for (let i = 0; i < octaves; i++) {
        total += noise.noise(x * frequency, y * frequency, 0) * amplitude;
        maxValue += amplitude;
        amplitude *= persistence;
        frequency *= lacunarity;
    }
    return total / maxValue;
}
```

### Himalayan-Style Mountain Range
Create a large `PlaneGeometry`, displace vertices with FBM, sharpen peaks, and color by altitude:

```javascript
export function createHimalayaMountains(scene) {
    const noise = new PerlinNoise();
    const size = 500;
    const segments = 100;
    const geometry = new THREE.PlaneGeometry(size, size, segments, segments);
    geometry.rotateX(-Math.PI / 2);

    const pos = geometry.attributes.position;
    const colors = [];
    const cRock = new THREE.Color(0x5a5a5a);
    const cDirt = new THREE.Color(0x7a6a5a);
    const cSnow = new THREE.Color(0xffffff);
    const cIce = new THREE.Color(0xddeeff);

    for (let i = 0; i < pos.count; i++) {
        const x = pos.getX(i);
        const z = pos.getZ(i);
        const dist = Math.sqrt(x * x + z * z);
        const ridge = Math.max(0, (dist - 30) / 180); // center low, edges high

        let n = fbm(noise, x * 0.015 + 50, z * 0.015 + 50, 7, 0.48, 2.1);
        n = Math.pow(Math.abs(n), 0.65) * Math.sign(n); // sharpen peaks

        let y = (n * 80 + 5) * ridge;
        if (y < 0) y = 0;
        pos.setY(i, y);

        const t = Math.min(y / 55, 1);
        let c;
        if (t < 0.25) c = cRock.clone().lerp(cDirt, t / 0.25);
        else if (t < 0.6) c = cDirt.clone().lerp(cSnow, (t - 0.25) / 0.35);
        else c = cSnow.clone().lerp(cIce, (t - 0.6) / 0.4);
        colors.push(c.r, c.g, c.b);
    }

    geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
    geometry.computeVertexNormals();

    const material = new THREE.MeshStandardMaterial({
        vertexColors: true, roughness: 0.95, flatShading: true, side: THREE.DoubleSide
    });
    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.set(0, -3, 0);
    mesh.receiveShadow = true;
    scene.add(mesh);
}
```

**Key parameters:**
- `ridge` — distance mask so the house/garden area stays flat while mountains rise at the perimeter.
- `pow(abs(n), 0.65)` — compresses low values and exaggerates peaks, creating sharp Himalayan-style summits instead of rolling hills.
- `flatShading: true` — gives a stylized low-poly look without needing custom shaders.
- `vertexColors` — height-based coloring is computed once at generation time, zero runtime cost.

## 8b. Modular Refactoring for Legacy Single-File Projects

When `main.js` grows past 1500 lines, splitting it into ESM modules improves maintainability and reduces merge conflicts. However, a naive "extract everything into shared state" approach often breaks because variables (`scene`, `camera`, `renderer`, `audioCtx`) are referenced in dozens of places across closures.

### Safe Extraction Strategy
**Rule: extract fully independent subsystems first; keep tightly-coupled code in `main.js`.**

| Priority | Subsystem | Risk | Example |
|----------|-----------|------|---------|
| 1 | Pure data/config | None | Texture paths, constants |
| 2 | Self-contained utilities | Low | Audio loading, sound playback |
| 3 | Pure generators | Low | Terrain, sky, particle systems |
| 4 | Model loaders | Medium | `placeKenney`, `loadModels` (depends on `scene`, `colliders`) |
| 5 | Interaction logic | High | Raycaster, puzzle state machine (touches `gameState`, `controls`) |

### Example: Extracting Audio + Config + Terrain

`js/config.js` — pure data, zero side effects:
```javascript
export const TEX = {
    wood: { color: 'assets/textures/wood_color.jpg', roughness: 'assets/textures/wood_rough.jpg' },
    floor: { color: 'assets/textures/floor_color.jpg' }
};

const texLoader = new THREE.TextureLoader();
export function loadMat(paths, overrides = {}) {
    const mat = new THREE.MeshStandardMaterial({
        map: paths.color ? texLoader.load(paths.color) : null,
        ...overrides
    });
    if (mat.map) mat.map.colorSpace = THREE.SRGBColorSpace;
    return mat;
}
```

`js/audio.js` — self-contained, imports nothing from main:
```javascript
export const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
const sounds = {};

export async function loadSounds(files) { /* ... */ }
export function playSound(name, volume = 1.0) { /* ... */ }
export function startAmbient() { /* ... */ }
```

`js/terrain.js` — pure generator, takes `scene` as parameter:
```javascript
import { PerlinNoise, fbm } from './noise.js'; // or inline

export function createHimalayaMountains(scene) {
    // ... generate geometry, add to scene ...
}
```

`main.js` — top-level imports only:
```javascript
import { loadSounds, playSound, startAmbient, playFootstep, stopFootstep, audioCtx } from './js/audio.js';
import { TEX, loadMat } from './js/config.js';
import { createHimalayaMountains } from './js/terrain.js';
```

### Critical Pitfalls During Extraction

1. **Missing import of `audioCtx`** — If `main.js` previously referenced `audioCtx` as a top-level `const`, extracting it into `audio.js` without re-exporting it breaks `audioCtx.state` checks. Always re-export shared singletons.

2. **DOM queries inside modules** — If a module does `document.getElementById('blocker')` at the top level, it may run before the DOM is ready. Move DOM access into initialization functions or call them from `main.js` after `DOMContentLoaded`.

3. **Circular dependencies** — Do NOT let `audio.js` import from `main.js`. Pass callbacks or use events instead.

4. **Scope confusion with `scene`** — Terrain generators should accept `scene` as a parameter rather than importing it. This keeps them testable and avoids tight coupling.

### When NOT to extract
If a function references `gameState`, `controls`, `camera`, `renderer`, and `scene` all at once, keep it in `main.js` until you can refactor it to accept dependencies as parameters. Premature extraction of the animation loop or interaction handler creates spaghetti imports.

## 9. Performance Tips & Runtime Debugging

### System-First Diagnosis
Before blaming Three.js code, verify the machine isn't resource-starved:
```bash
top -l 1 | head -5
# Look for: Load Avg > 10, CPU idle < 20%, free memory < 500MB
```
If Xcode/build tools are running, the browser will stutter regardless of code quality. Pause heavy compiles first.

### Renderer Configuration (High Impact)
These three lines often determine whether a scene runs at 60fps or 15fps on integrated graphics:
```javascript
renderer = new THREE.WebGLRenderer({ antialias: false });  // antialias = 4x fill-rate
renderer.setPixelRatio(1);                                 // Retina 2x = 4x pixels
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFShadowMap;              // PCFSoft is 2x slower
```
- **Pixel ratio**: On a MacBook Retina screen, `devicePixelRatio = 2` means a 1920×1080 canvas renders at 3840×2160. Cap to `1` for prototypes, `1.5` for polish.
- **Shadow maps**: Each `castShadow = true` light re-renders the scene. With 4 rooms × 1 overhead SpotLight = 4 shadow passes per frame. Reduce to `512` or disable on all but the player's current room.
- **Model shadows**: Batch-disable `castShadow` on small decorative objects (books, plants, cups). Only large furniture and walls need to cast shadows.

```javascript
// Apply to ALL loaded GLTF models
model.traverse(c => {
    if (c.isMesh) {
        c.castShadow = false;      // small items don't need to cast
        c.receiveShadow = true;    // still receive room lighting
    }
});
```

### Asset Audit & Cleanup
A common cause of "opening the project feels laggy" is **asset bloat** — thousands of files in the project, most never loaded.

**Audit workflow:**
```bash
# Count total model files
find assets/models -type f | wc -l

# Count what the code actually references
grep -oE "['\"][^'\"]+\\.glb['\"]" main.js | sort | uniq | wc -l
```

If the ratio is extreme (e.g., 469 glb files, 78 referenced), purge the rest:
```bash
cd "assets/models/Models/GLTF format"
for f in *.glb; do
  if ! grep -q "$f" ../../../main.js; then
    rm "$f"
  fi
done
```

Also delete unused format backups (DAE/FBX/OBJ/STL) that ship with asset packs:
```bash
rm -rf models/"DAE format" models/"FBX format" models/"OBJ format" models/"STL format"
```

**Real-world impact:** A project with 2000+ files (Kenney assets + Sketchfab downloads + format backups) can drop to ~400 files after cleanup. This dramatically improves IDE indexing, git operations, and local server startup time.

**Automation tip:** The `grep -q "$f" main.js` approach is conservative but safe. If your project loads models dynamically (e.g., `const file = 'tree_' + variant + '.glb'`), construct a regex that covers all variants, or whitelist known prefixes before deleting.

### Loading Bottleneck
`init()` often fires **~100 concurrent resource loads** (sounds + GLTFs + textures). Browsers limit HTTP/1.1 concurrency to **6–8 requests per domain**. The rest queue, making the page feel frozen.

**Symptoms:** White screen for 10+ seconds, then everything pops in at once.

**Mitigations:**
1. **Loading screen** — Show a progress bar so users know the page isn't dead.
2. **Lazy loading** — Load only the player's starting room + shared assets. Defer other rooms until the player approaches a doorway.
3. **GLTF merging** — Use `gltf-transform` to merge dozens of small `.glb` files into one atlas per room (reduces requests from 80 → 3).

### Fog & Background for Daytime Scenes
For outdoor visibility, set fog color to match the sky instead of using dark night fog:
```javascript
scene.background = new THREE.Color(0x87CEEB);          // sky blue
scene.fog = new THREE.Fog(0xB0DFFF, 20, 80);          // light blue, far range
// near=20 means indoor spaces (<15m) are unaffected by fog
```

Sky sphere with clouds:
```javascript
const skyGeo = new THREE.SphereGeometry(80, 32, 32);
const skyMat = new THREE.MeshBasicMaterial({ color: 0x87CEEB, side: THREE.BackSide });
scene.add(new THREE.Mesh(skyGeo, skyMat));

// Clouds — white, semi-transparent spheres grouped
function createCloud(x, y, z, scale = 1) {
    const cloud = new THREE.Group();
    const mat = new THREE.MeshStandardMaterial({
        color: 0xffffff, transparent: true, opacity: 0.95, flatShading: true
    });
    for (let i = 0; i < 5; i++) {
        const r = (Math.random() * 1.5 + 0.8) * scale;
        const sphere = new THREE.Mesh(new THREE.SphereGeometry(r, 8, 8), mat);
        sphere.position.set(
            (Math.random() - 0.5) * 3 * scale,
            (Math.random() - 0.5) * 0.5 * scale,
            (Math.random() - 0.5) * 1.5 * scale
        );
        cloud.add(sphere);
    }
    cloud.position.set(x, y, z);
    scene.add(cloud);
}
for (let i = 0; i < 25; i++) {
    createCloud(
        (Math.random() - 0.5) * 120,
        Math.random() * 20 + 25,
        (Math.random() - 0.5) * 120,
        Math.random() * 1.2 + 0.8
    );
}
```

Daytime lighting stack:
```javascript
const ambient = new THREE.AmbientLight(0xffffff, 0.9);
scene.add(ambient);

const sunLight = new THREE.DirectionalLight(0xffffee, 1.5);
sunLight.position.set(10, 20, 10);
scene.add(sunLight);

const hemiLight = new THREE.HemisphereLight(0x87CEEB, 0x362d1d, 0.8);
scene.add(hemiLight);
```

## 10. Multi-Room Level Architecture

### Indoor Lighting Setup
A single overhead SpotLight is never enough for realistic room illumination. For a 10×10 room with 4m ceilings, a single 60° SpotLight from the center only illuminates a ~4.5m diameter circle on the floor, leaving walls and corners in darkness.

**Proven per-room lighting stack (3 lights + hemisphere):**

```javascript
function makeRoomLight(x, z) {
    // 1. Main overhead light — wide angle, high intensity
    const main = new THREE.SpotLight(0xffddaa, 3.0);
    main.position.set(x, 3.9, z);
    main.target.position.set(x, 0, z);
    main.angle = Math.PI / 2;           // 90° covers entire floor
    main.penumbra = 0.8;                // very soft falloff
    main.distance = 20;
    main.castShadow = true;
    main.shadow.mapSize.set(1024, 1024);
    main.shadow.bias = -0.0005;
    main.shadow.camera.near = 0.1;
    main.shadow.camera.far = 8;
    scene.add(main);
    scene.add(main.target);

    // 2. Wall-wash light 1 — diagonal, creates side shadows on walls
    const w1 = new THREE.SpotLight(0xffeedd, 1.2);
    w1.position.set(x - 3, 3.6, z - 3);
    w1.target.position.set(x + 4, 0, z + 4);
    w1.angle = Math.PI / 3;
    w1.penumbra = 0.6;
    w1.distance = 18;
    w1.castShadow = true;
    w1.shadow.mapSize.set(512, 512);
    w1.shadow.bias = -0.001;
    scene.add(w1);
    scene.add(w1.target);

    // 3. Wall-wash light 2 — opposite diagonal
    const w2 = new THREE.SpotLight(0xffeedd, 1.2);
    w2.position.set(x + 3, 3.6, z + 3);
    w2.target.position.set(x - 4, 0, z - 4);
    w2.angle = Math.PI / 3;
    w2.penumbra = 0.6;
    w2.distance = 18;
    w2.castShadow = true;
    w2.shadow.mapSize.set(512, 512);
    w2.shadow.bias = -0.001;
    scene.add(w2);
    scene.add(w2.target);

    return main;
}

// 4. Global hemisphere fill — prevents corners from going pure black
const hemiLight = new THREE.HemisphereLight(0xffffff, 0x444444, 0.5);
scene.add(hemiLight);
```

Always add `renderer.shadowMap.type = THREE.PCFSoftShadowMap;` after `renderer.shadowMap.enabled = true;` for interior scenes.

**Why this works:**
- The 90° main light reaches every wall, unlike a 60° cone that dies before the edges.
- The two diagonal wall-wash lights strike furniture at an angle, casting visible side shadows onto walls (overhead-only lighting cannot create wall shadows because light is parallel to the wall surface).
- HemisphereLight provides sky/ground bounce so even unlit crevices have readable detail.

### Indoor Lighting Debugging
When rooms still look wrong after applying the stack above, check these causes:

1. **External DirectionalLight (sun) leaking** — A sun at `(20, 30, -10)` can shine over the top of front walls (height ~4m) and contaminate front-facing rooms while back rooms are shielded. Lower sun intensity or verify with a reverse ray trace from room center to sun.
2. **Decorative object glare** — A chandelier or glass bowl placed directly under a SpotLight creates intense specular highlights with metalness > 0.5. Lower the decor's metalness/roughness or move the light slightly off-center.
3. **Furniture density × low-res shadows** — Dense furniture with 512×512 shadow maps produces overlapping coarse shadows. Raise shadow maps to 1024×1024.
4. **Shadow acne on walls** — SpotLight grazing walls at shallow angles produces stripe artifacts. Raise bias to `-0.0005` or switch to `PCFSoftShadowMap`.
5. **SpotLight spilling into adjacent rooms** — If the main 90° light bleeds through doorways, verify doorways have lintels and that interior walls extend to the ceiling plane. If spill is still visible, lower `penumbra` slightly or add thin blocker planes above door headers.

## 10. Multi-Room Level Architecture

For connected rooms (e.g., a house), build a single large floor/ceiling and use interior walls as dividers. Do not create separate scenes.

### Layout Example (4 rooms, 20x20)
Rooms arranged in a grid, sharing wall boundaries:
```
+--------+--------+
| Study  | Bedroom|
+--------+--------+
|Living  | Kitchen|
+--------+--------+
```

Build outer walls at the perimeter, then add interior walls with doorways:

```javascript
const W = 20, D = 20, H = 4, T = 0.2;
const doorW = 1.4, doorH = 2.2, innerDoorW = 2.0;

// Interior vertical wall at x=5, with doorways at z=0 and z=10
// Lower segment z:[-5,-1]
addBoxCollider(5, H/2, -3, T, H, 4);
// Lintel above doorway z:[-1,1]  — NO collider here (players walk through)
// Middle segment z:[1,9]
addBoxCollider(5, H/2, 5, T, H, 8);
// Lintel above doorway z:[9,11]  — NO collider
// Upper segment z:[11,15]
addBoxCollider(5, H/2, 13, T, H, 4);
```

### Critical: Do NOT Collide with Lintels
AABB colliders in this guide are 2D (x/z only). If you add a collider for a door header (the wall segment above the door), it will block the doorway at ground level because y-axis is ignored.

```javascript
// WRONG — blocks the doorway
addBoxCollider(5, 3.1, 0, T, H - doorH, innerDoorW);

// CORRECT — visual only, no collider
const lintel = new THREE.Mesh(new THREE.BoxGeometry(T, H - doorH, innerDoorW), wallMat);
lintel.position.set(5, 3.1, 0);
scene.add(lintel);
// No addBoxCollider() call!
```

### Furniture per Room
Place furniture relative to each room's zone. Keep placeholder boxes for collision, then load external models on top and hide the boxes (see Placeholder-to-Model Swap Pattern).

### Per-Room Ceiling & Floor
Do not use one giant `BoxGeometry(20, 0.1, 20)` for the entire house floor or ceiling. It stretches textures and looks artificial. Instead, create one geometry per room with appropriate materials:

```javascript
// Different materials per room
const floorMatWood = loadMat(TEX.floor);
setRepeat(floorMatWood, 2, 2);
const floorMatTile = loadMat(TEX.floor_tile);
setRepeat(floorMatTile, 3, 3);

function setRepeat(mat, u, v) {
    if (mat.map) mat.map.repeat.set(u, v);
    if (mat.roughnessMap) mat.roughnessMap.repeat.set(u, v);
    if (mat.normalMap) mat.normalMap.repeat.set(u, v);
}

// 4 rooms, each 10x10
makeFloor(0, 0, floorMatWood);   // Living room
makeFloor(0, 10, floorMatWood);  // Study
makeFloor(10, 10, floorMatWood); // Bedroom
makeFloor(10, 0, floorMatTile);  // Kitchen

function makeFloor(x, z, mat) {
    const floor = new THREE.Mesh(new THREE.BoxGeometry(10, 0.05, 10), mat);
    floor.position.set(x, -0.025, z);
    floor.receiveShadow = true;
    scene.add(floor);
}

// Ceilings: thin PlaneGeometry per room, facing down
const ceilMat = new THREE.MeshStandardMaterial({ color: 0xf0f0f0, roughness: 0.9 });
function makeCeiling(x, z) {
    const ceil = new THREE.Mesh(new THREE.PlaneGeometry(10, 10), ceilMat);
    ceil.rotation.x = Math.PI / 2;
    ceil.position.set(x, 4, z);
    ceil.receiveShadow = true;
    scene.add(ceil);
}
makeCeiling(0, 0);
makeCeiling(0, 10);
makeCeiling(10, 10);
makeCeiling(10, 0);
```

### Creating Windows in Exterior Walls

For floor-to-ceiling windows, split exterior walls into segments and fill openings with transparent glass planes. Do **not** add colliders in the window gap or players will see an invisible wall.

**Glass material (reusable):**
```javascript
const glassMat = new THREE.MeshStandardMaterial({
    color: 0xffffff,
    metalness: 0.1,
    roughness: 0.0,
    transparent: true,
    opacity: 0.3,
    side: THREE.DoubleSide
});
```

**Wall segmentation example (north wall with two 4m-wide windows):**
The wall spans x∈[-5,15] at z=-5. Place windows at x∈[-3,1] (living room) and x∈[9,13] (kitchen), leaving solid segments on the edges and between windows.

```javascript
function makeWindow(x, z, width, height, rotY = 0) {
    const glass = new THREE.Mesh(new THREE.PlaneGeometry(width, height), glassMat);
    glass.position.set(x, height / 2, z);
    glass.rotation.y = rotY;
    scene.add(glass);
}

// North wall (z = -5), total width 20m, height 4m
// Left solid segment: x=[-5,-3], width 2m
addBoxCollider(-4, 2, -5, 2, 4, 0.2);
const wallLeft = new THREE.Mesh(new THREE.BoxGeometry(2, 4, 0.2), wallMat);
wallLeft.position.set(-4, 2, -5); scene.add(wallLeft);

// Window 1 at x=[-3,1], width 4m — NO collider, just glass
makeWindow(-1, -5, 4, 3.5, 0);

// Middle solid segment: x=[1,9], width 8m
addBoxCollider(5, 2, -5, 8, 4, 0.2);
const wallMid = new THREE.Mesh(new THREE.BoxGeometry(8, 4, 0.2), wallMat);
wallMid.position.set(5, 2, -5); scene.add(wallMid);

// Window 2 at x=[9,13], width 4m — NO collider
makeWindow(11, -5, 4, 3.5, 0);

// Right solid segment: x=[13,15], width 2m
addBoxCollider(14, 2, -5, 2, 4, 0.2);
const wallRight = new THREE.Mesh(new THREE.BoxGeometry(2, 4, 0.2), wallMat);
wallRight.position.set(14, 2, -5); scene.add(wallRight);
```

**Pitfall — forgetting the window gap collider:** If you accidentally call `addBoxCollider` for the space where the glass plane sits, the player will hit an invisible barrier when looking "out" the window. Only collider the solid wall segments.

**Pitfall — glass only visible from one side:** Without `side: THREE.DoubleSide`, the glass plane disappears when viewed from outside the house. Always use `DoubleSide` for window glass.

### Toggle Door Colliders
Doors must block movement when closed and allow passage when open. Store a `colliderIndex` on the door's `userData` and toggle `colliders[index].disabled` after the open/close animation finishes. See the Door Group Rotation Pattern above for the implementation.

### Drawer Interaction
A reusable "slide open/close" mechanic for cabinets and nightstands. Animate position along a local axis (usually Z) instead of rotating:

```javascript
if (type === 'drawer') {
    const data = obj.userData;
    const isOpen = data.isOpen;
    data.isOpen = !isOpen;
    const startZ = obj.position.z;
    const endZ = isOpen ? startZ - 0.3 : startZ + 0.3;
    let t = 0;
    function step() {
        t += 0.06;
        if (t > 1) t = 1;
        const ease = 1 - Math.pow(1 - t, 3);
        obj.position.z = startZ + (endZ - startZ) * ease;
        if (t < 1) requestAnimationFrame(step);
    }
    step();
    playSound('button', 0.4);
}
```

### Outdoor Extension (Garden)
Add an exterior around the house bounds so players see something when looking out windows or escaping:

```javascript
function buildGarden() {
    // Grass plane
    const grassMat = new THREE.MeshStandardMaterial({ color: 0x2d5a27, roughness: 0.95 });
    const grass = new THREE.Mesh(new THREE.PlaneGeometry(50, 50), grassMat);
    grass.rotation.x = -Math.PI / 2;
    grass.position.set(5, -0.06, 5);
    grass.receiveShadow = true;
    scene.add(grass);

    // Simple fence posts
    const fenceMat = loadMat(TEX.wood);
    const posts = [[-5, -5], [15, -5], [-5, 15], [15, 15]]; // corners
    posts.forEach(([px, pz]) => {
        const post = new THREE.Mesh(new THREE.BoxGeometry(0.1, 1.2, 0.1), fenceMat);
        post.position.set(px, 0.6, pz);
        scene.add(post);
    });

    // Simple trees (cylinder + sphere)
    const treePositions = [[-8, -8], [18, -8], [-8, 18], [18, 18]];
    treePositions.forEach(([tx, tz]) => {
        const trunk = new THREE.Mesh(
            new THREE.CylinderGeometry(0.15, 0.2, 1.5, 8),
            new THREE.MeshStandardMaterial({ color: 0x5c4033 })
        );
        trunk.position.set(tx, 0.75, tz);
        scene.add(trunk);
        const leaves = new THREE.Mesh(
            new THREE.SphereGeometry(0.8, 8, 8),
            new THREE.MeshStandardMaterial({ color: 0x228b22 })
        );
        leaves.position.set(tx, 1.8, tz);
        scene.add(leaves);
    });
}
```

## 11. Black Screen Debugging Checklist

If the page loads but the 3D view is completely black/empty after clicking start:

1. **Check if `<canvas>` exists:**
   ```javascript
   document.querySelectorAll('canvas').length  // should be > 0
   ```
   If 0, `init()` never ran. Verify `init();` and `animate();` calls are still present at the **bottom** of `main.js`. These are easily deleted accidentally during large patches.

2. **Check browser console for errors:**
   - `Cannot access 'X' before initialization` → TDZ. See `js-tdz-init-order` skill.
   - `SyntaxError` → check for broken imports or trailing commas after patching.
   - Silent failure → verify `importmap` CDN URLs are reachable.

3. **Verify module is loading:**
   - Check Network tab for `main.js` 404s.
   - If caching is suspected, force-refresh with `?nocache=1`.

4. **Check for `requestPointerLock` failure:**
   In headless/automation browsers, `PointerLockControls.lock()` may fail silently. The blocker overlay disappears but the game never starts. Add a fallback or test in a real browser.

5. **Fog + Background color collision:**
   If `scene.background` and `scene.fog.color` are both very dark (e.g., `0x111111`), and objects are unlit/black, the entire frame can look empty. Temporarily disable fog or brighten the background to confirm geometry exists.

## 13. Real-Time Collision Debugging

When a player gets stuck near a doorway or claims "something is blocking me but I can't see what," add a live debugger that prints the blocking collider's name directly into the game's UI hint/crosshair overlay.

### Steps

1. **Name your colliders:**
   ```javascript
   function addBoxCollider(x, y, z, sx, sy, sz, name = null) {
       colliders.push({ minX: x - sx/2, maxX: x + sx/2, minZ: z - sz/2, maxZ: z + sz/2, disabled: false, name });
   }
   // doors
   colliders.push({ ..., name: 'door_living_kitchen' });
   ```

2. **Make `checkCollision` return the blocker instead of `true`:**
   ```javascript
   function checkCollision(x, y, z) {
       const r = PLAYER_RADIUS;
       for (const c of colliders) {
           if (c.disabled) continue;
           if (x + r > c.minX && x - r < c.maxX &&
               y > c.minY && y < c.maxY &&
               z + r > c.minZ && z - r < c.maxZ) {
               return c; // return the collider object
           }
       }
       return null;
   }
   ```

3. **Display blocker info in the animation loop:**
   ```javascript
   const cx = checkCollision(px + mx, py, pz);
   const cz = checkCollision(px, py, pz + mz);
   if (!cx) camera.position.x += mx;
   if (!cz) camera.position.z += mz;

   let blockInfo = '';
   if ((cx || cz) && px > 4 && px < 6 && pz > -2 && pz < 2) {
       const b = cx || cz;
       blockInfo = '被 ' + (b.name || ('墙(' + b.minX.toFixed(1) + ',' + b.minZ.toFixed(1) + ')')) + ' 挡住';
   }
   window._lastBlockInfo = blockInfo;
   ```

4. **Show it when raycaster finds nothing:**
   ```javascript
   if (hits.length > 0 && hits[0].distance < 2.5) {
       hintEl.textContent = hits[0].object.userData.label || '';
       hintEl.classList.add('show');
   } else if (window._lastBlockInfo) {
       hintEl.textContent = window._lastBlockInfo;
       hintEl.classList.add('show');
   } else {
       hintEl.classList.remove('show');
   }
   ```

This instantly reveals whether the player is hitting a wall segment, a door collider that failed to disable, or a piece of furniture placed too close to the doorway.

## 12. In-Browser Scene Editor (TransformControls)

When a scene has many placed models and the user wants to rearrange them without editing code, add an interactive drag/rotate editor using `TransformControls` alongside `PointerLockControls`.

### Setup
```js
import { TransformControls } from 'three/addons/controls/TransformControls.js';
let transformControl;
let isEditMode = false;

transformControl = new TransformControls(camera, renderer.domElement);
transformControl.addEventListener('dragging-changed', function (event) {
    controls.enabled = !event.value;
});
scene.add(transformControl);
transformControl.visible = false;
```

### KeyE Toggle Edit Mode
```js
const originalLock = controls.lock.bind(controls);
controls.lock = function() { if (isEditMode) return; originalLock(); };

case 'KeyE':
    isEditMode = !isEditMode;
    if (isEditMode) {
        controls.unlock();
        transformControl.visible = true;
    } else {
        transformControl.detach();
        transformControl.visible = false;
        controls.lock();
    }
    break;
```

### KeyT Toggle Translate/Rotate
```js
case 'KeyT':
    if (isEditMode) {
        transformControl.setMode(transformControl.mode === 'translate' ? 'rotate' : 'translate');
    }
    break;
```

### Model Selection via Raycaster
```js
if (isEditMode) {
    raycaster.setFromCamera(new THREE.Vector2(0, 0), camera);
    const hits = raycaster.intersectObjects(scene.children, true);
    const validHits = hits.filter(h => {
        let p = h.object;
        while (p) { if (p === transformControl) return false; p = p.parent; }
        return true;
    });
    if (validHits.length > 0) {
        let obj = validHits[0].object;
        while (obj.parent && obj.parent !== scene && !obj.userData.isFurniture) obj = obj.parent;
        if (obj.userData.isFurniture) {
            transformControl.detach();
            transformControl.attach(obj);
        }
    }
    return;
}
```

### Export Positions
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

**Pitfalls:**
- PointerLockControls re-locks on every click while unlocked — override `controls.lock()` to no-op during edit mode
- Raycaster hits the TransformControls gizmo itself — filter out hits whose parent chain includes `transformControl`
- Blocker overlay blocks clicks after unlock — hide the blocker when entering edit mode
- Re-attaching the same object causes flicker — guard with `if (transformControl.object === obj) return;`

## 12. Common Pitfalls

- **TDZ and block-scoped variables in movement code**: When refactoring the animation loop (e.g., adding `if (py > 4.0)` branches around collision checks), never move `const cx`/`const cz` into an `else` sub-block if downstream code (debug HUD, footstep logic, etc.) references them. JavaScript block scope means those bindings disappear after the `else` ends, causing a `ReferenceError` that silently kills the `requestAnimationFrame` loop and "freezes" the player. Declare shared temporaries with `let` before the branch:
  ```javascript
  let cx = null, cz = null;
  if (py > 4.0) {
      // roof movement without collision
  } else {
      cx = checkCollision(...);
      cz = checkCollision(...);
  }
  // downstream code can safely read cx/cz
  ```
  Also avoid using `const` variables before their declaration in the same block. If you need `px`/`pz` for vertical collision, declare them at the top of the `if (controls.isLocked)` block, not 20 lines below.
- **Duplicate variable declarations when adding lights**: When inserting HemisphereLight or other globals into a large file, use search (`grep -n 'const hemiLight'`) to verify the identifier doesn't already exist elsewhere. A second `const hemiLight = ...` 200 lines below the first causes an immediate `SyntaxError` that breaks the entire module, even if the file otherwise runs fine in browser ESM.
- **Door/Window Gaps**: When cutting holes in walls, calculate wall segment lengths precisely. If the room is 10m wide with a 1.4m door centered, each side wall is `(10 - 1.4) / 2 = 4.3m`. Center positions: left at `-5 + 4.3/2 = -2.85`, right at `5 - 4.3/2 = 2.85`. An incorrect width (e.g., 4.6) leaves visible gaps beside the door.
- **Missing Lintel**: Always add a beam above door holes (`height = wallHeight - doorHeight`, positioned at `doorTop + beamHeight/2`), or players will see empty space and potential light leaks.
- **Door Rotation Pivot**: Use `geometry.translate()` to shift the geometry origin to the hinge edge, then rotate the mesh. For a 1.4m wide door: `geometry.translate(0.7, 0, 0)` so the left edge becomes the pivot.
- **Audio Autoplay**: Browsers block AudioContext until user gesture. Always resume inside a click handler.
- **8K Texture Lag**: Downloaded PBR textures are often 8K. Batch-resize to 1K/2K immediately before use, or the browser will stutter on load. Use `sips -Z 1024` on macOS.
- **Retina Overdraw**: `window.devicePixelRatio` can be 2 or 3 on Macs. Cap it: `renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))`.
- **Segmented Wall UVs**: If you split a wall into multiple BoxGeometries for door cutouts, each segment resets UVs to 0-1, breaking texture continuity. Use world-space UV projection (see UV Alignment section).
- **Lintel Colliders in Multi-Room**: In a 2D AABB system (no y-axis), never add colliders for door headers/lintels — they will block the doorway at ground level. Only collider the lower wall segments. If you upgrade to 3D collision (with minY/maxY), headers naturally won't block because they sit above player height, but keep the habit of only colliding walkable surfaces.
- **2D collision breaks with roofs and stairs**: A common failure mode when extending a flat AABB system to multi-level structures (e.g., adding a roof, external stairs, or a second floor). If `checkCollision` only tests x and z, a roof collider at y=4.2 will trap the player at spawn because the player's x/z falls inside the roof's footprint. Always store `minY`/`maxY` in colliders and pass the player's current `y` to `checkCollision`.

### Vertical Collision for Roofs & Platforms
When a player jumps onto a roof or walks up stairs to a higher level, gravity will pull them through the surface unless you add vertical landing detection.

**Implementation:**
```javascript
// In the animation loop, BEFORE horizontal movement:
velocity.y -= 9.8 * delta;
const newY = camera.position.y + velocity.y * delta;

if (velocity.y < 0 && newY > groundHeight) {
    const groundCol = checkCollision(px, newY, pz);
    // Only land if we were already above this collider (prevents ceiling snagging)
    if (groundCol && camera.position.y >= groundCol.maxY - 0.05) {
        camera.position.y = groundCol.maxY + 0.01; // +epsilon is critical!
        velocity.y = 0;
        jumpCount = 0;
    } else {
        camera.position.y = newY;
    }
} else {
    camera.position.y = newY;
}
```

**Why `+ 0.01` matters:** If you set `camera.position.y = groundCol.maxY` exactly, floating point noise can make it `4.29999999` on the next frame. Since `checkCollision` uses `y < maxY`, the player will now register as "inside" the collider and horizontal movement gets blocked. Always land slightly above (`maxY + 0.01`) so the player sits cleanly on top.

**Preventing tunneling through thin colliders:**
A single-point `checkCollision(px, newY, pz)` fails when the player falls fast enough to skip over a thin surface in one frame. If the collider is only 0.2 units thick and gravity produces a frame delta of `-0.3`, the player jumps from `y = 4.5` to `y = 4.2` without ever sampling the range `4.3–4.1` where the collider lives.

Fix by sweeping downward from the previous frame's Y to `newY` when the single-point test misses:

```javascript
if (velocity.y < 0 && newY > groundHeight) {
    let groundCol = checkCollision(px, newY, pz);
    // Sweep test: falling fast can tunnel through thin colliders
    if (!groundCol && camera.position.y > newY) {
        for (let testY = camera.position.y; testY >= newY; testY -= 0.05) {
            const col = checkCollision(px, testY, pz);
            if (col) { groundCol = col; break; }
        }
    }
    if (groundCol && camera.position.y >= groundCol.maxY - 0.2) {
        camera.position.y = groundCol.maxY + 0.05;
        velocity.y = 0;
        jumpCount = 0;
    } else {
        camera.position.y = newY;
    }
}
```

Key adjustments:
- **Step size (`0.05`)**: Smaller than the thinnest collider you expect (roof at 0.2). For even faster falls, decrease to `0.02`.
- **Tolerance (`-0.2`)**: Must be larger than the sweep step plus the collider thickness, otherwise the player is rejected as "not above" the surface even though the sweep found it. Do not keep the tight `-0.05` tolerance when using this fix.
- **Only run when `camera.position.y > newY`**: The sweep is only needed on descent. Skip it when ascending or on flat ground to save CPU.

**Roof hard-height landing:** If a roof's surface is thin (e.g., `BoxGeometry(20, 0.2, 20)` centered at y=4.2, surface at y=4.3), floating-point noise can still place the player slightly inside the mesh even with `+0.01`. Give the roof collider a `name` (e.g., `'roof'`) and special-case it in vertical landing:
```javascript
if (groundCol && camera.position.y >= groundCol.maxY - 0.05) {
    if (groundCol.name === 'roof') {
        camera.position.y = 4.35; // hard height well above roof surface
    } else {
        camera.position.y = groundCol.maxY + 0.05;
    }
    velocity.y = 0;
    jumpCount = 0;
}
```
Then in horizontal movement, skip collision checks when `py > 4.0` so the player can walk freely on the roof without the roof AABB blocking movement.

**Stair platform pitfall:** If stairs end at a small "landing platform" that overlaps a larger roof collider, remove the platform's collider entirely and let the roof collider handle landing. A platform collider with its own AABB will trap the player when its y-range (`[4.2, 4.4]`) encompasses the player's landing height.

**Stair step colliders with y-axis detection:** When upgrading a flat (x/z-only) AABB system to 3D (with y-axis), stair step colliders that are shorter than player height (e.g., `sy = 0.35`) will no longer block the player because the player's y (e.g., 1.6) falls outside the step's y-range. Fix: remove all per-step colliders entirely and rely on jumping, or replace stairs with a ramp/slope collision.

**Indoor ceiling guard:** Use a height-gated check so players already on the roof (`y >= 4.0`) aren't forced back down by interior ceiling logic:
```javascript
const isIndoor = px > -5 && px < 15 && pz > -5 && pz < 15 && camera.position.y < 4.0;
if (isIndoor && camera.position.y > 3.8) {
    camera.position.y = 3.8; // Only traps low-flying indoor jumps
}
```
- **Doorway Width Must Match Door Width**: If a doorway is wider than the door (e.g., 2.0m doorway with a 1.4m door), the door will float in the opening with visible gaps on both sides and the collision box will not align with the door edges. Resize the doorway (wall segments and lintel) to exactly match the door width.
- **Full-file rewrite for large refactors**: When a JS file exceeds 1000 lines and requires 5+ interdependent changes (e.g., restructuring rooms, doors, and interactions simultaneously), incremental `patch` operations become fragile and often mismatch. Instead, read the file, plan the new structure, and rewrite it in sequential append passes using `execute_code` with Python. This avoids the "patch mismatch death spiral" and keeps the file syntactically valid throughout.
- **Door rotation direction (sign of rotY)**: When a door geometry is translated so the hinge is at the local origin (`geo.translate(width/2, height/2, 0)`), the door extends along local **+x**. Rotating the group by `Math.PI/2` maps local +x to world **-z**, while `-Math.PI/2` maps it to world **+z**. If the hinge is on the south side of a doorway (e.g., z=-0.7) and the doorway extends north to z=0.7, you **must** use `-Math.PI/2` so the door fills the doorway. Using `Math.PI/2` will make the door extend backwards into the room behind the hinge, leaving the doorway visually empty but with a collider that may still block passage depending on implementation.
- **Doorway clearance vs. player radius**: A 1.4m wide doorway is not fully usable. If the player has a collision radius of 0.4m, the usable passage width is only `1.4 - (0.4 * 2) = 0.6m`. With radius 0.3m it becomes 0.8m. This is because the player's collision circle extends 0.4m on both sides of their center point. If adjacent wall colliders end exactly at the doorway edges (e.g., wall at z=-0.7 and wall at z=0.7), the player must thread the needle through a 0.6m gap. Keep furniture at least 1.0m away from doorway centers to avoid accidentally narrowing this further.
- **Furniture blocking doorways**: A chair placed at (6, -0.2) near a doorway at x=5, z∈[-0.7,0.7] can completely block exit even though it's technically "in the room" rather than "in the doorway." The player's collision circle (radius 0.3-0.4) plus the chair's collider can overlap with the doorway exit path. After placing furniture, always test walking through every doorway from both directions. If players get stuck, use the Real-Time Collision Debugging technique above to identify the exact blocker.
- **Door collider disabled timing**: In `toggleDoor()`, disable the door's collider **immediately** when opening, not after the animation finishes. If you wait for the animation to complete, the player cannot walk through the doorway until the door fully swings open, creating the perception that the door "didn't open." Conversely, when closing, re-enable the collider only after the animation finishes so the door doesn't clip the player during its sweep.

## 14. Interior Layout & Procedural Furniture

When a scene feels empty or the furniture placement looks chaotic, apply realistic home-layout rules and fill gaps with procedural furniture built from Three.js primitives. This avoids waiting for external model downloads.

### Spatial Reasoning for Room Layouts

For a multi-room house, sketch the grid first. A 20×20 house split into four 10×10 rooms:

```
+--------+--------+
| Study  | Bedroom|  z: 5 ~ 15
+--------+--------+
|Living  | Kitchen|  z: -5 ~ 5
+--------+--------+
 x: -5~5   x: 5~15
```

**Rules for realistic placement:**
- **Sofas** — back against a wall, facing the room's focal point (TV, fireplace, coffee table). Avoid placing directly in front of doorways.
- **Beds** — headboard against the longest solid wall (usually the north/back wall), centered or with equal clearance on both sides. Leave ~0.5m between bed sides and nightstands.
- **Desks** — against a wall with the chair in front of it, not blocking the door path. Depth along the wall (x-axis) is usually better than sticking out into the room.
- **Dining sets** — table in the middle or near a wall, chairs pulled out evenly. Keep at least 1.0m clearance from doorways so the player can walk through.
- **Cabinets/wardrobes** — back flush against the wall. Use `z = wallZ + depth/2` for south-facing walls, or `z = wallZ - depth/2` for north-facing walls.
- **Plants/vases** — corners or beside large furniture, not in walkways.

**Pitfall — Doorway clearance:** A 1.4m doorway minus player radius (0.4m each side) leaves only ~0.6m of usable width. A chair at (6, -0.2) near a doorway at x=5 can completely seal the exit because the chair collider + player collider overlap the doorway path. After placing furniture, test every doorway from both directions.

### Adding Rotation Support to Model Loaders

Kenney GLB models often load aligned to local +x. To make a sofa face north-south along a wall, the loader must support `rotationY`.

```javascript
function placeKenney(file, targetSize, worldPos, placeholderName, rotationY = 0) {
    gltfLoader.load(basePath + file, (gltf) => {
        const model = gltf.scene;
        model.traverse(c => { if (c.isMesh) { c.castShadow = true; c.receiveShadow = true; } });
        if (rotationY) model.rotation.y = rotationY;

        const box = new THREE.Box3().setFromObject(model);
        const size = new THREE.Vector3(); box.getSize(size);
        const scale = Math.min(targetSize.x / size.x, targetSize.y / size.y, targetSize.z / size.z);
        model.scale.setScalar(scale);

        const center = new THREE.Vector3(); box.getCenter(center);
        scene.add(model);
        model.position.set(
            worldPos.x - center.x * scale,
            worldPos.y - box.min.y * scale,
            worldPos.z - center.z * scale
        );

        if (placeholderName) {
            const ph = scene.getObjectByName(placeholderName);
            if (ph) ph.visible = false;
        }
    });
}
```

Usage: `placeKenney('loungeSofa.glb', size, pos, '_placeholder_sofa', Math.PI / 2);`

**Important:** Apply rotation **before** computing the bounding box so the position correction accounts for the rotated extents.

### Procedural European Furniture from Primitives

When external models are unavailable or the wrong style, generate ornate furniture directly using `BoxGeometry`, `CylinderGeometry`, `SphereGeometry`, and `TorusGeometry` with a curated material palette.

**European palette:**
```javascript
const euroWood = new THREE.MeshStandardMaterial({ color: 0x5c2a2a, roughness: 0.4 });
const darkWood = new THREE.MeshStandardMaterial({ color: 0x3e1e1e, roughness: 0.5 });
const gold = new THREE.MeshStandardMaterial({ color: 0xd4af37, metalness: 0.7, roughness: 0.2 });
const marble = new THREE.MeshStandardMaterial({ color: 0xf5f5f5, roughness: 0.1 });
const velvet = new THREE.MeshStandardMaterial({ color: 0x800020, roughness: 0.8 });
const glass = new THREE.MeshStandardMaterial({ color: 0xffffff, metalness: 0.1, roughness: 0.0, transparent: true, opacity: 0.4 });
```

**Four-poster bed example:**
```javascript
function buildFourPosterBed(x, z) {
    const g = new THREE.Group();
    g.position.set(x, 0, z);
    scene.add(g);

    // Frame & mattress
    const frame = new THREE.Mesh(new THREE.BoxGeometry(1.5, 0.35, 2.1), euroWood);
    frame.position.y = 0.35; frame.castShadow = true; g.add(frame);
    const mattress = new THREE.Mesh(new THREE.BoxGeometry(1.4, 0.15, 2.0), new THREE.MeshStandardMaterial({ color: 0xfafafa }));
    mattress.position.y = 0.55; g.add(mattress);
    const blanket = new THREE.Mesh(new THREE.BoxGeometry(1.42, 0.12, 1.4), velvet);
    blanket.position.set(0, 0.62, 0.25); g.add(blanket);

    // Four posts + canopy rails
    for (let px of [-0.7, 0.7]) {
        for (let pz of [-1.0, 1.0]) {
            const post = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, 2.4, 8), darkWood);
            post.position.set(px, 1.2, pz); post.castShadow = true; g.add(post);
            const finial = new THREE.Mesh(new THREE.SphereGeometry(0.07, 8, 8), gold);
            finial.position.set(px, 2.42, pz); g.add(finial);
        }
        const rail = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, 2.0, 6), darkWood);
        rail.position.set(px, 2.25, 0); rail.rotation.x = Math.PI / 2; g.add(rail);
    }

    // Headboard with tufted buttons
    const headboard = new THREE.Mesh(new THREE.BoxGeometry(1.5, 0.8, 0.06), euroWood);
    headboard.position.set(0, 0.8, -1.03); g.add(headboard);
    for (let i = 0; i < 3; i++) {
        const tuft = new THREE.Mesh(new THREE.SphereGeometry(0.04, 6, 6), gold);
        tuft.position.set(-0.3 + i * 0.3, 0.85, -0.99); g.add(tuft);
    }

    addBoxCollider(x, 0.6, z, 1.6, 1.2, 2.2);
}
```

**Fireplace + mirror combo:**
```javascript
function buildFireplace(x, z) {
    const g = new THREE.Group();
    g.position.set(x, 0, z);
    scene.add(g);

    const body = new THREE.Mesh(new THREE.BoxGeometry(2.2, 1.2, 0.5), marble);
    body.position.y = 0.6; g.add(body);
    const inner = new THREE.Mesh(new THREE.BoxGeometry(1.2, 0.8, 0.2), new THREE.MeshStandardMaterial({ color: 0x1a1a1a }));
    inner.position.set(0, 0.5, 0.16); g.add(inner);
    const mantle = new THREE.Mesh(new THREE.BoxGeometry(2.6, 0.15, 0.6), marble);
    mantle.position.set(0, 1.275, 0.05); g.add(mantle);

    // Columns + caps
    for (let sx of [-1.0, 1.0]) {
        const col = new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.12, 1.35, 8), marble);
        col.position.set(sx, 0.675, 0); g.add(col);
        const cap = new THREE.Mesh(new THREE.SphereGeometry(0.14, 8, 8), gold);
        cap.position.set(sx, 1.4, 0); g.add(cap);
    }

    // Mirror above
    const mFrame = new THREE.Mesh(new THREE.BoxGeometry(1.0, 1.4, 0.06), gold);
    mFrame.position.set(0, 2.3, 0.08); g.add(mFrame);
    const mGlass = new THREE.Mesh(new THREE.BoxGeometry(0.8, 1.2, 0.04), new THREE.MeshStandardMaterial({ color: 0xcceeff, metalness: 0.9, roughness: 0 }));
    mGlass.position.set(0, 2.3, 0.1); g.add(mGlass);

    addBoxCollider(x, 0.6, z, 2.6, 1.35, 0.6);
}
```

**Chandelier:**
```javascript
function buildChandelier(x, y, z) {
    const g = new THREE.Group();
    g.position.set(x, y, z);
    scene.add(g);
    for (let r of [0.15, 0.35, 0.55]) {
        const ring = new THREE.Mesh(new THREE.TorusGeometry(r, 0.015, 8, 24), gold);
        ring.rotation.x = Math.PI / 2; g.add(ring);
    }
    const center = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, 0.6, 8), gold);
    center.position.y = 0.3; g.add(center);
    for (let i = 0; i < 8; i++) {
        const angle = (i / 8) * Math.PI * 2;
        const cry = new THREE.Mesh(new THREE.SphereGeometry(0.04, 6, 6), glass);
        cry.position.set(Math.cos(angle) * 0.35, -0.15, Math.sin(angle) * 0.35);
        g.add(cry);
    }
}
```

### Hiding Overlapping Placeholders

When procedural furniture replaces an existing placeholder at the same coordinates, hide the old mesh by name to prevent z-fighting:

```javascript
function buildEuropeanDecor() {
    ['_placeholder_bed', '_placeholder_sofa', '_placeholder_desk',
     '_placeholder_chair', '_placeholder_fridge', '_placeholder_cabinet',
     '_placeholder_table', 'paper'].forEach(name => {
        const obj = scene.getObjectByName(name);
        if (obj) obj.visible = false;
    });
    // ...procedural furniture code...
}
```

**Pitfall — Missing `.name` on placeholders:** If a placeholder mesh was created without explicitly setting `.name`, `getObjectByName()` returns `undefined` and it remains visible. Always assign `.name` when creating placeholder furniture:

```javascript
const table = new THREE.Mesh(new THREE.BoxGeometry(1.2, 0.8, 0.6), woodMat);
table.name = '_placeholder_table';  // Required for later hiding
scene.add(table);
```

### Keeping Placeholder and External Model Positions in Sync

If your project has both placeholder blocks (for collision/fallback) and external model loaders (Kenney/GLTF), any layout change must be applied to **both** code paths or the external models will load in the wrong spots and overlap.

Workflow:
1. Adjust the placeholder `position.set(...)` and `addBoxCollider(...)` in `buildFurniture()`.
2. Adjust the corresponding `placeKenney(...)` or `placeModel(...)` call with the same world coordinates.
3. If the model needs rotation to align with a wall, add `rotationY` support to the loader (see above) and pass the same angle used by the placeholder's `.rotation.y`.

After a large layout refactor, search the file for both `position.set` and `placeKenney` to verify nothing is out of sync.
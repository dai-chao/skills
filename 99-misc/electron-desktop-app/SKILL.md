---
name: electron-desktop-app
description: |
  Scaffold, build, package, and customize cross-platform desktop apps with Electron.
  Covers project setup, main/renderer IPC, security, theming, native menus, file dialogs,
  and packaging for macOS/Windows/Linux.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [electron, desktop, cross-platform, macos, windows, packaging, electron-builder]
    category: software-development
    related_skills: [macos-development, software-development-methodologies]
---

# Electron Desktop App Development

## When to Use This Skill

Trigger when the user wants to:
- Build a cross-platform desktop app with Electron
- Package an existing web app into a native desktop app
- Scaffold a new Electron project with proper security practices
- Add native features (file dialogs, menus, auto-updater, notifications)
- Build and sign for macOS (.dmg, .app) or Windows (.exe, .msi)

## Quick Start: Scaffold a New Electron App

```bash
mkdir my-electron-app && cd my-electron-app
npm init -y
npm install electron electron-builder --save-dev
```

**package.json** (minimal with build config):
```json
{
  "name": "my-app",
  "version": "1.0.0",
  "main": "main.js",
  "scripts": {
    "start": "electron .",
    "build": "electron-builder",
    "build:mac": "electron-builder --mac",
    "build:win": "electron-builder --win",
    "build:all": "electron-builder --mac --win",
    "pack": "electron-builder --dir"
  },
  "build": {
    "appId": "com.example.myapp",
    "productName": "MyApp",
    "directories": { "output": "dist" },
    "files": ["main.js", "renderer/**/*", "package.json"],
    "mac": {
      "category": "public.app-category.utilities",
      "target": [{ "target": "dmg", "arch": ["x64", "arm64"] }]
    },
    "win": {
      "target": [{ "target": "nsis", "arch": ["x64"] }]
    }
  }
}
```

## Security: Context Isolation + Preload Bridge

**NEVER** use `nodeIntegration: true`. Always use `contextIsolation: true` with a preload script.

**main.js:**
```js
const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');

function createWindow() {
  const win = new BrowserWindow({
    width: 900, height: 700,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'renderer', 'preload.js')
    }
  });
  win.loadFile(path.join(__dirname, 'renderer', 'index.html'));
}
```

**renderer/preload.js:**
```js
const { contextBridge, ipcRenderer } = require('electron');
contextBridge.exposeInMainWorld('electronAPI', {
  selectFiles: () => ipcRenderer.invoke('select-files'),
  // expose only what the renderer needs
});
```

## IPC Patterns

**Main → Renderer (one-way):**
```js
// main.js
win.webContents.send('update-available', version);

// renderer
window.electronAPI.onUpdate((version) => { ... });
// preload: onUpdate: (cb) => ipcRenderer.on('update-available', (_, v) => cb(v))
```

**Renderer → Main (invoke/handle):**
```js
// renderer
const result = await window.electronAPI.selectFiles();

// main.js
ipcMain.handle('select-files', async () => {
  const { dialog } = require('electron');
  const result = await dialog.showOpenDialog({ properties: ['openFile'] });
  return result.filePaths;
});
```

## Common Pitfalls

1. **ContextIsolation disabled** — Using `nodeIntegration: true` or `contextIsolation: false` exposes full Node.js to renderer, a security risk. Always use preload bridge.

2. **Path resolution in packaged app** — In dev, `__dirname` is the project root. In packaged app, it's inside `app.asar`. Use `path.join(__dirname, 'renderer', 'file.html')` consistently.

3. **macOS code signing on local builds** — If you don't have an Apple Developer cert, set `CSC_IDENTITY_AUTO_DISCOVERY=false` to skip signing for local testing:
   ```bash
   CSC_IDENTITY_AUTO_DISCOVERY=false npm run pack
   ```
   See [macos-development skill](skill://macos-development) for full signing details.

4. **Electron download timeouts** — If GitHub is slow, use a mirror:
   ```bash
   export ELECTRON_MIRROR="https://npmmirror.com/mirrors/electron/"
   ```

5. **File protocol restrictions** — Renderer cannot directly access filesystem paths. Use `file://` URLs or pass file contents via IPC.

## Bundling Static Assets (Music, Images, Data)

To ship files inside the app package (e.g., a music player with built-in tracks), use `extraResources` in `package.json`:

```json
{
  "build": {
    "files": ["main.js", "renderer/**/*", "package.json"],
    "extraResources": [
      {
        "from": "assets/music",
        "to": "music",
        "filter": ["**/*"]
      }
    ]
  }
}
```

Then resolve the path differently in dev vs production:

```js
// main.js
const path = require('path');

function getResourcePath(resourceName) {
  const isDev = !app.isPackaged;
  if (isDev) {
    return path.join(__dirname, 'assets', resourceName);
  }
  // In packaged app, extraResources land in resources/ next to app.asar
  return path.join(process.resourcesPath, resourceName);
}

// Usage: getResourcePath('music') → .../MyApp.app/Contents/Resources/music
```

**Pitfall:** Don't put large assets in `"files"` — they get bundled into `app.asar` which is read-only and has path quirks. Use `extraResources` for anything the app needs to read at runtime via filesystem APIs.

## Packaging Commands

| Command | Output |
|---------|--------|
| `npm run pack` | Unpacked dir for testing (no installer) |
| `npm run build:mac` | `.dmg` + `.zip` for macOS |
| `npm run build:win` | `.exe` installer for Windows |
| `npm run build:all` | Both platforms |

## macOS-Specific Notes

- `titleBarStyle: 'hiddenInset'` gives a modern look on macOS
- `app.on('activate')` is required for macOS dock click behavior
- `app.on('window-all-closed')` should NOT quit on macOS (standard behavior)
- Notarization requires Apple Developer account; skip for local testing

See [references/electron-macos-build.md](references/electron-macos-build.md) from the macos-development skill for detailed signing/notarization troubleshooting.

## UI Patterns: Minimal Dark Player (NetEase/Spotify Style)

When the user wants a music player or media app, they prefer:
- **Compact window** (500x600 or smaller), not large desktop-app sizes
- **Dark theme** with warm accent (orange `#ff6b35` rather than default green)
- **Minimal controls**: play/pause, prev/next, progress bar, playlist only
- **No add-file UI** — music is bundled via `extraResources`, loaded automatically on boot
- **macOS title bar**: use `titleBarStyle: 'hiddenInset'` but pad the header (`padding-top: 32px`) to avoid overlap with traffic lights
- **Playback mode**: loop entire playlist (no shuffle/repeat toggle needed)
- **Animations**: audio visualizer bars driven by real audio data (Web Audio API), not CSS fake animations. See `templates/electron-audio-player/` for the complete implementation.

## UI Patterns: Warm-Editorial Dashboard (Agent Guard Style)

When the user wants a desktop app for **data dashboards, security tools, or admin panels**, they prefer a warm-editorial design language rather than the default dark/tech look:
- **Cream canvas** (`#faf9f5`) as the main page floor, not cool gray or pure white
- **Warm coral primary accent** (`#cc785c`) for CTAs and featured states, with active darker variant `#a9583e`
- **Dark navy product surfaces** (`#181715`) for code blocks, mockups, terminal panels, or high-contrast detail cards
- **Serif display type** (e.g., Cormorant Garamond / Tiempos Headline) for page titles and section headers at weight 400 with negative letter-spacing
- **Humanist sans body** (Inter / StyreneB) at 400/500 for UI labels, buttons, tables, and captions
- **Generous whitespace** — 32px card padding, 24px section gaps, 96px between major bands
- **Color-block elevation** — use cream cards (`#efe9de`) and dark cards (`#181715`) instead of heavy drop shadows
- **No pure-white cards or blue/cyan accents** — the warm cream + coral + dark navy trinity is the brand signature

This palette works well for security dashboards, audit logs, and permission managers because the coral draws attention to warnings and risks while the cream keeps the interface readable for long sessions. See `templates/electron-warm-dashboard/` for a starter using this style.

### Audio Visualizer: Real Data, Not CSS Fake

**Pitfall:** Do NOT use CSS `@keyframes` animations for the visualizer. The user explicitly rejected this as "too fake." Use the Web Audio API `AnalyserNode` instead.

**Pattern:**
```js
let audioCtx, analyser, source, dataArray;

function initAudioContext() {
  if (audioCtx) return;
  audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  analyser = audioCtx.createAnalyser();
  analyser.fftSize = 64;
  analyser.smoothingTimeConstant = 0.8;
  source = audioCtx.createMediaElementSource(audioElement);
  source.connect(analyser);
  analyser.connect(audioCtx.destination);
  dataArray = new Uint8Array(analyser.frequencyBinCount);
}

function updateVisualizer() {
  if (!analyser || !isPlaying) return;
  analyser.getByteFrequencyData(dataArray);
  // Map frequency bins to bar heights
  const bars = document.querySelectorAll('.visualizer .bar');
  const step = Math.floor(dataArray.length / bars.length);
  for (let i = 0; i < bars.length; i++) {
    let sum = 0;
    for (let j = 0; j < step; j++) sum += dataArray[i * step + j];
    const avg = sum / step;
    const height = 4 + (avg / 255) * maxHeight;
    bars[i].style.height = height + 'px';
  }
  requestAnimationFrame(updateVisualizer);
}
```

**Critical Pitfall — Autoplay + Visualizer Not Starting:**
When the app auto-plays on boot (e.g., `playTrack(0)` in `init()`), the visualizer often stays flat on first play but works after pause/resume. This is because Chromium's autoplay policy suspends the `AudioContext` until the audio element truly starts outputting.

**Fix:** Use the `<audio>` element's `'playing'` event (not `play().then()`) to start the visualizer:

```js
function playTrack(index) {
  initAudioContext();
  audio.src = tracks[index].path;

  const onPlaying = () => {
    audio.removeEventListener('playing', onPlaying);
    if (audioCtx && audioCtx.state === 'suspended') {
      audioCtx.resume();
    }
    isPlaying = true;
    updatePlayButton();
    updateVisualizer(); // NOW the analyser has real data
  };

  audio.addEventListener('playing', onPlaying);
  audio.play().catch(err => {
    console.error('播放失败:', err);
    audio.removeEventListener('playing', onPlaying);
  });
}
```

**Why this works:** The `'playing'` event fires when the audio element actually begins producing sound, which is *after* the autoplay policy allows it. `play().then()` resolves too early — the audio context may still be suspended and the analyser has no data yet.

**Key points:**
- Create `MediaElementSource` from the `<audio>` element, connect to `AnalyserNode`, then to destination
- Call `getByteFrequencyData()` each frame via `requestAnimationFrame`
- Map the `Uint8Array` (0-255) to pixel heights
- Stop the loop on pause, reset bars to minimum height
- Resume `audioCtx` if suspended (browsers block autoplay until user interaction)
- **Always start the visualizer from the `'playing'` event, not `play().then()`**

### Layout: Left Sidebar + Right Control Panel

The user pivoted from a stacked layout to a **left/right split**:
- **Left sidebar** (260px): playlist with track names, playing indicator (pulsing dot), track count header
- **Right main area**: large visualizer, song title, progress bar, playback controls
- Window size should be wider to accommodate both panels (e.g., 800x500)

See `templates/electron-audio-player/` for the complete left/right implementation.

## Templates

The `templates/electron-audio-player/` directory contains a complete working starter with bundled music support, left/right layout, and real Web Audio visualizer:

| File | Purpose |
|------|---------|
| `package.json` | Build config with `extraResources` for shipping assets |
| `main.js` | Main process with `getResourcePath()` + `scanAudioFiles()` helpers, 1726x1242 window |
| `preload.js` | Context-isolated IPC bridge |
| `index.html` | Left sidebar (playlist) + right panel (visualizer + controls), 100 bars |
| `style.css` | Dark theme, left/right layout, real-data visualizer bars, pulse indicators, play-button glow |
| `app.js` | Web Audio API visualizer with `'playing'` event fix, playlist loop, progress bar, auto-play on boot, keyboard shortcuts |

## Customizing AI coding assistants

This section covers installing, theming, and safely customizing desktop AI coding assistants (Codex, Claude, Cursor, etc.) on macOS. Session-specific notes for the Codex Dream Skin case study are in `references/ai-coding-assistant-case-study.md`.

### When to use

- User drops a GitHub URL for a theme/customizer repo without explanation.
- User wants to install, switch, or restore a theme for a local AI coding assistant.
- User reports theme/CDP/injector issues.

### General workflow

1. Inspect the repo README and platform-specific docs (e.g. `macos/README.md`).
2. Pre-flight: verify the target app is installed, locate its bundle, and close it before running installers that modify config.
3. Run tests if available (e.g. `cd macos && npm test` or `scripts/doctor-macos.sh`).
4. Install via the repo's entry script (prefer `--no-launch`).
5. Start with the customizer's CDP/debug port and verify the injector is alive.
6. Switch built-in presets or import custom backgrounds.
7. Verify and screenshot.
8. Restore official appearance when done.

### Safety boundaries

- Never modify the target app's `.app`, `app.asar`, `WindowsApps`, or code signature.
- Prefer tools that use local loopback CDP (127.0.0.1) and validate the listener belongs to the target app.
- Close the target app before installers that back up `config.toml`.
- Keep custom backgrounds UI-free: no window chrome, sidebars, cards, buttons, text, or watermarks.
- Recommended master size: `2560 × 1440`, ≤ 16 MB, ≤ 16384 px per side.

### Common issues

| Symptom | Fix |
|---------|-----|
| "Close Codex before installation" | Quit the target app and rerun installer |
| Start script times out but injector launched | Check logs/state; run `verify` again |
| `theme.json` color overrides not picked up | Reload route or restart the injector |
| Background has UI/chrome embedded | Regenerate a pure `2560×1440` wallpaper and re-import |
| "Theme not found" | Check `themes/` directory for valid IDs |

### References

- `references/ai-coding-assistant-case-study.md` — Codex Dream Skin macOS case study with exact paths, preset IDs, import command, and theme color override recipe.

## References

- `templates/electron-audio-player/` — Complete working audio player template (main.js, preload.js, renderer with dark UI, bundled assets, visualizer animations)

# Electron Warm-Editorial Dashboard Starter

A starter template for Electron desktop apps using the warm-editorial design language (cream canvas + coral accents + dark navy product surfaces). Suitable for security dashboards, audit log viewers, permission managers, and admin panels.

## Design Tokens

- Canvas: `#faf9f5`
- Surface card: `#efe9de`
- Primary coral: `#cc785c`
- Primary active: `#a9583e`
- Ink: `#141413`
- Body: `#3d3d3a`
- Muted: `#6c6a64`
- Hairline: `#e6dfd8`
- Surface dark: `#181715`
- Success: `#5db872`
- Warning: `#d4a017`
- Error: `#c64545`

## Typography

- Display: Cormorant Garamond (serif), weight 400, negative letter-spacing
- Body: Inter (humanist sans), weight 400/500
- Code: JetBrains Mono

## Included Components

- Left sidebar navigation with active state
- Top header with page title and action buttons
- Stat cards (total, warning, danger, success)
- Content band with header + link
- Log list with severity dots
- Data table with badges
- Filter chips
- Permission list with removable tags
- Modal dialog
- Form input with focus ring

## Files

- `package.json` — Electron build config
- `main.js` — Main process with IPC handlers
- `preload.js` — Secure context bridge
- `renderer/index.html` — Main UI
- `renderer/style.css` — Warm-editorial design system
- `renderer/app.js` — Frontend state and rendering

## Running

```bash
cd templates/electron-warm-dashboard
npm install
npm start
```

## Security Notes

- Uses `contextIsolation: true` and `nodeIntegration: false`
- All filesystem access goes through `ipcMain.handle` from the main process
- Renderer cannot access Node.js APIs directly

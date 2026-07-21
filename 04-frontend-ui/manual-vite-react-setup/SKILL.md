---
name: manual-vite-react-setup
title: Manual Vite React Setup (Bypassing create-vite)
description: When create-vite fails due to Node version incompatibility or network issues, manually scaffold a minimal Vite + React + React Router project.
triggers:
  - create-vite throws "styleText" or Node version errors
  - Node.js < 20 and need a Vite React project
  - Need minimal React router project without relying on interactive CLI tools
---

# Manual Vite React Setup

## Problem
`npm create vite@latest` fails on older Node.js (e.g., v18) because newer create-vite requires Node 20+.

## Solution: Manual Scaffolding

Create these files in the target directory:

### 1. package.json
```json
{
  "name": "react-app",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.22.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@vitejs/plugin-react": "^4.2.0",
    "vite": "^5.0.0"
  }
}
```

### 2. vite.config.js
```js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
})
```

### 3. index.html
```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>React App</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
```

### 4. src/main.jsx
```jsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
)
```

### 5. src/App.jsx
Basic router shell:
```jsx
import { Routes, Route, NavLink } from 'react-router-dom'

function App() {
  return (
    <>
      <nav>
        <NavLink to="/" end>Home</NavLink>
      </nav>
      <Routes>
        <Route path="/" element={<div>Home</div>} />
      </Routes>
    </>
  )
}
export default App
```

### 6. src/index.css
```css
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body, #root { width: 100%; height: 100%; }
```

## Install & Run
```bash
npm install
npx vite --port 5173
```

If `npx vite` hangs or has no stdout in background mode, verify with:
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:5173/
```

## Pitfalls
- Do NOT use `create-vite` CLI on Node 18; it will crash with `styleText` export errors.
- Vite 5.x works fine on Node 18; only the `create-vite` scaffolding tool is incompatible.
- Backgrounding with `&` in terminal foreground is blocked; use `terminal(background=true)` for dev servers.
- Dev server stdout may be buffered when run in background; use HTTP health checks instead of watching logs.

## Tailwind CSS v4 + Vite 5 Integration (Node 18 Compatible)

Tailwind CSS v4 uses a Vite-native plugin and eliminates the traditional `tailwind.config.js`. On Node 18, use this exact setup:

### package.json (additional devDependencies)
```json
{
"devDependencies": {
  "tailwindcss": "^4.3.1",
  "@tailwindcss/vite": "^4.3.1",
  "@vitejs/plugin-react": "^4.3.4",
  "vite": "^5.4.11"
}
}
```

### vite.config.ts
```ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
plugins: [react(), tailwindcss()],
})
```

### src/index.css
```css
@import "tailwindcss";

@theme {
--color-void: #0a0a0f;
--color-surface: #13131f;
--color-accent: #6366f1;
}
```

**Key differences from Tailwind v3:**
- No `tailwind.config.js` — configuration lives in CSS via `@theme`
- No `postcss` or `autoprefixer` needed
- Plugin is `@tailwindcss/vite`, not `@tailwindcss/postcss`
- Colors/utilities defined with CSS custom property syntax (`--color-*`, `--font-*`)

## Leaflet + React Map Integration Pattern

For interactive maps with Leaflet in React:

```bash
npm install leaflet react-leaflet @types/leaflet
```

### Key implementation notes
- Use `react-leaflet` components (`MapContainer`, `TileLayer`, `GeoJSON`, `Marker`)
- Custom markers via `L.DivIcon` with inline SVG for crisp rendering at any size
- Dark map theme: use CARTO dark tiles + CSS `filter: invert(1) hue-rotate(180deg) brightness(0.7) contrast(1.2) saturate(0.3)` on `.leaflet-tile-pane`
- GeoJSON layers for isochrones/polygons with dynamic `style` function based on feature properties
- Always set `zoomControl={false}` and build custom controls for consistent UI theming

See `references/leaflet-isochrone-patterns.md` for complete isochrone map implementation details.

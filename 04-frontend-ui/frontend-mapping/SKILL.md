---
name: frontend-mapping
description: "Build interactive map web apps with React, Leaflet, and real geospatial data. Covers isochrones, routing layers, dark-themed UI, and API proxying for CORS-blocked geoservices."
version: 1.0.0
author: assistant
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [maps, leaflet, react, isochrone, geospatial, openstreetmap, carto, vite, proxy, cors]
    category: software-development
    requires_toolsets: [terminal, web, browser]
---

# Frontend Mapping Skill

Build beautiful, interactive map web applications with React + Leaflet + real geospatial APIs.

## When to Use

- User wants an isochrone map (travel-time reachable areas)
- User wants a route planner with multiple transport modes
- User wants to visualize POIs, airports, train stations on a map
- User wants a dark-themed, unique map UI (not default Google Maps look)
- User needs to proxy geospatial APIs to bypass CORS in browser

## Tech Stack

- **Framework:** Vite + React + TypeScript
- **Map Engine:** Leaflet + react-leaflet
- **Styling:** Tailwind CSS v4 + custom dark theme
- **Animations:** Framer Motion for UI panels
- **Icons:** Lucide React
- **Tile Layer:** CARTO dark_matter / dark_all (free, no key needed)
- **Isochrone API:** OpenRouteService (ORS) — free tier 2000 req/day

## Project Scaffolding

```bash
npm create vite@latest my-map -- --template react-ts
npm install leaflet react-leaflet @types/leaflet lucide-react framer-motion
npm install -D tailwindcss @tailwindcss/vite
```

Vite config with proxy for ORS:

```typescript
// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/ors-api': {
        target: 'https://api.openrouteservice.org',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/ors-api/, ''),
        secure: true,
      },
    },
  },
})
```

## CSS: Dark Theme for Leaflet

```css
@import "tailwindcss";

@theme {
  --color-void: #0a0a0f;
  --color-surface: #13131f;
  --color-accent: #6366f1;
  /* ... etc */
}

html, body, #root { width: 100%; height: 100%; overflow: hidden; }

.leaflet-container { background: #0a0a0f !important; }
.leaflet-tile-pane {
  filter: invert(1) hue-rotate(180deg) brightness(0.7) contrast(1.2) saturate(0.3);
}
```

## Isochrone API Integration

```typescript
// src/api.ts
const ORS_BASE = '/ors-api/v2/isochrones';

export async function fetchIsochrones(
  lat: number, lng: number, mode: string, ranges: number[]
) {
  const response = await fetch(ORS_BASE, {
    method: 'POST',
    headers: {
      'Authorization': 'YOUR_ORS_API_KEY',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      locations: [[lng, lat]],
      profile: mode,
      range: ranges,
      range_type: 'time',
      smoothing: 10,
    }),
  });
  return response.ok ? await response.json() : null;
}
```

**Fallback when API fails:** generate concentric polygons based on average speed per mode:

| Mode | Speed |
|------|-------|
| foot-walking | 5 km/h |
| cycling-regular | 15 km/h |
| public-transport | 25 km/h |
| driving-car | 40 km/h |

## Key Pitfalls

1. **CORS on ORS API** — Browser blocks direct `fetch()` to `api.openrouteservice.org`. Always use Vite proxy (`/ors-api`) or a backend relay.

2. **ORS API Key** — Register at https://openrouteservice.org/sign-up/ for free key. The demo key in docs expires. Replace before production.

3. **Leaflet height bug** — If `leaflet-container` grows to 100000+ px, Tailwind `h-full` isn't resolving. Ensure `html, body, #root` all have `height: 100%`.

4. **Node version** — Vite 8+ requires Node 20+. On older Node (e.g. 18), downgrade to Vite 5: `npm install vite@5.4.11 --save-dev`.

5. **Tailwind v4 + Vite 5** — Need `@tailwindcss/vite` plugin in `vite.config.ts`. The old `postcss` approach doesn't work with Tailwind v4.

6. **Tile layer attribution** — CARTO tiles require attribution: `&copy; OpenStreetMap contributors &copy; CARTO`.

7. **React StrictMode double-mount** — In dev, `useEffect` runs twice. Isochrone fetches should be cancellable (use a `cancelled` flag) to avoid race conditions.

## Verification

```bash
cd my-map
npm run dev
# Open http://localhost:5173/
# Check: map loads dark, city selector works, transport mode switches,
# isochrone polygons render with gradient colors.
```

## References

- `references/ors-cors-proxy.md` — CORS error transcript and proxy fix
- `references/leaflet-tailwind-dark-theme.md` — Complete CSS for dark maps

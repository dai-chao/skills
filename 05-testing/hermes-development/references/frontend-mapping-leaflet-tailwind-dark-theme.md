# Leaflet + Tailwind v4 Dark Theme — Complete CSS

## Problem

Default Leaflet looks garishly bright against a dark UI. Tailwind v4's `@import "tailwindcss"` doesn't automatically apply to Leaflet's DOM elements.

## Solution

### 1. Tailwind v4 Setup

```bash
npm install -D tailwindcss @tailwindcss/vite
```

```typescript
// vite.config.ts
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
})
```

```css
/* src/index.css */
@import "tailwindcss";

@theme {
  --color-void: #0a0a0f;
  --color-surface: #13131f;
  --color-surface-raised: #1a1a2e;
  --color-surface-hover: #22223a;
  --color-border: #2a2a3e;
  --color-text-primary: #f0f0f5;
  --color-text-secondary: #8a8a9e;
  --color-text-muted: #5a5a6e;
  --color-accent: #6366f1;
  --color-accent-glow: #818cf8;
  --color-airport: #f59e0b;
  --color-train: #10b981;
}
```

### 2. Leaflet Dark Overrides

```css
/* Invert tile colors for dark theme */
.leaflet-tile-pane {
  filter: invert(1) hue-rotate(180deg) brightness(0.7) contrast(1.2) saturate(0.3);
}

/* Dark attribution box */
.leaflet-control-attribution {
  background: rgba(10, 10, 15, 0.8) !important;
  color: #5a5a6e !important;
}

/* Dark popups */
.leaflet-popup-content-wrapper {
  background: #1a1a2e !important;
  border: 1px solid #2a2a3e !important;
  color: #f0f0f5 !important;
}
```

### 3. Glass Morphism Panels

```css
.glass-panel {
  background: rgba(19, 19, 31, 0.85);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(42, 42, 62, 0.6);
}
```

### 4. Isochrone Gradient Colors

```css
@theme {
  --color-iso-15: rgba(99, 102, 241, 0.65);
  --color-iso-30: rgba(139, 92, 246, 0.50);
  --color-iso-45: rgba(168, 85, 247, 0.35);
  --color-iso-60: rgba(192, 75, 220, 0.22);
  --color-iso-90: rgba(217, 70, 239, 0.12);
  --color-iso-120: rgba(236, 72, 153, 0.08);
}
```

## Tile Layer Recommendation

```tsx
<TileLayer
  url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
/>
```

CARTO dark tiles are free, no API key, and look great with the inverted filter approach.

# Leaflet Isochrone Map — Implementation Patterns

Condensed reference from building a production isochrone map with React + Leaflet + OpenRouteService.

## OpenRouteService Isochrone API

```typescript
const ORS_API_KEY = 'your-key-here'; // free at openrouteservice.org
const ORS_BASE = 'https://api.openrouteservice.org/v2/isochrones';

async function fetchIsochrones(lat: number, lng: number, profile: string, ranges: number[]) {
  const response = await fetch(ORS_BASE, {
    method: 'POST',
    headers: {
      'Authorization': ORS_API_KEY,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      locations: [[lng, lat]],
      profile, // 'foot-walking' | 'cycling-regular' | 'driving-car' | 'public-transport'
      range: ranges, // seconds, e.g. [900, 1800, 2700, 3600, 5400, 7200]
      range_type: 'time',
      smoothing: 10,
      location_type: 'start',
    }),
  });
  return await response.json(); // GeoJSON FeatureCollection
}
```

**Profiles:** `foot-walking`, `cycling-regular`, `driving-car`, `public-transport` (experimental)

## Fallback Isochrone Generation (when API fails)

```typescript
function generateFallbackIsochrones(lat: number, lng: number, mode: string, ranges: number[]) {
  const speedKmh: Record<string, number> = {
    'foot-walking': 5,
    'cycling-regular': 15,
    'public-transport': 25,
    'driving-car': 40,
  };
  const speed = speedKmh[mode] || 5;
  const features = ranges.map(minutes => {
    const radiusKm = (speed * minutes) / 60;
    const radiusDeg = radiusKm / 111;
    const points: [number, number][] = [];
    for (let i = 0; i <= 64; i++) {
      const angle = (i / 64) * Math.PI * 2;
      const dx = radiusDeg * Math.cos(angle) / Math.cos(lat * Math.PI / 180);
      const dy = radiusDeg * Math.sin(angle);
      points.push([lng + dx, lat + dy]);
    }
    return {
      type: 'Feature',
      geometry: { type: 'Polygon', coordinates: [points] },
      properties: { value: minutes * 60, group_index: 0, center: [lng, lat] },
    };
  });
  return { type: 'FeatureCollection', features: features.reverse() };
}
```

## React-Leaflet GeoJSON Layer with Dynamic Styling

```tsx
import { GeoJSON } from 'react-leaflet';

const ISOCHRONE_RANGES = [
  { value: 15, color: 'rgba(99, 102, 241, 0.65)' },
  { value: 30, color: 'rgba(139, 92, 246, 0.50)' },
  { value: 45, color: 'rgba(168, 85, 247, 0.35)' },
  { value: 60, color: 'rgba(192, 75, 220, 0.22)' },
  { value: 90, color: 'rgba(217, 70, 239, 0.12)' },
  { value: 120, color: 'rgba(236, 72, 153, 0.08)' },
];

function IsochroneLayer({ data }) {
  const getStyle = (feature) => {
    const minutes = feature.properties.value / 60;
    const range = ISOCHRONE_RANGES.find(r => r.value === minutes);
    return {
      fillColor: range?.color || 'rgba(99, 102, 241, 0.3)',
      fillOpacity: 0.6,
      color: range?.color?.replace(/[\d.]+\)$/, '0.8)') || 'rgba(99, 102, 241, 0.8)',
      weight: 1.5,
    };
  };
  return <GeoJSON data={data} style={getStyle} />;
}
```

## Custom DivIcon Markers (Airport / Train / Center)

```typescript
const airportIcon = new L.DivIcon({
  html: `<div style="background:#f59e0b;width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;border:2px solid #0a0a0f;box-shadow:0 2px 8px rgba(245,158,11,0.5);"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#0a0a0f" stroke-width="2.5"><path d="M2 12h20"/><path d="M13 2l-4 10h6l-4 10"/></svg></div>`,
  className: '',
  iconSize: [28, 28],
  iconAnchor: [14, 14],
});
```

## Dark Theme Map CSS

```css
.leaflet-container {
  background: #0a0a0f !important;
}
.leaflet-tile-pane {
  filter: invert(1) hue-rotate(180deg) brightness(0.7) contrast(1.2) saturate(0.3);
}
.leaflet-popup-content-wrapper {
  background: #1a1a2e !important;
  border: 1px solid #2a2a3e !important;
  color: #f0f0f5 !important;
}
```

## Data Model — City with Transport Hubs

```typescript
interface City {
  id: string;
  name: string;
  nameEn: string;
  country: string;
  lat: number;
  lng: number;
  zoom: number;
  airports: { code: string; name: string; lat: number; lng: number; transitMinutes: number }[];
  trainStations: { name: string; lat: number; lng: number; type: 'high-speed' | 'regional' | 'subway' }[];
}
```

## Pitfalls
- **ORS API requires signup** — the free tier is generous but you need an API key
- **CORS in browser tools** — when testing from remote browsers, ORS API may be blocked; always implement fallback
- **Leaflet container height** — must have explicit height (e.g. `style={{ width: '100%', height: '100%' }}`) or map won't render
- **Tile loading on dark theme** — CARTO dark tiles load faster than filtered light tiles; use `https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png`
- **React 19 + react-leaflet** — ensure `@types/leaflet` is installed; react-leaflet v4 works with React 19

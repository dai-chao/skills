# OpenRouteService CORS Error — Fix with Vite Proxy

## Error Transcript

```
Access to fetch at 'https://api.openrouteservice.org/v2/isochrones' from origin
'http://localhost:5173' has been blocked by CORS policy:
No 'Access-Control-Allow-Origin' header is present on the requested resource.

POST https://api.openrouteservice.org/v2/isochrones net::ERR_FAILED 502 (Bad Gateway)
```

## Root Cause

ORS API does not send `Access-Control-Allow-Origin` headers. Browser `fetch()` from `localhost:5173` is blocked by CORS policy. Additionally, the demo/placeholder API key may return 502 Bad Gateway.

## Fix: Vite Dev Server Proxy

Configure `vite.config.ts` to proxy `/ors-api` → `https://api.openrouteservice.org`:

```typescript
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

Then change API base URL from absolute to relative:

```typescript
// Before (broken):
const ORS_BASE = 'https://api.openrouteservice.org/v2/isochrones'

// After (works):
const ORS_BASE = '/ors-api/v2/isochrones'
```

## Alternative Fixes

1. **Backend relay** — Express/Node server that calls ORS server-side and forwards response
2. **Local ORS instance** — Docker `docker run -p 8080:8080 openrouteservice/openrouteservice` (needs 8GB+ RAM)
3. **Browser extension** — CORS unblocker (dev only, not for users)

## Getting a Real API Key

1. Visit https://openrouteservice.org/sign-up/
2. Create account, generate API key
3. Replace `'YOUR_ORS_API_KEY'` in `src/api.ts`
4. Free tier: 2000 requests/day

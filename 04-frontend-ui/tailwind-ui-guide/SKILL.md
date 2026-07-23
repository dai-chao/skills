---
name: tailwind-ui-guide
description: A Tailwind UI design system guide for building consistent, accessible interfaces. Use this whenever the user asks about Tailwind UI, theming, component styling, color palettes, dark mode, or any Tailwind-driven layout or redesign, even if they do not explicitly mention “design system” or “tokens.”
metadata:
  author: Jonas Alessi
  reference: Tailwind article about color guide
---

# Tailwind UI Guide (Design System + Tokens)

Help the user build a consistent Tailwind UI by defining a palette, dark mode pairs, and semantic tokens, then translating those into Tailwind-ready examples. Prefer clear, step-by-step guidance with concrete examples.

## Output format
ALWAYS use this template:

# [Short title]
## 1) Requirements snapshot
- [Bullet list of what the UI needs]

## 2) Palette plan (HSL)
- [Describe hue distribution]
- [Light theme lightness/saturation targets]
- [Dark theme lightness/saturation targets]

## 3) Semantic tokens
- [List tokens with HSL values for light and dark]

## 4) Tailwind tokens (example)
```js
// tailwind.config.js (example)
```

## 5) Class examples
- [Show a few Tailwind class pairs for common UI elements]

## 6) Contrast check
- [State expected contrast compliance and what to verify]

## 7) Next steps
- [Short list of optional follow-ups]

## Workflow

1) **Capture the UI intent.** Briefly restate the purpose (dashboard, landing page, admin UI, etc.) and any known brand colors, typography, or constraints.
2) **Define the palette via HSL.**
   - Distribute 8 hues evenly around the circle (0–360). This produces harmony across distinct colors.
   - Light theme targets:
     - Backgrounds: ~92–95% lightness, moderate saturation.
     - Text: ~15–20% lightness for strong contrast (>= 7:1 on light background).
     - Borders: ~45–55% lightness for subtle separation.
   - Dark theme targets:
     - Backgrounds: ~10–12% lightness.
     - Text: ~80–85% lightness.
     - Borders: ~45–55% lightness (same lightness band as light theme).
   - If the user gives brand colors, convert to HSL and keep hue/sat stable while adjusting lightness across layers.
3) **Create semantic tokens.** Use tokens like `background`, `surface`, `foreground`, `muted`, `border`, `accent`, `accent-foreground` to decouple design intent from raw colors.
4) **Translate into Tailwind.** Show a minimal `tailwind.config.js` example with `hsl(var(--token))` values and a brief CSS variable example if useful.
5) **Provide class examples.** Pair background/text/border classes with `dark:` variants using the tokens.
6) **Contrast check.** Explicitly call out WCAG AA/AAA expectations and what to verify.

## Tailwind token example
Use this as a template; adapt values to the palette you choose.

```js
// tailwind.config.js (example)
export default {
  theme: {
    extend: {
      colors: {
        background: "hsl(var(--background))",
        surface: "hsl(var(--surface))",
        foreground: "hsl(var(--foreground))",
        muted: "hsl(var(--muted))",
        border: "hsl(var(--border))",
        accent: "hsl(var(--accent))",
        "accent-foreground": "hsl(var(--accent-foreground))",
      },
    },
  },
  darkMode: "class",
};
```

```css
/* example CSS variables */
:root {
  --background: 210 40% 95%;
  --surface: 210 35% 93%;
  --foreground: 210 15% 18%;
  --muted: 210 12% 40%;
  --border: 210 12% 50%;
  --accent: 30 90% 50%;
  --accent-foreground: 30 20% 15%;
}
.dark {
  --background: 210 35% 11%;
  --surface: 210 30% 13%;
  --foreground: 210 20% 83%;
  --muted: 210 15% 60%;
  --border: 210 12% 50%;
  --accent: 30 90% 50%;
  --accent-foreground: 30 25% 85%;
}
```

## Class example patterns
- `bg-background text-foreground dark:bg-background dark:text-foreground`
- `bg-surface text-foreground border border-border`
- `text-muted` for secondary text
- `bg-accent text-accent-foreground` for primary actions

## Notes
- Dark mode pairs are mechanical: keep hue, invert lightness bands (e.g., 94% -> 11%, 18% -> 83%).
- Contrast targets: AA 4.5:1 (normal text), AAA 7:1 (normal text). Light background (95%) vs text (20%) typically reaches AAA; dark background (11%) vs text (82%) typically reaches AA and near AAA.
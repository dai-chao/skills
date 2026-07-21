---
name: native-app-ui-clone
description: "Use when replicating native iOS/Android app UI from screenshots in HTML/CSS/JS. Covers scroll-driven animations, sticky headers, card folding, and exact layout physics."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [ui-replication, ios-clone, html-css-js, scroll-animations, mobile-ui]
    related_skills: [sketch, popular-web-designs]
---

# Native App UI Clone from Screenshots

Precisely replicate native mobile app UI and interactions in HTML/CSS/JS from screenshots or screen recordings. This skill governs the full workflow from screenshot analysis to pixel-perfect interactive replica.

## When to Use
- User shares a screenshot and asks to replicate an app UI
- User asks to "clone" or "make it look like" a native app
- User is curious about how a specific app's UI works
- Building HTML/CSS/JS prototypes that mimic native iOS/Android behavior
- Scroll-driven animations, sticky headers, card folding, or layout physics questions

## When NOT to Use
- Building a production web app (this is for visual replication, not architecture)
- The user wants a design system or component library (use `popular-web-designs`)
- Throwaway mockups without interaction (use `sketch`)

## Workflow

### 1. Screenshot Analysis
- Use `vision_analyze` to extract layout details from screenshots
- Note exact spacing, font sizes, colors, corner radii, shadows
- Identify scroll behavior: what sticks, what folds, what transforms
- Identify animation timing: ease curves, duration, stagger
- **User prefers working from screenshots** over verbal descriptions

### 2. Structure Decisions
- **Single-file HTML** for rapid iteration (user prefers lightweight experimentation)
- Use `-apple-system` fonts for iOS authenticity
- Use `viewport-fit=cover` for notch handling
- Use `overflow-y: scroll` with `-webkit-overflow-scrolling: touch` for native feel

### 3. Header Behavior (Critical)

**The Apple Weather App Pattern:**
- Header area starts large (city name + big temperature)
- On scroll, header content visually compacts but **container height stays fixed**
- Use `transform: scale()` + `translateY()` for visual deformation, NEVER change container height
- This prevents layout jumps and keeps cards at consistent positions
- Cards fold/scroll underneath the fixed-height header area

**Anti-patterns to avoid:**
- ❌ Changing header container height on scroll (causes layout jump)
- ❌ Using `display: none/block` or `visibility` toggles (causes reflow)
- ❌ Letting sticky header overlap content below (use fixed-height container or `padding-top`)
- ❌ Using `transform: scaleY()` on cards for folding (breaks document flow)

### 4. Card Folding Mechanics

**Correct approach:**
- Use actual `height` changes (not `transform: scaleY`) so document flow updates
- Fold order: shrink height first, then fade opacity
- Spacing between cards must remain consistent during fold
- Use `will-change: height, opacity` for performance
- Measure with `getBoundingClientRect()` for dynamic calculations

**Implementation pattern:**
```javascript
// Measure once, then animate
const fullHeight = card.getBoundingClientRect().height;
const headerHeight = card.querySelector('.card-hd').getBoundingClientRect().height;
const minHeight = headerHeight + 16; // keep title + padding

// On scroll: calculate progress based on position relative to viewport
const progress = Math.min(1, distance / (fullHeight - minHeight));
card.style.height = (fullHeight - (fullHeight - minHeight) * progress) + 'px';

// Opacity fades only after height is mostly shrunk
if (heightRatio < 0.4) {
    card.style.opacity = heightRatio / 0.4;
}
```

### 5. Scroll-Driven Animation
- Use `requestAnimationFrame` for scroll handlers (debounce via `ticking` flag)
- Calculate trigger lines based on `getBoundingClientRect()`, not `scrollTop` alone
- Account for sticky headers: use their `bottom` position as the fold trigger line

### 6. Visual Polish
- Use `backdrop-filter: blur()` for iOS frosted glass cards
- Gradient backgrounds with multiple stops for sky/weather effects
- Subtle borders (`rgba(255,255,255,0.08)`) for card definition
- Emoji for weather icons (user accepts this for prototypes)

## User Preferences (This User)

- **Extremely terse commands** — expect immediate execution without preamble
- **Prefers screenshots over verbal descriptions**
- **Cares deeply about exact animation timing** — "height shrinks first, then opacity fades, spacing stays constant"
- **Dislikes transform-based shortcuts** when real layout changes are needed
- **Prefers lightweight experimentation** — single-file HTML, quick iteration, not complex production workflows
- **Expects autonomous execution** — will say "文案你来定" (you decide the copy), trusts agent's judgment

## Common Pitfalls

1. **Layout jump on header compacting** — Root cause: changing container height. Fix: keep height fixed, use `transform: scale()` on inner content.
2. **Cards overlapping header** — Root cause: sticky header without proper spacing. Fix: use fixed-height header container or add `padding-top` to content area.
3. **Card folding breaks document flow** — Root cause: using `transform: scaleY()`. Fix: use actual `height` changes.
4. **Inconsistent spacing during fold** — Root cause: `margin-bottom` on shrinking element. Fix: spacing should be on a wrapper or use `padding` instead of `margin` for gaps.
5. **Scroll handler lag** — Root cause: running layout calculations every scroll event. Fix: use `requestAnimationFrame` + `ticking` flag.

## Reference Files
- `references/ios-weather-app-replica.md` — Full reproduction recipe from the weather app session, including exact CSS values and JavaScript patterns
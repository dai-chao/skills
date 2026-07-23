---
name: framer-motion
description: Framer Motion patterns for React UI animation — `motion` components, `AnimatePresence`, `layout` animations, `useScroll`/`useTransform`, gestures, variants, and orchestration. Use when adding entrance/exit, page transitions, scroll-linked motion, gestures, shared-layout transitions, "Framer Motion", "motion.div", "AnimatePresence", "useScroll", "אנימציה ב-React", or "Framer".
---

# Framer Motion

Declarative, React-state-driven animation. The default for "this component should animate when X happens".

## When to use Framer Motion vs GSAP

| Need | Pick |
|------|------|
| Component mounts/unmounts | **Framer** (`AnimatePresence`) |
| State change drives motion | **Framer** (`animate` prop) |
| Drag, hover, tap gestures | **Framer** (`whileHover`, `drag`) |
| Shared element across routes | **Framer** (`layoutId`) |
| Long imperative timeline | **GSAP** ([gsap skill](../gsap/SKILL.md)) |
| Scroll-pinned 3D scene | **GSAP** ScrollTrigger ([threejs-scroll-cinema](../threejs-scroll-cinema/SKILL.md)) |
| Audio-synced choreography | **GSAP** |

Mixing both in one project is fine. Framer for component-scoped, GSAP for global timelines.

## Install

```bash
npm i motion
```

> Note: as of v11+ the package is `motion` (was `framer-motion`). Both still work.

```jsx
import { motion, AnimatePresence } from 'motion/react';
```

## Core API

| API | Purpose |
|-----|---------|
| `<motion.div>` | Animatable div (also `motion.span`, `motion.button`, `motion.path`, etc.) |
| `initial` / `animate` / `exit` | Animation states |
| `transition` | Duration, easing, type (tween/spring/inertia) |
| `variants` | Reusable named states |
| `whileHover` / `whileTap` / `whileFocus` / `whileInView` | Gesture-bound states |
| `<AnimatePresence>` | Animate exit when removed from tree |
| `layout` / `layoutId` | Auto-animate layout changes |
| `useScroll` | Scroll progress hook |
| `useTransform` | Map one MotionValue to another |
| `useMotionValue` / `useSpring` | Imperative motion values |
| `useInView` | IntersectionObserver hook |
| `useAnimate` | Imperative `animate(scope, ...)` for ref-based control |

## Minimal patterns

### Entrance

```jsx
<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ duration: 0.4, ease: 'easeOut' }}
>
  Hello
</motion.div>
```

### Exit (requires AnimatePresence)

```jsx
<AnimatePresence mode="wait">
  {isOpen && (
    <motion.div
      key="modal"
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
    />
  )}
</AnimatePresence>
```

### State-driven

```jsx
<motion.div animate={{ x: isOpen ? 200 : 0 }} />
```

### Hover + tap

```jsx
<motion.button
  whileHover={{ scale: 1.05 }}
  whileTap={{ scale: 0.95 }}
/>
```

### Variants (orchestrated)

```jsx
const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.1 } },
};
const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0 },
};

<motion.ul variants={container} initial="hidden" animate="show">
  {items.map((i) => <motion.li key={i.id} variants={item}>{i.label}</motion.li>)}
</motion.ul>
```

### Scroll progress

```jsx
const { scrollYProgress } = useScroll();
const opacity = useTransform(scrollYProgress, [0, 1], [1, 0]);

<motion.div style={{ opacity }} />
```

### Layout animation

```jsx
<motion.div layout>
  {/* When children re-arrange, this auto-animates */}
</motion.div>

// Shared element across routes:
<motion.div layoutId="hero-image" />
```

## Transition types

```jsx
// Tween (default)
transition={{ duration: 0.4, ease: 'easeOut' }}

// Spring
transition={{ type: 'spring', stiffness: 300, damping: 30 }}

// Mass + velocity
transition={{ type: 'spring', mass: 0.8, stiffness: 200, damping: 20 }}
```

Eases: `'linear' | 'easeIn' | 'easeOut' | 'easeInOut' | [number, number, number, number]` (cubic-bezier).

Spring is the default for most motion in modern UI. Tween is for exact-duration needs.

## Rules (non-negotiable)

1. **Respect `prefers-reduced-motion`.** Wrap with `<MotionConfig reducedMotion="user">` or check the media query.
2. **Animate transforms, not `top/left`.** `x`, `y`, `scale`, `rotate`, `opacity` are GPU-accelerated. `top`, `left`, `width`, `height` trigger layout.
3. **Layout + transform conflicts.** Don't animate `width` AND `scale` on the same element — pick one.
4. **Variants flat.** Variants don't propagate through non-motion children. Stay flat or use explicit `inherit={false}` to break.
5. **Keys on AnimatePresence children.** Without unique keys, exit animations don't fire.
6. **Don't animate inside `useEffect` if you can avoid it.** Use `animate` prop or `useAnimate` hook.

## Anti-patterns

| ✗ Wrong | ✓ Right |
|---------|---------|
| `animate={{ left: 100 }}` | `animate={{ x: 100 }}` |
| `<AnimatePresence>{items.map(i => <Item />)}</AnimatePresence>` (no key) | `<Item key={i.id}>` |
| Re-creating `variants` object every render | Define outside component or `useMemo` |
| `transition={{ duration: 5 }}` for UI feedback | Stay under 0.5s for UI (1-2s only for hero motion) |
| Mixing `initial="hidden"` string with `initial={{ opacity: 0 }}` object | Pick one style per component |

## Performance tips

- Use `layout` only on the outer container that needs it, not every child
- For long lists with `whileInView`, set `viewport={{ once: true }}` so animation runs once
- `MotionValue` reads/writes don't re-render — prefer them over React state for fast-changing values
- Avoid `layoutId` on more than ~10 elements at once — layout calculations are expensive

## Server components (Next.js App Router)

`motion` components require a Client Component:

```jsx
'use client';
import { motion } from 'motion/react';
```

Or wrap in a `'use client'` boundary. SSR works fine — initial state renders server-side.

## Output checklist

- [ ] Entrance animations under 600ms
- [ ] Exit animations wrapped in `AnimatePresence`
- [ ] All `AnimatePresence` children have unique keys
- [ ] No `top`/`left` animations — only transforms
- [ ] `prefers-reduced-motion` respected
- [ ] Variants defined outside render, or memoized
- [ ] No layout + transform animating same axis at once
- [ ] Tested in Chrome + Safari (Safari spring physics differ slightly)

## References (loaded on demand)

- [`motion` component](references/motion-component.md) — initial/animate/exit, transition, variants
- [AnimatePresence](references/animate-presence.md) — mount/unmount, mode, popLayout
- [Layout animations](references/layout-animations.md) — layout, layoutId, shared-layout
- [Scroll & gestures](references/scroll-and-gestures.md) — useScroll, useTransform, drag, hover/tap
- [Orchestration](references/orchestration.md) — staggerChildren, when, propagation, controls

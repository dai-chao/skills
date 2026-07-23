# Scroll & Gestures

## useScroll

Returns `MotionValue`s tracking scroll position.

```jsx
import { useScroll, useTransform, motion } from 'motion/react';

const { scrollY, scrollYProgress, scrollX, scrollXProgress } = useScroll();
```

| MotionValue | Range |
|-------------|-------|
| `scrollY` / `scrollX` | Pixels (0 → page height) |
| `scrollYProgress` / `scrollXProgress` | 0 → 1 across full scroll |

### Tracking a specific element

```jsx
const ref = useRef(null);
const { scrollYProgress } = useScroll({
  target: ref,
  offset: ['start end', 'end start'],
});

<section ref={ref}>
  <motion.div style={{ opacity: scrollYProgress }} />
</section>
```

`offset` defines start/end relative to viewport:
- `'start end'` → element's top hits viewport's bottom (entering)
- `'end start'` → element's bottom hits viewport's top (leaving)

Common offsets: `['start end', 'end start']` — full scroll-through-viewport progress.

### Container scroll (not page)

```jsx
const { scrollYProgress } = useScroll({ container: scrollContainerRef });
```

## useTransform

Map one MotionValue to another. Linear by default, custom interpolation supported.

```jsx
const opacity = useTransform(scrollYProgress, [0, 0.5, 1], [0, 1, 0]);
const x = useTransform(scrollYProgress, [0, 1], ['0%', '100%']);
const blur = useTransform(scrollYProgress, [0, 1], ['blur(0px)', 'blur(8px)']);
```

Multiple inputs:

```jsx
const xy = useTransform([mouseX, mouseY], ([x, y]) => `translate(${x}px, ${y}px)`);
```

Function form for complex logic:

```jsx
const scale = useTransform(scrollYProgress, (p) => 1 + Math.sin(p * Math.PI) * 0.5);
```

## useSpring (smooth a MotionValue)

```jsx
const smoothScrollY = useSpring(scrollY, { stiffness: 100, damping: 30 });
const x = useTransform(smoothScrollY, [0, 1000], [0, 200]);
```

Smooths jittery raw scroll into a damped value.

## useMotionValue

Manual MotionValue, not React state — doesn't trigger re-render.

```jsx
const x = useMotionValue(0);
useEffect(() => {
  x.set(window.scrollY);
}, []);

<motion.div style={{ x }} />
```

Read with `x.get()`. Subscribe with `x.on('change', cb)`.

## useInView

```jsx
import { useInView } from 'motion/react';

const ref = useRef(null);
const isInView = useInView(ref, { once: true, margin: '-100px' });

<motion.div
  ref={ref}
  initial={{ opacity: 0, y: 50 }}
  animate={isInView ? { opacity: 1, y: 0 } : {}}
/>
```

Or shorthand `whileInView` prop:

```jsx
<motion.div
  initial={{ opacity: 0 }}
  whileInView={{ opacity: 1 }}
  viewport={{ once: true, margin: '-100px' }}
/>
```

## Drag

```jsx
<motion.div
  drag
  dragConstraints={{ left: -100, right: 100, top: 0, bottom: 0 }}
  dragElastic={0.2}
  dragMomentum={true}
  onDragEnd={(e, info) => console.log(info.offset)}
/>
```

| Prop | Effect |
|------|--------|
| `drag` | `true` (both axes), `'x'`, `'y'` |
| `dragConstraints` | Box or ref to a container |
| `dragElastic` | 0-1, resistance past constraints |
| `dragMomentum` | Throw inertia after release |
| `dragSnapToOrigin` | Snap back to start |

Container constraint:

```jsx
const containerRef = useRef(null);

<div ref={containerRef}>
  <motion.div drag dragConstraints={containerRef} />
</div>
```

## whileHover / whileTap / whileFocus

```jsx
<motion.button
  whileHover={{ scale: 1.05 }}
  whileTap={{ scale: 0.95 }}
  whileFocus={{ outlineColor: '#0af' }}
/>
```

These take precedence over `animate` while active. On release, animates back to `animate` state.

## Gesture event handlers

| Handler | Fires on |
|---------|----------|
| `onHoverStart` / `onHoverEnd` | Pointer enter/leave |
| `onTapStart` / `onTap` / `onTapCancel` | Pointer down/up |
| `onDragStart` / `onDrag` / `onDragEnd` | Drag lifecycle |
| `onPanStart` / `onPan` / `onPanEnd` | Pan (works on touch) |

```jsx
<motion.div onTap={(e, info) => console.log(info.point)} />
```

## Common bugs

- **`whileInView` fires on every scroll** → set `viewport={{ once: true }}`
- **Drag breaks scroll on mobile** → use `drag="x"` only, leave y to scroll
- **Spring on scroll feels sluggish** → reduce damping or stiffness
- **`useTransform` returns NaN** → input MotionValue is `undefined` initially; provide initial scroll value
- **Drag constraints don't work with ref** → ref's element must be mounted before motion child renders

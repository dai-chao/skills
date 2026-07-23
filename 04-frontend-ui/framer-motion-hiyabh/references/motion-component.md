# `motion` Component

Every HTML/SVG element has a `motion.X` variant. Animatable via props.

## Animatable values

```jsx
<motion.div animate={{
  // Transforms (GPU)
  x: 100, y: 0, z: 0,
  scale: 1.2, scaleX: 1, scaleY: 1,
  rotate: 45, rotateX: 0, rotateY: 0, rotateZ: 0,
  skew: 0, skewX: 0, skewY: 0,
  // Opacity & color
  opacity: 1,
  backgroundColor: '#ff0',
  color: '#000',
  borderColor: '#333',
  // Box
  borderRadius: 12,
  boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
  // Filter
  filter: 'blur(8px)',
  // SVG
  pathLength: 0.5,
  pathOffset: 0,
}} />
```

`x`/`y`/`z` are aliases for `translateX`/`Y`/`Z`. Prefer them.

## initial / animate / exit

```jsx
<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  exit={{ opacity: 0, y: -20 }}
/>
```

`initial={false}` skips initial — useful when value comes from server-rendered state.

## transition

Per-prop or shared:

```jsx
// Shared
<motion.div animate={{ x: 100, opacity: 1 }} transition={{ duration: 0.4 }} />

// Per-prop
<motion.div animate={{
  x: 100,
  opacity: 1,
}} transition={{
  default: { duration: 0.4 },
  x: { type: 'spring', stiffness: 300 },
  opacity: { duration: 0.6 },
}} />
```

### Tween options

```jsx
{ type: 'tween', duration: 0.4, ease: 'easeOut', delay: 0.1 }
```

Eases:
- Strings: `'linear' | 'easeIn' | 'easeOut' | 'easeInOut' | 'circIn' | 'circOut' | 'circInOut' | 'backIn' | 'backOut' | 'backInOut' | 'anticipate'`
- Cubic bezier: `[0.42, 0, 0.58, 1]`
- Custom function: `(t) => t * t`

### Spring options

```jsx
// Stiffness/damping (most common)
{ type: 'spring', stiffness: 300, damping: 30 }

// Duration-based spring
{ type: 'spring', duration: 0.5, bounce: 0.25 }

// Mass + velocity
{ type: 'spring', mass: 1, stiffness: 200, damping: 20, velocity: 0 }
```

Spring presets via `transition={{ type: 'spring' }}` use Framer's defaults. Adjust to taste.

### Inertia

For drag throw-away momentum:

```jsx
{ type: 'inertia', velocity: 50, power: 0.8, timeConstant: 700 }
```

Rare for explicit use — auto-applied to `drag`.

## variants

Named animation states. Best for orchestrating across multiple elements.

```jsx
const variants = {
  closed: { opacity: 0, y: -20 },
  open: { opacity: 1, y: 0, transition: { duration: 0.3 } },
};

<motion.div
  variants={variants}
  initial="closed"
  animate={isOpen ? 'open' : 'closed'}
/>
```

Variants can take a function:

```jsx
const variants = {
  visible: (i) => ({
    opacity: 1,
    transition: { delay: i * 0.1 },
  }),
  hidden: { opacity: 0 },
};

items.map((item, i) => (
  <motion.li
    key={item.id}
    custom={i}
    variants={variants}
    initial="hidden"
    animate="visible"
  />
));
```

## Targets vs values

- **Target shorthand:** `animate={{ x: 100 }}` — single value
- **Keyframe array:** `animate={{ x: [0, 50, 100] }}` — animates through each
- **Keyframes with timing:** `animate={{ x: [0, 50, 100] }} transition={{ times: [0, 0.5, 1] }}`
- **String → string:** `animate="open"` — looks up variant

## Common bugs

- **Animation doesn't play** → `motion` component is mounting fresh; `initial` and `animate` are the same value
- **Flicker on first render** → `initial={{ opacity: 0 }}` but page rendered with opacity 1 in CSS first
- **Transition ignored** → wrong nesting; `transition` should be a sibling of `animate`
- **Color animation jumps** → Framer can't interpolate between named colors and hex; stick to hex/rgb

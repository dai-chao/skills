# AnimatePresence

Required to animate components when they unmount. Without it, the element disappears instantly.

## Basic usage

```jsx
import { AnimatePresence, motion } from 'motion/react';

<AnimatePresence>
  {isVisible && (
    <motion.div
      key="box"
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.8 }}
    >
      Content
    </motion.div>
  )}
</AnimatePresence>
```

The conditional render is what triggers exit. Wrap any conditional `motion.X` with `AnimatePresence`.

## Keys are mandatory

```jsx
// ✗ Wrong — no key, exit won't fire when item changes
<AnimatePresence>
  <motion.div animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
    {currentItem.label}
  </motion.div>
</AnimatePresence>

// ✓ Right — unique key triggers exit/enter cycle
<AnimatePresence mode="wait">
  <motion.div
    key={currentItem.id}
    initial={{ opacity: 0 }}
    animate={{ opacity: 1 }}
    exit={{ opacity: 0 }}
  >
    {currentItem.label}
  </motion.div>
</AnimatePresence>
```

## mode

| Mode | Behavior |
|------|----------|
| `'sync'` (default) | Old + new render at same time, exit + enter overlap |
| `'wait'` | Old animates out fully, then new animates in |
| `'popLayout'` | Old removed from layout immediately (no layout shift), exit animation plays on top |

```jsx
<AnimatePresence mode="wait">
```

`popLayout` is best for animating items leaving a list — the list collapses immediately, exit happens "above" the new layout.

## Lists with AnimatePresence

```jsx
<ul>
  <AnimatePresence mode="popLayout">
    {items.map((item) => (
      <motion.li
        key={item.id}
        layout
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: 20 }}
      >
        {item.label}
      </motion.li>
    ))}
  </AnimatePresence>
</ul>
```

`layout` on each item makes the rest of the list animate to fill the gap.

## Page transitions (Next.js App Router)

```jsx
'use client';
import { AnimatePresence, motion } from 'motion/react';
import { usePathname } from 'next/navigation';

export function PageWrapper({ children }) {
  const pathname = usePathname();
  return (
    <AnimatePresence mode="wait" initial={false}>
      <motion.div
        key={pathname}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -10 }}
        transition={{ duration: 0.25 }}
      >
        {children}
      </motion.div>
    </AnimatePresence>
  );
}
```

`initial={false}` skips the first mount animation (avoids flash on page load).

## onExitComplete

Fires when all exit animations finish. Useful for cleanup:

```jsx
<AnimatePresence onExitComplete={() => console.log('all gone')}>
  {items}
</AnimatePresence>
```

## Custom prop with variants

To pass dynamic data into exit variants:

```jsx
const variants = {
  enter: (direction) => ({ x: direction > 0 ? 100 : -100, opacity: 0 }),
  center: { x: 0, opacity: 1 },
  exit: (direction) => ({ x: direction > 0 ? -100 : 100, opacity: 0 }),
};

<AnimatePresence custom={direction} mode="wait">
  <motion.div
    key={page}
    custom={direction}
    variants={variants}
    initial="enter"
    animate="center"
    exit="exit"
  />
</AnimatePresence>
```

`custom` propagates to the variants function — perfect for "next/prev slide" UIs.

## Nested AnimatePresence

Each wraps its own scope. Inner exit must complete before outer's parent unmounts (or wrap with appropriate mode).

## Common bugs

- **Exit animation doesn't fire** → no key, OR conditional is `null` instead of falsy children
- **Flash on first render** → missing `initial={false}` on `AnimatePresence`
- **Exit fires for wrong items** → keys not stable across renders (using array index instead of stable id)
- **Layout jumps when item exits** → use `mode="popLayout"`
- **AnimatePresence inside conditional that unmounts** → useless; the parent unmounting kills exit. Move `AnimatePresence` to a stable parent.

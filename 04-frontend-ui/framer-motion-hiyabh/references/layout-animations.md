# Layout Animations

Animate any layout change automatically — sort, reorder, resize, position swap. Framer measures before/after and tweens the difference (FLIP technique).

## `layout` prop

```jsx
<motion.div layout>
  {/* When this element's layout changes, animation plays */}
</motion.div>
```

Common triggers:
- Sibling added/removed
- Flex/grid layout reflow
- Width/height changed via class swap
- Element moved in DOM

## `layout="position"` vs `layout="size"`

| Value | Animates |
|-------|----------|
| `true` (default) | Position + size |
| `"position"` | Only position (faster) |
| `"size"` | Only size |

For long lists where items move (not resize), use `layout="position"` to skip size measurements.

## `layoutId` — shared element transitions

Two motion components with the same `layoutId` animate from one to the other when the first unmounts and the second mounts.

```jsx
// Card view
{!isExpanded && (
  <motion.div layoutId="card-1" onClick={() => setExpanded(true)}>
    <motion.h2 layoutId="card-1-title">Title</motion.h2>
  </motion.div>
)}

// Modal view
{isExpanded && (
  <motion.div layoutId="card-1">
    <motion.h2 layoutId="card-1-title">Title</motion.h2>
    <p>Expanded content</p>
  </motion.div>
)}
```

The card morphs into the modal smoothly. Each `layoutId` should be unique per active pair.

## With AnimatePresence

For exit-during-route-change with layoutId, wrap in `AnimatePresence`:

```jsx
<AnimatePresence>
  {isOpen && (
    <motion.div layoutId="hero" key="modal">
      ...
    </motion.div>
  )}
</AnimatePresence>
```

## Reorderable lists

```jsx
import { Reorder } from 'motion/react';

<Reorder.Group axis="y" values={items} onReorder={setItems}>
  {items.map((item) => (
    <Reorder.Item key={item.id} value={item}>
      {item.label}
    </Reorder.Item>
  ))}
</Reorder.Group>
```

`Reorder` handles drag-to-reorder + layout animations automatically.

## Layout + transform conflicts

Don't animate `width` AND `scale` on the same element with `layout`:

```jsx
// ✗ Conflict — layout measures CSS width, scale transforms after
<motion.div layout animate={{ scale: 1.2 }} className={isOpen ? 'wide' : 'narrow'} />

// ✓ Pick one approach
<motion.div layout className={isOpen ? 'wide' : 'narrow'} />
// or
<motion.div animate={{ scale: isOpen ? 1.2 : 1 }} />
```

## `layoutScroll`

If your animated container scrolls, set `layoutScroll` so Framer accounts for scroll offset:

```jsx
<motion.div layoutScroll style={{ overflow: 'auto' }}>
  <motion.div layout>...</motion.div>
</motion.div>
```

## `layoutDependency`

By default Framer measures every render. To opt out, pass a dependency:

```jsx
<motion.div layout layoutDependency={isOpen}>
```

Layout only re-measures when `isOpen` changes. Helpful for very long lists.

## Spring is the default

```jsx
<motion.div layout transition={{ type: 'spring', stiffness: 300, damping: 30 }} />
```

For instant layout changes (no animation):

```jsx
<motion.div layout transition={{ duration: 0 }} />
```

## Performance

- `layout` animations are expensive — they measure DOM
- Avoid on more than ~10 simultaneous elements
- Use `layout="position"` when size doesn't change
- Use `layoutDependency` to skip measurements
- Children of `layout` parent inherit layout animation — disable per-child with `layout={false}`

## Distortion correction

When parent `scale` changes, children stretch. Add `style={{ borderRadius: ... }}` (or text) and Framer auto-corrects:

```jsx
<motion.div layout style={{ borderRadius: 12 }}>
  <motion.h2 layout="position">Title</motion.h2>
</motion.div>
```

`layout="position"` on the child keeps text un-stretched.

## Common bugs

- **Layout animation doesn't trigger** → no actual layout change happened (only style change without measurement difference)
- **Items jump unexpectedly** → multiple `layoutId` collisions; ensure ids are unique
- **Performance bad** → too many `layout` elements; switch to `layoutDependency` or `layout="position"`
- **Text stretches** → add `layout="position"` to text elements inside scaling parents
- **Modal appears in wrong position** → `layoutId` source unmounted before destination mounted; use `AnimatePresence` to bridge

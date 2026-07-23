# Orchestration

Coordinating multiple animations through variants, controls, or sequences.

## Variant propagation

A parent's `animate="open"` propagates to children's variants if children declare `variants` with the same key.

```jsx
const parent = {
  closed: { opacity: 0 },
  open: { opacity: 1 },
};
const child = {
  closed: { x: -50 },
  open: { x: 0 },
};

<motion.div variants={parent} initial="closed" animate={isOpen ? 'open' : 'closed'}>
  <motion.div variants={child} />
  {/* No need for initial/animate here — inherited from parent */}
</motion.div>
```

This only works through `motion` components. Plain `<div>` breaks the chain.

## staggerChildren

```jsx
const parent = {
  open: {
    opacity: 1,
    transition: {
      staggerChildren: 0.08,
      delayChildren: 0.2,
      staggerDirection: 1,  // 1 = first to last, -1 = last to first
    },
  },
  closed: {
    opacity: 0,
    transition: {
      staggerChildren: 0.05,
      staggerDirection: -1,  // reverse for exit
    },
  },
};
```

Staggers `transition.delay` for each motion child variant.

## when

```jsx
transition: {
  when: 'beforeChildren',  // parent finishes, then children
  // or
  when: 'afterChildren',   // children finish, then parent
}
```

Useful for:
- `beforeChildren` — fade in container, then slide content in
- `afterChildren` — items fade out, then container slides out

## Disabling propagation

```jsx
<motion.div animate="open" inherit={false} />
```

Stops parent variant from propagating into this subtree.

## useAnimate (imperative)

For complex sequences without state-driven props:

```jsx
import { useAnimate } from 'motion/react';

const [scope, animate] = useAnimate();

async function sequence() {
  await animate('h1', { opacity: 1, y: 0 });
  await animate('p', { opacity: 1 }, { delay: 0.2 });
  animate('button', { scale: 1 }, { type: 'spring' });
}

<div ref={scope}>
  <h1 style={{ opacity: 0 }}>Title</h1>
  <p style={{ opacity: 0 }}>Subtitle</p>
  <button style={{ scale: 0 }}>Go</button>
</div>
```

`scope` scopes selectors. Animations target plain DOM elements, no `motion.X` needed.

## Animation controls (legacy)

```jsx
import { useAnimation } from 'motion/react';

const controls = useAnimation();

useEffect(() => {
  async function run() {
    await controls.start({ opacity: 1 });
    await controls.start({ x: 100 });
  }
  run();
}, []);

<motion.div animate={controls} />
```

Older API. Prefer `useAnimate` for new code.

## MotionConfig

Apply transition defaults globally:

```jsx
<MotionConfig transition={{ type: 'spring', stiffness: 200 }}>
  <App />
</MotionConfig>
```

Also for `reducedMotion`:

```jsx
<MotionConfig reducedMotion="user">
  {/* Respects system setting */}
</MotionConfig>
```

Values: `'never'` (always animate), `'always'` (never animate), `'user'` (respect setting).

## LazyMotion (bundle size optimization)

```jsx
import { LazyMotion, domAnimation, m } from 'motion/react';

<LazyMotion features={domAnimation}>
  <m.div animate={{ x: 100 }} />
</LazyMotion>
```

Use `m.X` instead of `motion.X` to opt into smaller bundle (~5KB instead of 25KB). `domMax` adds drag + layout features.

## Page-level orchestration

```jsx
const page = {
  initial: { opacity: 0 },
  animate: {
    opacity: 1,
    transition: { staggerChildren: 0.1, delayChildren: 0.2 },
  },
};

const item = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
};

<motion.section variants={page} initial="initial" animate="animate">
  <motion.h1 variants={item}>Headline</motion.h1>
  <motion.p variants={item}>Subhead</motion.p>
  <motion.button variants={item}>CTA</motion.button>
</motion.section>
```

Headline → subhead → button cascade automatically.

## Common bugs

- **Variants don't propagate** → non-motion element broke the chain (e.g., `<div><motion.div />`); wrap intermediate as `motion.div`
- **`staggerChildren` does nothing** → children don't have matching variant names
- **`when: 'beforeChildren'` ignored** → no `staggerChildren` or `delayChildren` set
- **Inherited animate fires twice** → child has its own `animate` prop overriding parent
- **Sequence with `useAnimate` runs out of order** → forgot `await` between steps

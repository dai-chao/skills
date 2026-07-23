# Design System Reference — Skill Visualizer

> Complete CSS design tokens for the Skill Visualizer output.
> Adapted from codebase-to-course with skill-visualization-specific additions.

---

## 1. Color Palette

### Background Colors
| Variable | Value | Usage |
|----------|-------|-------|
| `--color-bg` | `#FAF7F2` | Warm white, aged-paper feel |
| `--color-bg-warm` | `#F5F0E8` | Warmer shade for alternating sections |
| `--color-bg-code` | `#1E1E2E` | Deep indigo-charcoal for code blocks |
| `--color-bg-graph` | `#FEFCF8` | Slightly warmer for graph canvas area |
| `--color-text` | `#2C2A28` | Deep charcoal primary text |
| `--color-text-secondary` | `#6B6560` | Warm gray secondary text |
| `--color-text-muted` | `#9E9790` | Muted for timestamps, labels |
| `--color-border` | `#E5DFD6` | Soft warm border |
| `--color-border-light` | `#EEEBE5` | Lighter border |
| `--color-surface` | `#FFFFFF` | Card surface |
| `--color-surface-warm` | `#FDF9F3` | Warm card surface |

### File Role Colors (Node Graph & Badges)
| Variable | Value | Role | Emoji |
|----------|-------|------|-------|
| `--color-role-entry` | `#D94F30` | Entry Point (SKILL.md) | 🎯 |
| `--color-role-reference` | `#2A7B9B` | Reference files | 📚 |
| `--color-role-script` | `#2D8B55` | Executable scripts | ⚙️ |
| `--color-role-config` | `#D4A843` | Configuration | ⚡ |
| `--color-role-asset` | `#7B6DAA` | Static assets | 🎨 |
| `--color-role-hook` | `#E06B56` | Hooks / event handlers | 🔗 |

### Accent Colors
| Variable | Value | Description |
|----------|-------|-------------|
| `--color-accent` | `#2A7B9B` | Teal — represents connection/flow |
| `--color-accent-hover` | `#236A86` | Hover state |
| `--color-accent-light` | `#E4F2F7` | Light variant |
| `--color-accent-muted` | `#5BA3BD` | Muted variant |

### Semantic Colors
| Variable | Value | Usage |
|----------|-------|-------|
| `--color-success` | `#2D8B55` | Success states |
| `--color-success-light` | `#E8F5EE` | Success background |
| `--color-error` | `#C93B3B` | Error states |
| `--color-error-light` | `#FDE8E8` | Error background |
| `--color-info` | `#2A7B9B` | Info states |
| `--color-info-light` | `#E4F2F7` | Info background |

### Edge / Connection Colors
| Variable | Value | Usage |
|----------|-------|-------|
| `--color-edge-default` | `#C4BBB0` | Default dependency edge |
| `--color-edge-active` | `#2A7B9B` | Active/highlighted edge |
| `--color-edge-data` | `#D4A843` | Data flow edge |
| `--color-edge-control` | `#D94F30` | Control flow edge |

### Heatmap Gradient
```css
--heatmap-0: #FAF7F2;    /* No interaction */
--heatmap-1: #FDE8E0;    /* Low */
--heatmap-2: #F9C4B0;    /* Medium-low */
--heatmap-3: #F09070;    /* Medium */
--heatmap-4: #D94F30;    /* High */
--heatmap-5: #A83820;    /* Very high */
```

**Rules:**
- Alternate section backgrounds: even sections use `--color-bg`, odd use `--color-bg-warm`
- Node graph background uses `--color-bg-graph`
- Code blocks always use `--color-bg-code` with light text
- File role colors must be visually distinguishable from each other

---

## 2. Typography

### Font Families
```css
--font-display:  'Bricolage Grotesque', Georgia, serif;
--font-body:     'DM Sans', -apple-system, sans-serif;
--font-mono:     'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
```

### Font Size Scale (1.25 ratio)
| Variable | Value | Usage |
|----------|-------|-------|
| `--text-xs` | `0.75rem` (12px) | Labels, badges |
| `--text-sm` | `0.875rem` (14px) | Secondary text, code |
| `--text-base` | `1rem` (16px) | Body text |
| `--text-lg` | `1.125rem` (18px) | Lead paragraphs |
| `--text-xl` | `1.25rem` (20px) | Section subtitles |
| `--text-2xl` | `1.5rem` (24px) | Section headings |
| `--text-3xl` | `1.875rem` (30px) | Major headings |
| `--text-4xl` | `2.25rem` (36px) | Page title |
| `--text-5xl` | `3rem` (48px) | Hero text |

### Line Heights
| Variable | Value | Usage |
|----------|-------|-------|
| `--leading-tight` | `1.15` | Headings |
| `--leading-snug` | `1.3` | Subtitles |
| `--leading-normal` | `1.6` | Body text |
| `--leading-loose` | `1.8` | Comfortable reading |

### Google Fonts Import
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400;12..96,600;12..96,700;12..96,800&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400;1,9..40,500&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
```

### Typography Rules
- Section numbers: `--text-5xl`, font-display, weight 800, role color at 15% opacity
- Section titles: `--text-3xl` or `--text-4xl`, font-display, weight 700
- Subsection headings: `--text-xl` or `--text-2xl`, font-display, weight 600
- Body text: `--text-base` or `--text-lg`, font-body, `--leading-normal`
- Code: `--text-sm`, font-mono
- Labels/badges: `--text-xs`, font-mono, uppercase, letter-spacing 0.05em
- File names: font-mono, `--text-sm`, bold

---

## 3. Spacing & Layout

### Spacing Scale
```css
--space-1:  0.25rem;   /* 4px */
--space-2:  0.5rem;    /* 8px */
--space-3:  0.75rem;   /* 12px */
--space-4:  1rem;      /* 16px */
--space-5:  1.25rem;   /* 20px */
--space-6:  1.5rem;    /* 24px */
--space-8:  2rem;      /* 32px */
--space-10: 2.5rem;    /* 40px */
--space-12: 3rem;      /* 48px */
--space-16: 4rem;      /* 64px */
--space-20: 5rem;      /* 80px */
--space-24: 6rem;      /* 96px */
```

### Layout Variables
```css
--content-width:      900px;    /* Standard reading width */
--content-width-wide: 1100px;   /* For graph and matrix */
--nav-height:         50px;
--radius-sm:   8px;
--radius-md:   12px;
--radius-lg:   16px;
--radius-full: 9999px;
```

### Section Layout
```css
.section {
  min-height: 100dvh;
  scroll-snap-align: start;
  padding: var(--space-16) var(--space-6);
  padding-top: calc(var(--nav-height) + var(--space-12));
}
.section-content {
  max-width: var(--content-width);
  margin: 0 auto;
}
.section-content-wide {
  max-width: var(--content-width-wide);
  margin: 0 auto;
}
```

---

## 4. Shadows & Depth

```css
--shadow-sm:  0 1px 2px rgba(44, 42, 40, 0.05);
--shadow-md:  0 4px 12px rgba(44, 42, 40, 0.08);
--shadow-lg:  0 8px 24px rgba(44, 42, 40, 0.1);
--shadow-xl:  0 16px 48px rgba(44, 42, 40, 0.12);
--shadow-glow: 0 0 20px rgba(42, 123, 155, 0.15);  /* For active nodes */
```

> Use warm-tone RGBA `(44, 42, 40)` — NEVER pure-black shadows.

---

## 5. Animations & Transitions

### Easing & Duration
```css
--ease-out:    cubic-bezier(0.16, 1, 0.3, 1);
--ease-in-out: cubic-bezier(0.65, 0, 0.35, 1);
--duration-fast:   150ms;
--duration-normal: 300ms;
--duration-slow:   500ms;
--stagger-delay:   120ms;
```

### Scroll-triggered Fade-in
```css
.animate-in {
  opacity: 0;
  transform: translateY(20px);
  transition: opacity var(--duration-slow) var(--ease-out),
              transform var(--duration-slow) var(--ease-out);
}
.animate-in.visible {
  opacity: 1;
  transform: translateY(0);
}
```

### Node Pulse Animation
```css
@keyframes nodePulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.08); }
}
.node-active {
  animation: nodePulse 2s var(--ease-in-out) infinite;
}
```

### Edge Flow Animation
```css
@keyframes edgeFlow {
  from { stroke-dashoffset: 20; }
  to { stroke-dashoffset: 0; }
}
.edge-animated {
  stroke-dasharray: 10 10;
  animation: edgeFlow 1s linear infinite;
}
```

### Packet Travel Animation
```css
@keyframes packetTravel {
  0% { offset-distance: 0%; opacity: 0; }
  10% { opacity: 1; }
  90% { opacity: 1; }
  100% { offset-distance: 100%; opacity: 0; }
}
```

### Intersection Observer
```javascript
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
      observer.unobserve(entry.target);
    }
  });
}, { rootMargin: '0px 0px -10% 0px', threshold: 0.1 });
document.querySelectorAll('.animate-in').forEach(el => observer.observe(el));
```

---

## 6. Node Graph Specific Styles

### Node Appearance
```css
.graph-node {
  cursor: pointer;
  transition: transform var(--duration-fast) var(--ease-out),
              filter var(--duration-fast) var(--ease-out);
}
.graph-node:hover {
  transform: scale(1.1);
  filter: brightness(1.1);
}
.graph-node.selected {
  filter: brightness(1.15);
  /* Add glow shadow via SVG filter */
}
.graph-node.dimmed {
  opacity: 0.3;
  transition: opacity var(--duration-normal) var(--ease-out);
}
```

### Node Size Scale
| File Importance | Circle Radius | Condition |
|-----------------|---------------|-----------|
| Entry Point | 40px | Always largest |
| High (≥3 refs) | 32px | Referenced by 3+ files |
| Medium (1-2 refs) | 24px | Referenced by 1-2 files |
| Low (0 refs) | 18px | No references |

### Edge Appearance
```css
.graph-edge {
  stroke: var(--color-edge-default);
  stroke-width: 1.5;
  fill: none;
  transition: stroke var(--duration-fast),
              stroke-width var(--duration-fast);
}
.graph-edge.highlighted {
  stroke: var(--color-edge-active);
  stroke-width: 2.5;
}
.graph-edge.dimmed {
  opacity: 0.1;
}
```

---

## 7. Navigation & Progress

### HTML Structure
```html
<nav class="nav">
  <div class="progress-bar" role="progressbar" aria-valuenow="0"></div>
  <div class="nav-inner">
    <span class="nav-title">Skill Name — Visualization</span>
    <div class="nav-dots">
      <button class="nav-dot" data-target="section-1" data-tooltip="Overview"
              role="tab" aria-label="Overview"></button>
      <!-- One per section -->
    </div>
  </div>
</nav>
```

### Progress Bar
```javascript
function updateProgressBar() {
  const scrollTop = window.scrollY;
  const scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
  const progress = (scrollTop / scrollHeight) * 100;
  progressBar.style.width = progress + '%';
}
window.addEventListener('scroll', () => {
  requestAnimationFrame(updateProgressBar);
}, { passive: true });
```

### Navigation Dot States
- **Default**: `border: 2px solid var(--color-text-muted)`, hollow
- **Current**: `border-color: var(--color-accent)`, filled, subtle glow
- **Visited**: `background: var(--color-accent)`, filled

### Keyboard Navigation
```javascript
document.addEventListener('keydown', (e) => {
  if (['INPUT', 'TEXTAREA'].includes(e.target.tagName)) return;
  if (e.key === 'ArrowDown' || e.key === 'ArrowRight') { nextSection(); e.preventDefault(); }
  if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') { prevSection(); e.preventDefault(); }
});
```

---

## 8. Responsive Breakpoints

### Tablet (≤768px)
```css
@media (max-width: 768px) {
  :root {
    --text-4xl: 1.875rem;
    --text-5xl: 2.25rem;
  }
  .graph-container { height: 400px; }
  .matrix-container { overflow-x: auto; }
  .file-cards { grid-template-columns: 1fr; }
}
```

### Mobile (≤480px)
```css
@media (max-width: 480px) {
  :root {
    --text-4xl: 1.5rem;
    --text-5xl: 1.875rem;
  }
  .section { padding: var(--space-8) var(--space-4); }
  .graph-container { height: 300px; }
}
```

---

## 9. Code Block & Syntax Highlighting (Catppuccin)

```css
pre, code {
  white-space: pre-wrap;
  word-break: break-word;
  overflow-x: hidden;
}
```

| CSS Class | Color | Token |
|-----------|-------|-------|
| `.code-keyword` | `#CBA6F7` (purple) | if, else, return, function |
| `.code-string` | `#A6E3A1` (green) | "strings" |
| `.code-function` | `#89B4FA` (blue) | function names |
| `.code-comment` | `#6C7086` (muted gray) | // comments |
| `.code-number` | `#FAB387` (peach) | numbers |
| `.code-property` | `#F9E2AF` (yellow) | object keys |
| `.code-operator` | `#94E2D5` (teal) | =, =>, + |
| `.code-tag` | `#F38BA8` (pink) | HTML tags |
| `.code-attr` | `#F9E2AF` (yellow) | HTML attributes |
| `.code-value` | `#A6E3A1` (green) | attribute values |

---

## 10. Scrollbar & Background

```css
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
  background: var(--color-border);
  border-radius: var(--radius-full);
}

body {
  background: var(--color-bg);
  background-image: radial-gradient(
    ellipse at 20% 50%,
    rgba(42, 123, 155, 0.03) 0%,
    transparent 50%
  );
}

html {
  scroll-snap-type: y proximity;
  scroll-behavior: smooth;
}
```

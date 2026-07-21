---
name: creative-visual-generation
description: "Generate visual content: ASCII art/video, diagrams (Excalidraw, architecture), infographics, pixel art, 3D (p5js, Three.js), animations (Manim), HTML mockups (Sketch, Claude Design), design systems, and UI cloning."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Visual Generation, ASCII Art, Diagrams, Infographics, Pixel Art, 3D, Animation, HTML Mockups, Design Systems, UI Clone]
    related_skills: [media-content-creation, llm-inference-serving]
---

# Creative Visual Generation

## When to Use This Skill

Trigger when the user wants to:
- Create visual content (art, diagrams, animations, mockups)
- Generate ASCII art or video
- Build infographics or architecture diagrams
- Create pixel art or 3D scenes
- Design HTML mockups or clone native app UIs
- Generate animations with Manim
- Work with design systems or Google's DESIGN.md spec

## Tool Selection Guide

| Tool | Output | Best For | Complexity |
|:-----|:-------|:---------|:-----------|
| **ASCII Art** | Text/Terminal | Retro aesthetics, quick visuals | Low |
| **ASCII Video** | MP4/GIF | Animated ASCII art | Medium |
| **Excalidraw** | SVG/JSON | Hand-drawn diagrams | Low |
| **Architecture Diagram** | SVG/HTML | Cloud/infra diagrams | Low |
| **Baoyu Infographic** | PNG/SVG | Data infographics (21 layouts) | Medium |
| **Pixel Art** | PNG | Retro game sprites | Low |
| **p5js** | Canvas/WebGL | Generative art, shaders, interactive | Medium |
| **Manim** | MP4 | Math/algorithm animations | High |
| **Sketch** | HTML | Throwaway mockups (2-3 variants) | Low |
| **Claude Design** | HTML | One-off artifacts (landing, deck) | Medium |
| **Popular Web Designs** | HTML/CSS | 54 real design systems | Medium |
| **Native App UI Clone** | HTML/CSS | iOS/Android UI replication | Medium |
| **Pretext** | HTML | Browser demos with @chenglou/pretext | Medium |
| **ComfyUI** | Image/Video | AI image/video generation | High |
| **Design.md** | Token spec | Google's DESIGN.md authoring | Low |

## Section 1: ASCII Art & Video

### ASCII Art (pyfiglet, cowsay, boxes)
```bash
pip install pyfiglet
pyfiglet "Hello World"

# With cowsay
pip install cowsay
cowsay -t "Hello"
```

### ASCII Video
Convert video/audio to colored ASCII MP4/GIF.
```bash
pip install ascii-movie
ascii-movie input.mp4 --output output.mp4 --cols 120
```

See [references/ascii-art.md](references/ascii-art.md) and [references/ascii-video.md](references/ascii-video.md) for full details.

## Section 2: Diagrams & Infographics

### Excalidraw (Hand-Drawn Style)
Generate Excalidraw JSON for architecture, flow, and sequence diagrams.
```python
# Excalidraw JSON structure
{
  "type": "excalidraw",
  "version": 2,
  "elements": [...],
  "appState": {...}
}
```

### Architecture Diagrams
Dark-themed SVG architecture/cloud/infra diagrams as HTML.
```html
<!-- Dark-themed SVG diagram -->
<svg xmlns="http://www.w3.org/2000/svg" ...>
  <!-- Diagram elements -->
</svg>
```

### Baoyu Infographics
21 layouts × 21 styles for data visualization.
```python
# Generate infographic
from baoyu import Infographic
infographic = Infographic(layout="timeline", style="minimal")
```

See [references/excalidraw.md](references/excalidraw.md), [references/architecture-diagram.md](references/architecture-diagram.md), and [references/baoyu-infographic.md](references/baoyu-infographic.md) for full details.

**Note on Baoyu Infographic skill naming**: The skill is internally named `baoyu-infographic` (author: 宝玉/JimLiu). Users may refer to it as "豆包信息图" or "doubao-creative-design". The skill file is located at `skills/creative/baoyu-infographic/SKILL.md` and is bundled with Hermes by default.

## Section 3: Code-Based Visuals

### p5js
Generative art, shaders, interactive visuals, 3D.
```javascript
function setup() {
  createCanvas(400, 400);
}
function draw() {
  background(220);
  ellipse(mouseX, mouseY, 50, 50);
}
```

### Pixel Art
Convert images to retro pixel art with hardware-accurate palettes.
```bash
pip install pixel-art
pixel-art input.png --output output.png --palette nes
```

See [references/p5js.md](references/p5js.md) and [references/pixel-art.md](references/pixel-art.md) for full details.

## Section 4: Animations

### Manim (3Blue1Brown Style)
Math/algorithm animations.
```python
from manim import *

class SquareToCircle(Scene):
    def construct(self):
        circle = Circle()
        square = Square()
        self.play(Create(square))
        self.play(Transform(square, circle))
        self.play(FadeOut(circle))
```

See [references/manim-video.md](references/manim-video.md) for full details.

## Section 5: HTML Mockups & Design

### Sketch
Throwaway HTML mockups with 2-3 design variants.
```html
<!-- Quick HTML mockup -->
<div class="mockup">
  <header>...</header>
  <main>...</main>
</div>
```

### Claude Design
One-off HTML artifacts (landing pages, decks, prototypes).
```html
<!-- Full landing page -->
<!DOCTYPE html>
<html>
<head>...</head>
<body>...</body>
</html>
```

### Popular Web Designs
54 real design systems (Stripe, Linear, Vercel) as HTML/CSS.
```html
<!-- Linear-style design system -->
<link rel="stylesheet" href="design-systems/linear.css">
```

### Native App UI Clone
Replicate iOS/Android app UI from screenshots.
```html
<!-- iOS-style UI -->
<div class="ios-screen">
  <div class="status-bar">...</div>
  <div class="app-content">...</div>
</div>
```

### Pretext
Browser demos with @chenglou/pretext.
```javascript
import { createElement } from 'pretext';
```

See [references/sketch.md](references/sketch.md), [references/claude-design.md](references/claude-design.md), [references/popular-web-designs.md](references/popular-web-designs.md), [references/native-app-ui-clone.md](references/native-app-ui-clone.md), and [references/pretext.md](references/pretext.md) for full details.

## Section 6: AI Image/Video Generation

### ComfyUI
Node-based AI image and video generation.
```bash
# Install ComfyUI
git clone https://github.com/comfyanonymous/ComfyUI.git
cd ComfyUI
pip install -r requirements.txt
python main.py
```

See [references/comfyui.md](references/comfyui.md) for full details.

## Section 7: Design Specifications

### Design.md (Google Token Spec)
Author and validate Google's DESIGN.md token specification files.
```markdown
# DESIGN.md
## Color Tokens
- `--color-primary`: #1976d2
- `--color-surface`: #ffffff
```

See [references/design-md.md](references/design-md.md) for full details.

## Common Pitfalls

1. **ASCII video file size**: ASCII video can be huge; limit resolution
2. **Excalidraw JSON compatibility**: Version 2 JSON may not work in older Excalidraw
3. **p5js performance**: Use `WEBGL` mode for 3D, avoid too many particles
4. **Manim render time**: Complex scenes can take hours; use `-pql` for preview
5. **HTML mockup scope**: Keep mockups focused; full apps need proper frameworks
6. **ComfyUI VRAM**: Image generation needs significant GPU memory; use tiled VAE for large images
7. **Design.md validation**: Always run validator before submitting token specs

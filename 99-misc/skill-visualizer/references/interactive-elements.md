# Interactive Elements Reference — Skill Visualizer

> Implementation patterns for all interactive components used in the skill visualization output.
> All CSS and JS are inlined in the single HTML output file.

---

## Architecture Note

The visualization is a **single self-contained HTML file**. All styles go in `<style>` tags in `<head>`, all scripts in `<script>` tags before `</body>`. No external JS/CSS dependencies (only Google Fonts).

---

## Element 1: Interactive Node Graph (File Constellation)

The centerpiece visualization. Uses **SVG** for rendering (not Canvas) for better accessibility and CSS animation support.

### HTML Structure
```html
<div class="graph-container" id="file-graph">
  <svg class="graph-svg" viewBox="0 0 900 600">
    <!-- Edges (drawn first, behind nodes) -->
    <g class="graph-edges">
      <path class="graph-edge" 
            data-from="file-1" data-to="file-2"
            d="M100,200 Q300,100 500,200"
            marker-end="url(#arrowhead)"/>
    </g>
    
    <!-- Nodes -->
    <g class="graph-nodes">
      <g class="graph-node" data-file="skill.md" data-role="entry" 
         transform="translate(100,200)">
        <circle r="40" fill="var(--color-role-entry)"/>
        <text dy="4" text-anchor="middle" fill="white" 
              font-size="11" font-family="var(--font-mono)">SKILL.md</text>
      </g>
    </g>
    
    <!-- Arrow marker definition -->
    <defs>
      <marker id="arrowhead" markerWidth="10" markerHeight="7" 
              refX="9" refY="3.5" orient="auto">
        <polygon points="0 0, 10 3.5, 0 7" fill="var(--color-edge-default)"/>
      </marker>
      <marker id="arrowhead-active" markerWidth="10" markerHeight="7"
              refX="9" refY="3.5" orient="auto">
        <polygon points="0 0, 10 3.5, 0 7" fill="var(--color-edge-active)"/>
      </marker>
      <!-- Glow filter for selected nodes -->
      <filter id="glow">
        <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
        <feMerge>
          <feMergeNode in="coloredBlur"/>
          <feMergeNode in="SourceGraphic"/>
        </feMerge>
      </filter>
    </defs>
  </svg>
  
  <!-- Info panel (slides in from right on node click) -->
  <div class="graph-info-panel" id="graph-info" style="display:none">
    <button class="graph-info-close" onclick="closeGraphInfo()">×</button>
    <div class="graph-info-content">
      <!-- Populated dynamically -->
    </div>
  </div>
  
  <!-- Legend -->
  <div class="graph-legend">
    <div class="legend-item">
      <span class="legend-dot" style="background:var(--color-role-entry)"></span>
      <span>Entry Point</span>
    </div>
    <div class="legend-item">
      <span class="legend-dot" style="background:var(--color-role-reference)"></span>
      <span>Reference</span>
    </div>
    <div class="legend-item">
      <span class="legend-dot" style="background:var(--color-role-script)"></span>
      <span>Script</span>
    </div>
    <div class="legend-item">
      <span class="legend-dot" style="background:var(--color-role-config)"></span>
      <span>Config</span>
    </div>
    <div class="legend-item">
      <span class="legend-dot" style="background:var(--color-role-asset)"></span>
      <span>Asset</span>
    </div>
    <div class="legend-item">
      <span class="legend-dot" style="background:var(--color-role-hook)"></span>
      <span>Hook</span>
    </div>
  </div>
</div>
```

### JS Interaction Logic
```javascript
// Node click: highlight connected files, dim others
function selectNode(fileId) {
  const nodeData = fileData[fileId];
  const connected = new Set([fileId, ...nodeData.referencesTo, ...nodeData.referencedBy]);
  
  // Dim non-connected nodes
  document.querySelectorAll('.graph-node').forEach(n => {
    n.classList.toggle('dimmed', !connected.has(n.dataset.file));
    n.classList.toggle('selected', n.dataset.file === fileId);
  });
  
  // Highlight connected edges
  document.querySelectorAll('.graph-edge').forEach(e => {
    const isConnected = (e.dataset.from === fileId || e.dataset.to === fileId);
    e.classList.toggle('highlighted', isConnected);
    e.classList.toggle('dimmed', !isConnected);
    if (isConnected) {
      e.setAttribute('marker-end', 'url(#arrowhead-active)');
    } else {
      e.setAttribute('marker-end', 'url(#arrowhead)');
    }
  });
  
  // Show info panel
  showGraphInfo(fileId);
}

// Node hover: subtle highlight without full dim
function hoverNode(fileId) {
  const nodeData = fileData[fileId];
  const connected = new Set([fileId, ...nodeData.referencesTo, ...nodeData.referencedBy]);
  
  document.querySelectorAll('.graph-edge').forEach(e => {
    const isConnected = (e.dataset.from === fileId || e.dataset.to === fileId);
    if (isConnected) {
      e.classList.add('highlighted');
    }
  });
}

function unhoverNode() {
  // Only reset if no node is selected
  if (!document.querySelector('.graph-node.selected')) {
    document.querySelectorAll('.graph-edge.highlighted').forEach(e => {
      e.classList.remove('highlighted');
    });
  }
}

// Click empty space to deselect
function deselectAll() {
  document.querySelectorAll('.graph-node').forEach(n => {
    n.classList.remove('dimmed', 'selected');
  });
  document.querySelectorAll('.graph-edge').forEach(e => {
    e.classList.remove('highlighted', 'dimmed');
    e.setAttribute('marker-end', 'url(#arrowhead)');
  });
  closeGraphInfo();
}
```

### Graph Info Panel
```html
<div class="graph-info-content">
  <div class="info-header">
    <span class="role-badge" style="background: var(--color-role-entry)">ENTRY POINT</span>
    <h3 class="info-filename">SKILL.md</h3>
  </div>
  <p class="info-summary">The main instruction file that defines...</p>
  <div class="info-stats">
    <span class="info-stat">📄 245 lines</span>
    <span class="info-stat">📤 References 3 files</span>
    <span class="info-stat">📥 Referenced by 0 files</span>
  </div>
  <div class="info-connections">
    <h4>Connections</h4>
    <div class="connection-out">→ references/design-system.md</div>
    <div class="connection-out">→ references/interactive-elements.md</div>
  </div>
</div>
```

### CSS Key Points
- Graph container has fixed aspect ratio, responsive via `viewBox`
- Info panel slides in from right with `transform: translateX(100%)` → `translateX(0)`
- Legend positioned at bottom-left of graph container
- On mobile, info panel becomes a bottom sheet

---

## Element 2: Execution Flow Timeline

Step-by-step animated visualization of how the skill executes.

### HTML Structure
```html
<div class="flow-timeline" id="exec-flow">
  <div class="flow-track">
    <!-- Phase nodes on the track -->
    <div class="flow-phase" data-phase="1" data-files='["SKILL.md"]'>
      <div class="flow-phase-dot">
        <span class="flow-phase-num">1</span>
      </div>
      <div class="flow-phase-content">
        <h4 class="flow-phase-title">Trigger</h4>
        <p class="flow-phase-desc">User says "visualize this skill"</p>
        <div class="flow-phase-files">
          <span class="flow-file-tag" style="border-color: var(--color-role-entry)">
            SKILL.md
          </span>
        </div>
      </div>
    </div>
    
    <!-- Animated connection line between phases -->
    <div class="flow-connector">
      <div class="flow-connector-line"></div>
      <div class="flow-connector-packet"></div>
    </div>
    
    <div class="flow-phase" data-phase="2" data-files='["SKILL.md"]'>
      <div class="flow-phase-dot">
        <span class="flow-phase-num">2</span>
      </div>
      <div class="flow-phase-content">
        <h4 class="flow-phase-title">Analysis</h4>
        <p class="flow-phase-desc">Read and classify all skill files</p>
        <div class="flow-phase-files">
          <!-- File tags populated dynamically -->
        </div>
      </div>
    </div>
    
    <!-- More phases... -->
  </div>
  
  <div class="flow-controls">
    <button class="btn flow-prev-btn" onclick="prevPhase()" disabled>← Previous</button>
    <button class="btn flow-next-btn" onclick="nextPhase()">Next Step →</button>
    <button class="btn flow-play-btn" onclick="playAllPhases()">▶ Play All</button>
    <button class="btn flow-reset-btn" onclick="resetFlow()">↺ Reset</button>
    <span class="flow-progress-text">Step 0 / N</span>
  </div>
</div>
```

### JS Logic
```javascript
let currentPhase = 0;
const phases = document.querySelectorAll('.flow-phase');
const connectors = document.querySelectorAll('.flow-connector');

function showPhase(index) {
  phases.forEach((p, i) => {
    p.classList.toggle('active', i <= index);
    p.classList.toggle('current', i === index);
  });
  connectors.forEach((c, i) => {
    c.classList.toggle('active', i < index);
  });
  
  // Scroll phase into view
  phases[index]?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  
  // Update controls
  document.querySelector('.flow-prev-btn').disabled = index <= 0;
  document.querySelector('.flow-next-btn').disabled = index >= phases.length - 1;
  document.querySelector('.flow-progress-text').textContent = 
    `Step ${index + 1} / ${phases.length}`;
}

function nextPhase() {
  if (currentPhase < phases.length - 1) {
    currentPhase++;
    showPhase(currentPhase);
  }
}

function prevPhase() {
  if (currentPhase > 0) {
    currentPhase--;
    showPhase(currentPhase);
  }
}

async function playAllPhases() {
  resetFlow();
  for (let i = 0; i < phases.length; i++) {
    currentPhase = i;
    showPhase(i);
    await new Promise(r => setTimeout(r, 1200));
  }
}

function resetFlow() {
  currentPhase = 0;
  showPhase(0);
}
```

### CSS Key Points
- Vertical timeline with line on the left, content on the right
- Phase dots pulse when active (`animation: nodePulse`)
- Connector packets animate along the line when transitioning
- Inactive phases are muted (opacity 0.4)
- Current phase has accent border and subtle glow
- On mobile, timeline takes full width

---

## Element 3: Collapsible File Cards

Expandable cards showing file details.

### HTML Structure
```html
<div class="file-cards">
  <div class="file-card animate-in" data-file="SKILL.md">
    <div class="file-card-header" onclick="toggleFileCard(this)">
      <div class="file-card-left">
        <span class="role-badge" style="background: var(--color-role-entry)">🎯 ENTRY</span>
        <span class="file-card-name">SKILL.md</span>
      </div>
      <div class="file-card-right">
        <span class="file-card-stat">245 lines</span>
        <span class="file-card-chevron">▾</span>
      </div>
    </div>
    
    <div class="file-card-body" style="display:none">
      <div class="file-card-summary">
        <h4>What it does</h4>
        <p>The main instruction file that defines the skill's behavior, 
           trigger keywords, and 4-phase execution flow.</p>
      </div>
      
      <div class="file-card-connections">
        <h4>Connections</h4>
        <div class="connection-list">
          <div class="connection-item outgoing">
            <span class="connection-arrow">→</span>
            <span class="connection-label">References</span>
            <span class="connection-target" onclick="scrollToFile('design-system')">
              references/design-system.md
            </span>
          </div>
        </div>
      </div>
      
      <div class="file-card-snippets">
        <h4>Key Sections</h4>
        <div class="snippet-block">
          <div class="snippet-label">Trigger Keywords</div>
          <pre class="snippet-code"><code>
<span class="code-comment">## Trigger Keywords</span>
<span class="code-string">"visualize this skill"</span>
<span class="code-string">"analyze this skill"</span>
<span class="code-string">"show me how this skill works"</span>
          </code></pre>
          <p class="snippet-explanation">
            These are the phrases that activate this skill when 
            a user types them.
          </p>
        </div>
      </div>
      
      <div class="file-card-patterns">
        <h4>Patterns Used</h4>
        <div class="pattern-tags">
          <span class="pattern-tag">Phased Execution</span>
          <span class="pattern-tag">Reference Delegation</span>
          <span class="pattern-tag">Progressive Disclosure</span>
        </div>
      </div>
    </div>
  </div>
</div>
```

### JS Logic
```javascript
function toggleFileCard(header) {
  const body = header.nextElementSibling;
  const chevron = header.querySelector('.file-card-chevron');
  const isOpen = body.style.display !== 'none';
  
  if (isOpen) {
    body.style.maxHeight = body.scrollHeight + 'px';
    requestAnimationFrame(() => {
      body.style.maxHeight = '0';
      body.style.opacity = '0';
    });
    setTimeout(() => { body.style.display = 'none'; }, 300);
    chevron.textContent = '▾';
  } else {
    body.style.display = 'block';
    body.style.maxHeight = '0';
    body.style.opacity = '0';
    requestAnimationFrame(() => {
      body.style.maxHeight = body.scrollHeight + 'px';
      body.style.opacity = '1';
    });
    setTimeout(() => { body.style.maxHeight = 'none'; }, 300);
    chevron.textContent = '▴';
  }
}
```

### CSS Key Points
- Cards have `border-radius: var(--radius-md)`, warm shadow
- Header has hover effect (darken background)
- Body uses `max-height` + `opacity` transition for smooth expand
- Role badge uses file role color with white text
- Code snippets use `--color-bg-code` background with Catppuccin colors
- Snippet explanation in warm italic text below code

---

## Element 4: Interaction Matrix / Heatmap

Visual matrix showing file-to-file interaction strength.

### HTML Structure
```html
<div class="matrix-container">
  <div class="matrix-wrapper">
    <table class="matrix-table" id="interaction-matrix">
      <thead>
        <tr>
          <th class="matrix-corner"></th>
          <th class="matrix-col-header" data-file="SKILL.md">
            <span class="matrix-label">SKILL.md</span>
          </th>
          <th class="matrix-col-header" data-file="design-system.md">
            <span class="matrix-label">design-system.md</span>
          </th>
          <!-- More columns... -->
        </tr>
      </thead>
      <tbody>
        <tr>
          <td class="matrix-row-header" data-file="SKILL.md">
            <span class="matrix-label">SKILL.md</span>
          </td>
          <td class="matrix-cell" data-from="SKILL.md" data-to="SKILL.md" 
              data-strength="0" onclick="showMatrixDetail(this)"
              style="background: var(--heatmap-0)">
          </td>
          <td class="matrix-cell" data-from="SKILL.md" data-to="design-system.md"
              data-strength="4" onclick="showMatrixDetail(this)"
              style="background: var(--heatmap-4)">
            <span class="matrix-value">4</span>
          </td>
          <!-- More cells... -->
        </tr>
      </tbody>
    </table>
  </div>
  
  <!-- Detail popup -->
  <div class="matrix-detail" id="matrix-detail" style="display:none">
    <button class="matrix-detail-close" onclick="closeMatrixDetail()">×</button>
    <h4 class="matrix-detail-title">SKILL.md → design-system.md</h4>
    <div class="matrix-detail-body">
      <p><strong>Interaction type:</strong> Reference (read on demand)</p>
      <p><strong>Strength:</strong> 4 — heavily referenced during Phase 3</p>
      <ul class="matrix-detail-list">
        <li>SKILL.md instructs to read design-system.md before building</li>
        <li>Color tokens are applied in the output HTML</li>
        <li>Typography rules guide all text rendering</li>
        <li>Animation patterns used for interactive elements</li>
      </ul>
    </div>
  </div>
  
  <!-- Heatmap legend -->
  <div class="matrix-legend">
    <span class="matrix-legend-label">Interaction Strength:</span>
    <div class="matrix-legend-gradient">
      <span class="ml-item" style="background: var(--heatmap-0)">None</span>
      <span class="ml-item" style="background: var(--heatmap-1)">Low</span>
      <span class="ml-item" style="background: var(--heatmap-2)"></span>
      <span class="ml-item" style="background: var(--heatmap-3)">Med</span>
      <span class="ml-item" style="background: var(--heatmap-4)"></span>
      <span class="ml-item" style="background: var(--heatmap-5)">High</span>
    </div>
  </div>
</div>
```

### JS Logic
```javascript
function showMatrixDetail(cell) {
  const from = cell.dataset.from;
  const to = cell.dataset.to;
  const detail = interactionData[from + '->' + to];
  
  if (!detail || cell.dataset.strength === '0') return;
  
  const panel = document.getElementById('matrix-detail');
  panel.querySelector('.matrix-detail-title').textContent = `${from} → ${to}`;
  panel.querySelector('.matrix-detail-body').innerHTML = detail.html;
  panel.style.display = 'block';
  
  // Highlight row and column
  document.querySelectorAll('.matrix-cell').forEach(c => c.classList.remove('highlighted'));
  document.querySelectorAll(`.matrix-cell[data-from="${from}"]`).forEach(c => 
    c.classList.add('row-highlight'));
  document.querySelectorAll(`.matrix-cell[data-to="${to}"]`).forEach(c => 
    c.classList.add('col-highlight'));
  cell.classList.add('highlighted');
}

function closeMatrixDetail() {
  document.getElementById('matrix-detail').style.display = 'none';
  document.querySelectorAll('.matrix-cell').forEach(c => 
    c.classList.remove('highlighted', 'row-highlight', 'col-highlight'));
}
```

### CSS Key Points
- Column headers rotated 45° for space efficiency
- Cells have hover effect (border highlight)
- Row/column headers use `font-mono` for file names
- On mobile, matrix scrolls horizontally with sticky row headers
- Detail panel appears as a floating card near the clicked cell
- Highlighted row/col get subtle background tint

---

## Element 5: Glossary Tooltips

Technical terms get hover/click tooltips with plain-language definitions.

### HTML Usage
```html
<p>The skill uses 
  <span class="term" data-definition="A prompt is a text instruction given to an AI model that tells it what to do. Think of it as writing a very detailed job brief for an extremely capable but literal-minded assistant.">prompt engineering</span>
  to guide the analysis.
</p>
```

### JS Logic
```javascript
// Create tooltip element once, reuse
const tooltip = document.createElement('div');
tooltip.className = 'tooltip';
tooltip.style.display = 'none';
document.body.appendChild(tooltip);

document.querySelectorAll('.term').forEach(term => {
  // Desktop: hover
  term.addEventListener('mouseenter', (e) => showTooltip(e.target));
  term.addEventListener('mouseleave', () => hideTooltip());
  // Mobile: click
  term.addEventListener('click', (e) => {
    e.stopPropagation();
    if (tooltip.style.display === 'block' && tooltip._currentTerm === e.target) {
      hideTooltip();
    } else {
      showTooltip(e.target);
    }
  });
});

function showTooltip(term) {
  tooltip.textContent = term.dataset.definition;
  tooltip.style.display = 'block';
  tooltip._currentTerm = term;
  
  const rect = term.getBoundingClientRect();
  const tipRect = tooltip.getBoundingClientRect();
  
  let top = rect.top - tipRect.height - 8;
  let left = rect.left + (rect.width / 2) - (tipRect.width / 2);
  
  // Flip below if not enough space above
  if (top < 8) top = rect.bottom + 8;
  // Keep within viewport
  left = Math.max(8, Math.min(left, window.innerWidth - tipRect.width - 8));
  
  tooltip.style.position = 'fixed';
  tooltip.style.top = top + 'px';
  tooltip.style.left = left + 'px';
  tooltip.style.zIndex = '10000';
}

function hideTooltip() {
  tooltip.style.display = 'none';
  tooltip._currentTerm = null;
}

document.addEventListener('click', () => hideTooltip());
```

### CSS Key Points
- `.term`: dashed underline (`border-bottom: 1.5px dashed var(--color-accent)`), `cursor: pointer`
- `.tooltip`: `position: fixed`, `z-index: 10000`, `background: var(--color-bg-code)`, white text
- Max-width 300px, padding `--space-3 --space-4`
- `border-radius: var(--radius-sm)`
- Subtle warm shadow `var(--shadow-md)`
- Appear animation: `opacity 0→1` + `translateY(4px→0)` in 150ms

---

## Element 6: Callout / Insight Boxes

Highlight key architectural insights about the skill.

### HTML Structure
```html
<!-- Architectural insight -->
<div class="callout callout-accent">
  <div class="callout-icon">🔍</div>
  <div class="callout-content">
    <strong class="callout-title">Architecture Insight</strong>
    <p>This skill uses a "hub and spoke" pattern — SKILL.md is the hub that 
    dispatches to specialized reference files on demand, keeping the main 
    instruction file focused and readable.</p>
  </div>
</div>

<!-- Tip for customization -->
<div class="callout callout-info">
  <div class="callout-icon">💡</div>
  <div class="callout-content">
    <strong class="callout-title">Customization Tip</strong>
    <p>To change the visual style of the output, you only need to modify 
    design-system.md — the SKILL.md doesn't need to change at all.</p>
  </div>
</div>

<!-- Warning about common mistake -->
<div class="callout callout-warning">
  <div class="callout-icon">⚠️</div>
  <div class="callout-content">
    <strong class="callout-title">Common Pitfall</strong>
    <p>If you modify the reference files without updating SKILL.md's 
    "Reference Files" table, the AI may not know to read them.</p>
  </div>
</div>
```

### Three Variants
| Class | Style | Usage |
|-------|-------|-------|
| `callout-accent` | Teal left border, light accent bg | Architectural insights |
| `callout-info` | Blue left border, light info bg | Tips & customization |
| `callout-warning` | Red left border, light error bg | Warnings & pitfalls |

### CSS
```css
.callout {
  display: flex;
  gap: var(--space-4);
  padding: var(--space-5) var(--space-6);
  border-radius: var(--radius-md);
  border-left: 4px solid;
  margin: var(--space-6) 0;
}
.callout-accent {
  border-color: var(--color-accent);
  background: var(--color-accent-light);
}
.callout-info {
  border-color: var(--color-info);
  background: var(--color-info-light);
}
.callout-warning {
  border-color: var(--color-error);
  background: var(--color-error-light);
}
.callout-icon { font-size: 1.5rem; flex-shrink: 0; }
.callout-title { font-family: var(--font-display); font-weight: 600; }
```

---

## Element 7: Stats Dashboard Cards

Overview statistics about the skill.

### HTML Structure
```html
<div class="stats-grid">
  <div class="stat-card animate-in">
    <div class="stat-icon">📄</div>
    <div class="stat-value">5</div>
    <div class="stat-label">Files</div>
  </div>
  <div class="stat-card animate-in">
    <div class="stat-icon">📏</div>
    <div class="stat-value">1,247</div>
    <div class="stat-label">Total Lines</div>
  </div>
  <div class="stat-card animate-in">
    <div class="stat-icon">🔗</div>
    <div class="stat-value">8</div>
    <div class="stat-label">Connections</div>
  </div>
  <div class="stat-card animate-in">
    <div class="stat-icon">📊</div>
    <div class="stat-value">Medium</div>
    <div class="stat-label">Complexity</div>
  </div>
</div>
```

### CSS
```css
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: var(--space-4);
  margin: var(--space-8) 0;
}
.stat-card {
  background: var(--color-surface);
  border-radius: var(--radius-md);
  padding: var(--space-6);
  text-align: center;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--color-border-light);
  transition: transform var(--duration-fast) var(--ease-out),
              box-shadow var(--duration-fast) var(--ease-out);
}
.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}
.stat-icon { font-size: 2rem; margin-bottom: var(--space-2); }
.stat-value { 
  font-family: var(--font-display); 
  font-size: var(--text-3xl); 
  font-weight: 700;
  color: var(--color-accent);
}
.stat-label {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-secondary);
  margin-top: var(--space-1);
}
```

---

## Element 8: Visual File Tree

Show the skill's file structure.

### HTML Structure
```html
<div class="file-tree animate-in">
  <div class="ft-folder open">
    <span class="ft-toggle" onclick="toggleFolder(this)">▾</span>
    <span class="ft-name">skill-name/</span>
    <span class="ft-desc">Root skill directory</span>
    <div class="ft-children">
      <div class="ft-file" data-role="entry">
        <span class="ft-icon">🎯</span>
        <span class="ft-name">SKILL.md</span>
        <span class="ft-desc">Main instruction file — the brain of the skill</span>
        <span class="ft-size">245 lines</span>
      </div>
      <div class="ft-folder open">
        <span class="ft-toggle" onclick="toggleFolder(this)">▾</span>
        <span class="ft-name">references/</span>
        <span class="ft-desc">Supporting knowledge files</span>
        <div class="ft-children">
          <div class="ft-file" data-role="reference">
            <span class="ft-icon">📚</span>
            <span class="ft-name">design-system.md</span>
            <span class="ft-desc">Visual design specifications</span>
            <span class="ft-size">180 lines</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
```

### JS
```javascript
function toggleFolder(toggle) {
  const folder = toggle.parentElement;
  const children = folder.querySelector('.ft-children');
  const isOpen = folder.classList.contains('open');
  
  if (isOpen) {
    children.style.maxHeight = children.scrollHeight + 'px';
    requestAnimationFrame(() => { children.style.maxHeight = '0'; });
    folder.classList.remove('open');
    toggle.textContent = '▸';
  } else {
    folder.classList.add('open');
    toggle.textContent = '▾';
    children.style.maxHeight = children.scrollHeight + 'px';
    setTimeout(() => { children.style.maxHeight = 'none'; }, 300);
  }
}
```

### CSS Key Points
- Font-mono for all file names
- File role colors via `data-role` attribute
- Folder names bold and accent-colored
- Indentation: `padding-left: var(--space-6)` per level
- File descriptions in secondary text, smaller size
- Hover: subtle background highlight

---

## Element 9: Data Flow Diagram

Shows data/information flow between files with animated packets.

### HTML Structure
```html
<div class="data-flow" id="data-flow">
  <div class="df-actors">
    <div class="df-actor" id="df-user" style="border-color: var(--color-role-entry)">
      <div class="df-actor-icon">👤</div>
      <span>User Input</span>
    </div>
    <div class="df-connector">
      <svg class="df-line"><line x1="0" y1="50%" x2="100%" y2="50%"/></svg>
    </div>
    <div class="df-actor" id="df-skill" style="border-color: var(--color-role-entry)">
      <div class="df-actor-icon">🎯</div>
      <span>SKILL.md</span>
    </div>
    <div class="df-connector">
      <svg class="df-line"><line x1="0" y1="50%" x2="100%" y2="50%"/></svg>
    </div>
    <div class="df-actor" id="df-ref" style="border-color: var(--color-role-reference)">
      <div class="df-actor-icon">📚</div>
      <span>References</span>
    </div>
    <div class="df-connector">
      <svg class="df-line"><line x1="0" y1="50%" x2="100%" y2="50%"/></svg>
    </div>
    <div class="df-actor" id="df-output" style="border-color: var(--color-role-asset)">
      <div class="df-actor-icon">📄</div>
      <span>Output HTML</span>
    </div>
  </div>
  
  <div class="df-step-label" id="df-label">Click "Next" to trace the data flow</div>
  
  <div class="df-controls">
    <button class="btn df-next-btn" onclick="nextDataFlowStep()">Next →</button>
    <button class="btn df-reset-btn" onclick="resetDataFlow()">Reset</button>
    <span class="df-progress"></span>
  </div>
</div>
```

### CSS Key Points
- Horizontal layout on desktop, vertical on mobile
- Actors are rounded-corner cards with role-colored top border
- Connector lines are thin SVGs with animated dash pattern
- Active actor gets `box-shadow: var(--shadow-glow)` and `scale(1.05)`
- Step label appears below the diagram, updates with each step

---

## Summary: All Interactive Elements

| # | Element | Purpose | User Interaction |
|---|---------|---------|-----------------|
| 1 | **Node Graph** | File relationships | Click/hover nodes |
| 2 | **Flow Timeline** | Execution phases | Step-by-step controls |
| 3 | **File Cards** | File deep dives | Expand/collapse |
| 4 | **Heatmap Matrix** | Interaction strength | Click cells |
| 5 | **Glossary Tooltips** | Technical terms | Hover/click |
| 6 | **Callout Boxes** | Key insights | Static (≤2 per section) |
| 7 | **Stats Dashboard** | Overview metrics | Hover animation |
| 8 | **File Tree** | Directory structure | Toggle folders |
| 9 | **Data Flow** | Information flow | Step-by-step controls |

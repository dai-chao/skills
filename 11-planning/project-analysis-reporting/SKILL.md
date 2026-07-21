---
name: project-analysis-reporting
description: Analyze a codebase/project directory and produce structured deliverables — technical analysis, business reports, project books, and product showcase materials. Covers code review, architecture analysis, business planning, and presentation-ready artifacts.
version: 1.0.0
author: Hermes Agent
metadata:
  hermes:
    tags: [project-analysis, code-review, business-planning, reporting, presentation]
    related_skills: [writing-plans, aliyun-dashscope-video-pipeline, xhs-ai-short-drama-operator]
---

# Project Analysis & Reporting

## Overview

When a user asks you to "analyze this project" or "review this codebase" or "write a project book/report", produce structured, multi-layered deliverables that serve both technical and business audiences. This skill covers:

1. **Technical Analysis** — architecture, code quality, dependencies, risks
2. **Business Reporting** — project books, pitch decks, operational plans
3. **Product Showcase** — visual cards, HTML presentations, demo materials

## Trigger Conditions

Load this skill when the user says any of:
- "分析这个项目" / "Analyze this project"
- "Review this codebase" / "Code review"
- "写项目书" / "项目计划书" / "business plan"
- "产品展示" / "demo" / "showcase"
- "给领导汇报" / "presentation" / "pitch"
- Any combination of project analysis + deliverable creation

## Workflow

### Phase 1: Discovery (Always Do First)

Before writing anything, understand the project thoroughly:

```
Step 1: Directory tree
  → mcp_filesystem_directory_tree or search_files(target='files')

Step 2: Read core config files
  → package.json, app.json, README, config files
  → Understand tech stack, entry points, dependencies

Step 3: Read key source files
  → Entry points (app.js, main.py, index.ts)
  → Core business logic (the "engine" files)
  → 3-5 most important utility modules

Step 4: Identify architecture patterns
  → Data flow, API integrations, state management
  → Security model, deployment strategy
```

**Rule of thumb:** Read at least 10-15 files before forming conclusions. Surface-level analysis is worse than no analysis.

### Phase 2: Technical Analysis

Structure the analysis in layers:

```
Layer 1: Project Overview (1 paragraph)
  → What is it, who is it for, core value prop

Layer 2: Architecture (table + diagram description)
  → Tech stack, data flow, external dependencies
  → Key modules and their responsibilities

Layer 3: Code Quality Assessment (strengths + concerns)
  → What's done well (security, error handling, patterns)
  → What's risky (hardcoded values, missing validation, tech debt)

Layer 4: Data Flow Deep Dive
  → Trace a complete user journey through the code
  → Identify bottlenecks, failure points, retry logic

Layer 5: Recommendations (prioritized)
  → Short-term (1-2 weeks): quick wins, critical fixes
  → Medium-term (1-3 months): features, refactoring
  → Long-term (3-12 months): scale, platform, monetization
```

### Phase 3: Business Reporting (When Requested)

If the user asks for "项目书" or "business plan" or "怎么运营/收益":

```
Section 1: Project Overview
  → Positioning, target users, core value

Section 2: Product Features
  → Current capabilities, UX highlights, competitive differentiation

Section 3: Technical Architecture
  → Stack, integrations, security, scalability

Section 4: Market & Competition
  → Competitive landscape, differentiation, market opportunity

Section 5: Operations Strategy
  → Cold start, growth, community, content

Section 6: Business Model
  → Revenue streams, pricing, cost structure, unit economics

Section 7: Roadmap
  → Short/medium/long-term milestones

Section 8: Risk & Mitigation
  → Technical, market, regulatory risks

Section 9: Team & Resources
  → Roles needed, current assets
```

### Phase 4: Product Showcase (When Requested)

If the user asks for visual demos or "产品展示":

**HTML Card Gallery Pattern:**
```html
<!DOCTYPE html>
<html>
<head>
  <style>
    /* Responsive grid: auto-fill minmax(300px, 1fr) */
    /* Cards: white bg, rounded corners, subtle shadow */
    /* Image area: aspect-ratio 3/4, placeholder or actual image */
    /* Tag: absolute positioned top-left, dark pill */
    /* Prompt area: monospace font, scrollable, light bg */
    /* Meta: flex row, small text, border-top separator */
  </style>
</head>
<body>
  <header>
    <h1>Project Name · Showcase</h1>
    <p>One-line description</p>
  </header>
  
  <section>
    <h2>Category Name</h2>
    <div class="cards-grid">
      <!-- Card template -->
      <div class="card">
        <div class="card-image">
          <span class="card-tag">Tag</span>
          <img src="..." alt="..."> <!-- or placeholder -->
        </div>
        <div class="card-body">
          <div class="card-label">Prompt</div>
          <div class="card-prompt">The full prompt text...</div>
          <div class="card-meta">
            <span><strong>Key:</strong> Value</span>
            <span><strong>Key:</strong> Value</span>
          </div>
        </div>
      </div>
    </div>
  </section>
</body>
</html>
```

**Key design decisions for showcase cards:**
- Use `aspect-ratio` for consistent image sizing
- Prompt text uses monospace font in a scrollable container
- Tags are dark pills positioned absolute over image
- Meta info is a flex row with `border-top` separator
- Responsive: single column on mobile, 2-3 columns on desktop
- Hover: subtle lift (`translateY(-4px)`) + shadow increase

## Output Format Rules

### For Technical Analysis (Terminal/Chat)

- Use plain text tables (not markdown code blocks for tables)
- Use `---` horizontal rules to separate sections
- Bold key terms with `**term**`
- Keep paragraphs short (2-3 sentences max)
- Numbered lists for sequential steps
- Bullet lists for non-sequential items

### For Business Reports (Markdown Files)

- Save to a `.md` file in the project directory or `~/Desktop/`
- Use proper markdown headers (`#`, `##`, `###`)
- Include tables for structured data
- Add a summary/TL;DR at the top
- End with actionable next steps

### For Product Showcases (HTML Files)

- Save to `.html` file, self-contained (no external dependencies)
- Use CSS Grid for card layout
- Include placeholder instructions for image replacement
- Make it copy-paste ready for the user to fill in images
- Add responsive breakpoints for mobile

### For Complete Project Books (HTML + Business + Showcase)

When the user asks for a "complete project book" or "项目书" that combines business reporting with product showcase:

**Use the HTML template at `references/html-project-book-template.html`** — it contains:
- 10-chapter business report structure (overview, features, tech, operations, revenue, competition, roadmap, team, risks)
- Product showcase card gallery with image-on-top / story-below layout
- Sticky navigation with section anchors
- PDF export button using html2pdf.js (blob download method, not `.save()`)
- Scroll-triggered entrance animations (IntersectionObserver, CSS transitions)
- Print media queries that disable animations for clean PDF output
- Responsive design for mobile/desktop

**Key design decisions from this session:**
- Card image area: `width: 100%; height: auto; object-fit: contain` to preserve aspect ratio
- Story text only (not full prompt) in card body — user-facing Chinese narrative
- Tags as absolute-positioned dark pills over image
- Meta info as flex row with `border-top` separator
- Animation: fadeInUp for hero, slideInLeft for section titles, staggered fadeIn for cards/tables
- PDF export: use `.toPdf().get('pdf')` then `pdf.output('blob')` + manual download link, because `.save()` fails in headless/blocked environments

**Layout & Spacing Rules (from user feedback):**
- Default to spacious, breathable layouts. User explicitly dislikes compact/tight spacing ("太紧凑了")
- Use generous whitespace: section margins 32px+, card gaps 20px+, grid gaps 60px for two-column layouts
- Two-column sections (overview, product, tech, operations, revenue, plan) should use `gap: 60px` and `margin: 32px 0`
- Card internal padding: 24px minimum
- Print media query: two-column layouts should collapse to single column (`grid-template-columns: 1fr`) for clean PDF output

**HTML Container Structure Rule (critical):**
- All page content MUST be wrapped in a single `<div class="container">` with `max-width: 1200px; margin: 0 auto`
- Never remove the container wrapper when editing — it constrains content width
- Hero/title section can be inside or outside container depending on design preference, but all chapter content must be inside
- When removing elements (like buttons, scripts), verify the container open/close tags remain intact

**Feature Card Enhancement Pattern (for info-card grids):**
When displaying feature highlights or value propositions in a card grid, use this pattern for visual richness:
- Add a large emoji icon at the top of each card (32px) for visual anchoring
- Use `display: flex; flex-direction: column; gap: 32px` for the card container (not grid with single column)
- Card padding: 32px; border-radius: 16px; subtle border + enhanced shadow
- Hover effect: `translateY(-4px)` + deeper shadow for interactivity
- Title: 18px, font-weight 700, color #1a1a1a, margin-bottom 12px
- Body: 15px, line-height 1.9, color #555, margin-bottom 0
- Never use default `.info-card` styling for feature cards — always override with specific `.highlight-cards .info-card` selectors

**Business Plan Sections for Investor-Ready Documents:**
When the user asks "这是不是商业计划书" or wants to make the document investor-ready, ensure these sections exist:
- **Team** — Founder background, key hires needed, current status (solo/part-time/full-time)
- **Funding Ask** — Round, amount, equity offered, valuation, use of funds breakdown
- **Milestones** — 6/12/18 month targets with concrete KPIs
- **Exit Strategy** — Acquisition targets, IPO path, follow-on rounds
- **Why Us** — Technical validation status, cost advantage, timing window

If these sections are missing, add them as new numbered chapters and update the navigation.

## Pitfalls

1. **Don't skip discovery** — Writing before reading produces shallow, wrong analysis
2. **Don't be overly verbose** — Business audiences want conclusions, not essays
3. **Don't mix technical and business** — Keep them in separate sections unless the user explicitly asks for both
4. **Don't forget the audience** — "给领导汇报" needs business focus; "code review" needs technical depth
5. **Don't generate fake data** — If you don't know costs/user numbers, say "estimated" or ask the user
6. **Don't skip file paths** — Always state where you saved deliverables
7. **Don't use html2pdf.js `.save()` for PDF export** — It fails in headless/blocked environments. Use `.toPdf().get('pdf')` then `pdf.output('blob')` + manual download link instead. If the user later asks to remove PDF export, also remove the CDN script tag, the button, and any `@media print` rules that were added for PDF — but **never remove the `<div class="container">` wrapper** in the process
8. **Don't force fixed aspect ratios on showcase images** — Use `height: auto; object-fit: contain` to preserve original proportions
9. **Don't put raw prompts in user-facing cards** — Show story/narrative text only, keep technical prompts internal
10. **Don't remove container wrappers when cleaning up code** — Removing elements (buttons, scripts, etc.) can accidentally delete the `<div class="container">` wrapper, causing all content to stretch full-width. Always verify container tags remain intact after deletions. If content suddenly becomes full-width after an edit, the container wrapper is the first thing to check
11. **Don't use default `.info-card` styling for feature cards** — Feature cards need dedicated overrides (larger padding, icons, hover effects, enhanced shadows). Default `.info-card` is too plain for highlighted content. Always create a `.highlight-cards .info-card` override block
12. **Don't leave orphaned section headings when restructuring** — When adding new chapters (e.g., "团队", "融资需求") or renumbering existing ones, update the navigation links, anchor IDs, and heading numbers consistently across the entire document. Mismatched numbering confuses readers

## Related Skills

- `writing-plans` — For implementation planning after analysis
- `aliyun-dashscope-video-pipeline` — If the project involves AI generation
- `xhs-ai-short-drama-operator` — If the project is social media content
- `social-media-image-sourcing` — For product showcase image sourcing

## Linked Files

- `references/html-project-book-template.html` — Self-contained HTML project book with navigation, product showcase cards, PDF export, and scroll animations. Copy and modify for new projects.
- `references/business-report-template.md` — Markdown template for 10-section business reports

## Remember

```
Discovery first → Analysis second → Deliverables third
Technical depth for engineers, business clarity for stakeholders
Always save files to known paths
Always state where you saved things
```

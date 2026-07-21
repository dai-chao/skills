# iOS Weather App Replica — Reference

Complete reproduction recipe from the June 2026 session. Covers the exact header compacting and card folding patterns that worked.

## Final Working Structure

```html
<!-- Fixed-height header container -->
<div class="header-section" id="headerSection">
    <div class="header" id="header">
        <div class="header-inner" id="headerInner">
            <div class="city">北京</div>
            <div class="desc">多云</div>
            <div class="temp">26°</div>
            <div class="hl">最高 32° · 最低 21°</div>
        </div>
    </div>
</div>

<!-- Cards container -->
<div class="cards" id="cards">
    <div class="card" data-card>...逐小时预报...</div>
    <div class="card" data-card>...10日预报...</div>
    <div class="card" data-card>...空气质量...</div>
    <div class="card" data-card>...紫外线指数...</div>
    <div class="card" data-card>...日落...</div>
</div>
```

## CSS — Header (Fixed Height, Transform Deformation)

```css
/* Header container: NEVER changes height */
.header-section {
    height: 280px;
    position: relative;
    overflow: hidden;
}

/* Inner content positioned at bottom */
.header {
    position: absolute;
    bottom: 20px;
    left: 0; right: 0;
    text-align: center;
    padding: 0 20px;
}

.header-inner {
    display: flex;
    flex-direction: column;
    align-items: center;
    transition: transform 0.3s;
    transform-origin: center center;
}

/* Expanded state */
.header .city { font-size: 32px; font-weight: 400; }
.header .desc { font-size: 16px; color: rgba(255,255,255,0.8); margin-top: 4px; }
.header .temp { font-size: 96px; font-weight: 200; letter-spacing: -2px; margin-top: 8px; }
.header .hl { font-size: 15px; color: rgba(255,255,255,0.7); margin-top: 8px; }

/* Compact state: ONLY transform changes, container height stays 280px */
.header-section.compact .header-inner {
    transform: scale(0.6) translateY(-40px);
}
.header-section.compact .city { font-size: 20px; }
.header-section.compact .desc { font-size: 20px; color: #fff; margin-top: 0; }
.header-section.compact .temp { font-size: 20px; font-weight: 400; letter-spacing: 0; margin-top: 0; }
.header-section.compact .hl { opacity: 0; height: 0; overflow: hidden; margin-top: 0; }
```

## CSS — Cards (Frosted Glass)

```css
.cards { padding: 0 16px; }

.card {
    background: rgba(30, 50, 70, 0.5);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-radius: 16px;
    margin-bottom: 12px;
    overflow: hidden;
    border: 1px solid rgba(255,255,255,0.08);
    will-change: height, opacity;
}

.card-hd {
    padding: 12px 16px;
    font-size: 13px;
    text-transform: uppercase;
    color: rgba(255,255,255,0.6);
    letter-spacing: 0.5px;
    font-weight: 500;
    border-bottom: 1px solid rgba(255,255,255,0.06);
}

.card-bd { padding: 12px 16px; }
```

## JavaScript — Scroll Handler

```javascript
const scroll = document.getElementById('scroll');
const headerSection = document.getElementById('headerSection');
const cards = document.querySelectorAll('.card');

// Measure card dimensions once
const cardData = [];
function measure() {
    cardData.length = 0;
    cards.forEach(card => {
        card.style.height = '';
        card.style.opacity = '';
        card.style.overflow = '';
        const fullH = card.getBoundingClientRect().height;
        const headerH = card.querySelector('.card-hd').getBoundingClientRect().height;
        cardData.push({ el: card, fullHeight: fullH, headerHeight: headerH });
    });
}
window.addEventListener('load', measure);
setTimeout(measure, 100);
setTimeout(measure, 500);

let ticking = false;
scroll.addEventListener('scroll', () => {
    if (!ticking) {
        requestAnimationFrame(handleScroll);
        ticking = true;
    }
});

function handleScroll() {
    ticking = false;
    const scrollTop = scroll.scrollTop;
    
    // Toggle compact class at threshold
    const compactThreshold = 80;
    if (scrollTop > compactThreshold) {
        headerSection.classList.add('compact');
    } else {
        headerSection.classList.remove('compact');
    }

    // Use header bottom as fold trigger line
    const headerRect = headerSection.getBoundingClientRect();
    const foldTriggerY = headerRect.bottom;

    cards.forEach((card, i) => {
        const data = cardData[i];
        if (!data) return;

        const rect = card.getBoundingClientRect();
        const cardTop = rect.top;
        const fullH = data.fullHeight;
        const headerH = data.headerHeight;

        const distance = foldTriggerY - cardTop;

        if (distance > 0 && cardTop < foldTriggerY + fullH) {
            const minHeight = headerH + 16;
            const maxFoldDistance = fullH - minHeight;
            const foldProgress = Math.min(1, distance / (maxFoldDistance * 0.8));
            const currentHeight = fullH - (fullH - minHeight) * foldProgress;
            const heightRatio = currentHeight / fullH;
            
            let opacity = 1;
            if (heightRatio < 0.4) {
                opacity = heightRatio / 0.4;
            }

            card.style.height = currentHeight + 'px';
            card.style.opacity = Math.max(0, opacity);
            card.style.overflow = 'hidden';
        } else if (cardTop >= foldTriggerY) {
            card.style.height = '';
            card.style.opacity = '';
            card.style.overflow = '';
        } else {
            card.style.height = (data.headerHeight + 16) + 'px';
            card.style.opacity = '0';
            card.style.overflow = 'hidden';
        }
    });
}
```

## Key Parameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| Header container height | 280px | Fixed, never changes |
| Compact threshold | 80px scroll | When header content starts scaling |
| Header scale | 0.6 | Visual compacting factor |
| Card min height | headerH + 16px | Keeps title + padding visible |
| Fold progress divisor | 0.8 | Controls fold speed (lower = faster) |
| Opacity fade start | heightRatio < 0.4 | Height mostly done before fading |

## Background Gradient

```css
background: linear-gradient(180deg, 
    #1a3a5c 0%, 
    #2d5a87 30%, 
    #4a7fb5 60%, 
    #6b9fd4 100%
);
```

## What Didn't Work (Documented Pitfalls)

1. **Changing header height on scroll** → Layout jump, cards jump up
2. **Using `transform: scaleY()` on cards** → Document flow doesn't update, spacing breaks
3. **Using `display: none/block` for header toggle** → Reflow causes visible jump
4. **Sticky header without fixed height** → Cards overlap header when scrolling
5. **Calculating fold based on `scrollTop` alone** → Doesn't account for sticky header position

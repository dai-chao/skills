/* Skill Café — performance-tuned app */
(() => {
  const DATA_URL = "data/skills.json";
  const SYNONYMS_URL = "data/search-synonyms.json";
  const SKILL_ROOT = "..";
  const PAGE_SIZE = 24;
  const SEARCH_DEBOUNCE_MS = 180;

  /** API base for AI ask. Override via window.SKILL_CAFE_API or <meta name="skill-cafe-api">. */
  function apiBase() {
    const fromWindow =
      typeof window.SKILL_CAFE_API === "string" ? window.SKILL_CAFE_API.trim() : "";
    const fromMeta = document.querySelector('meta[name="skill-cafe-api"]')?.content?.trim() || "";
    const raw = fromWindow || fromMeta;
    if (raw) return raw.replace(/\/$/, "");
    if (location.hostname === "localhost" || location.hostname === "127.0.0.1") {
      return "http://localhost:3000";
    }
    return ""; // same-origin behind reverse proxy
  }

  function apiUrl(path) {
    const base = apiBase();
    const p = path.startsWith("/") ? path : `/${path}`;
    return base ? `${base}${p}` : p;
  }

  // Lightweight inline SVG icons (avoid lucide.createIcons on hundreds of cards)
  const ICON_SVG = {
    pointer: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4l7.07 17 2.51-7.39L21 11.07z"/></svg>',
    git: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="6" x2="6" y1="3" y2="15"/><circle cx="18" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M18 9a9 9 0 0 1-9 9"/></svg>',
    shield: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/><path d="m9 12 2 2 4-4"/></svg>',
    palette: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="13.5" cy="6.5" r=".5" fill="currentColor"/><circle cx="17.5" cy="10.5" r=".5" fill="currentColor"/><circle cx="8.5" cy="7.5" r=".5" fill="currentColor"/><circle cx="6.5" cy="12.5" r=".5" fill="currentColor"/><path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.926 0 1.648-.746 1.648-1.688 0-.437-.18-.835-.437-1.125-.29-.289-.438-.652-.438-1.125a1.64 1.64 0 0 1 1.668-1.668h1.996c3.051 0 5.555-2.503 5.555-5.554C21.965 6.012 17.461 2 12 2z"/></svg>',
    flask: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2v6a2 2 0 0 0 .245.96l5.51 10.08A2 2 0 0 1 18 22H6a2 2 0 0 1-1.755-2.96l5.51-10.08A2 2 0 0 0 10 8V2"/><path d="M6.453 15h11.094"/></svg>',
    server: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="8" x="2" y="2" rx="2" ry="2"/><rect width="20" height="8" x="2" y="14" rx="2" ry="2"/><line x1="6" x2="6.01" y1="6" y2="6"/><line x1="6" x2="6.01" y1="18" y2="18"/></svg>',
    file: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/></svg>',
    globe: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/></svg>',
    chart: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v16a2 2 0 0 0 2 2h16"/><path d="M18 17V9"/><path d="M13 17V5"/><path d="M8 17v-3"/></svg>',
    card: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="14" x="2" y="5" rx="2"/><line x1="2" x2="22" y1="10" y2="10"/></svg>',
    map: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.106 5.553a2 2 0 0 0 1.788 0l3.659-1.83A1 1 0 0 1 21 4.619v12.764a1 1 0 0 1-.553.894l-4.553 2.277a2 2 0 0 1-1.788 0l-4.212-2.106a2 2 0 0 0-1.788 0l-3.659 1.83A1 1 0 0 1 3 19.381V6.618a1 1 0 0 1 .553-.894l4.553-2.277a2 2 0 0 1 1.788 0z"/><path d="M15 5.764v15"/><path d="M9 3.236v15"/></svg>',
    wand: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 4V2"/><path d="M15 16v-2"/><path d="M8 9h2"/><path d="M20 9h2"/><path d="M17.8 11.8 19 13"/><path d="M15 9h.01"/><path d="M17.8 6.2 19 5"/><path d="m3 21 9-9"/><path d="M12.2 6.2 11 5"/></svg>',
    puzzle: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19.439 7.85c-.075.332.109.682.41.865a2.001 2.001 0 0 1 .08 3.362 1.998 1.998 0 0 1-.49 3.04 2 2 0 0 1-2.96.49 2 2 0 0 0-3.362.08 2 2 0 0 1-3.04-.49 2.001 2.001 0 0 0-3.04-.49 2 2 0 0 1-.49-3.04 2 2 0 0 0-.08-3.362A2 2 0 0 1 5.44 7.85a2 2 0 0 0 .49-3.04 2 2 0 0 1 .49-3.04 2 2 0 0 1 3.04.49A2 2 0 0 0 12.5 2a2 2 0 0 1 3.04.49 2 2 0 0 0 3.04.49 2 2 0 0 1 .49 3.04 2 2 0 0 0 .49 3.04Z"/></svg>',
    trend: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>',
    box: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/><path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/></svg>',
  };

  const CAT_ICON_KEY = {
    "01-cursor-native": "pointer",
    "02-workflow-git": "git",
    "03-code-quality": "shield",
    "04-frontend-ui": "palette",
    "05-testing": "flask",
    "06-devops-infra": "server",
    "07-docs-office": "file",
    "08-research-web": "globe",
    "09-analytics": "chart",
    "10-payments-auth": "card",
    "11-planning": "map",
    "12-meta": "wand",
    "13-integrations": "puzzle",
    "14-finance": "trend",
    "99-misc": "box",
  };

  const state = {
    data: null,
    skills: [],
    byId: null,
    sorted: { hot: null, recent: null, name: null },
    view: "home",
    tab: "all",
    query: "",
    category: "",
    sort: "hot",
    page: 1,
    filteredCache: null,
    filteredKey: "",
    current: null,
    searchTimer: null,
    renderToken: 0,
    loadingMore: false,
    io: null,
    ask: null,
  };

  const $ = (sel, el = document) => el.querySelector(sel);
  const I18n = () => window.SkillCafeI18n;
  const t = (key) => I18n()?.t(key) ?? key;
  const lang = () => I18n()?.getLang?.() || "zh";

  function skillDesc(skill) {
    if (lang() === "zh") {
      return skill.description_zh || skill.description || "";
    }
    return skill.description || skill.description_zh || "";
  }

  function skillCat(skill) {
    return I18n()?.catLabel(skill.category, skill.category_label) || skill.category_label;
  }

  function refreshChromeIcons(root) {
    // Only for static chrome / modal — never for large lists
    if (window.lucide?.createIcons) {
      window.lucide.createIcons({
        attrs: { "stroke-width": 2 },
        nameAttr: "data-lucide",
        root: root || document.body,
      });
    }
  }

  function formatInstalls(n) {
    if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + "M";
    if (n >= 1_000) return (n / 1_000).toFixed(1) + "K";
    return String(n);
  }

  function escapeHtml(str) {
    return String(str ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function catSvg(cat) {
    return ICON_SVG[CAT_ICON_KEY[cat] || "box"];
  }

  function skillUrl(skill, file = "SKILL.md") {
    return `${SKILL_ROOT}/${skill.path}/${file}`;
  }

  function toast(title, msg, variant = "primary") {
    const el = $("#toast");
    if (!el) return;
    el.variant = variant;
    $("#toastTitle").textContent = title;
    $("#toastMsg").textContent = msg;
    el.toast();
  }

  function debounce(fn, ms) {
    return (...args) => {
      clearTimeout(state.searchTimer);
      state.searchTimer = setTimeout(() => fn(...args), ms);
    };
  }

  /** Lightweight cards — no Shoelace / Lucide per item */
  function cardHtml(skill, { showRank = true } = {}) {
    const gold = skill.rank <= 3;
    const hot = skill.rank <= 30;
    return `<article class="card cv-auto${gold ? " is-gold" : ""}" data-id="${escapeHtml(skill.id)}">
      <div class="card-body">
        <div class="card-top">
          <div class="card-icon">${catSvg(skill.category)}</div>
          ${showRank ? `<span class="rank-badge${gold ? " gold" : ""}">#${skill.rank}</span>` : ""}
        </div>
        <h3>${escapeHtml(skill.title)}</h3>
        <p class="card-desc">${escapeHtml(skillDesc(skill))}</p>
        <div class="card-meta">
          <span class="chip cat">${escapeHtml(skillCat(skill))}</span>
          ${hot ? `<span class="chip hot">${escapeHtml(t("hot"))}</span>` : ""}
          <span class="meta-item">${escapeHtml(skill.updated)}</span>
          <span class="meta-item">${formatInstalls(skill.popularity)} ${escapeHtml(t("installs"))}</span>
        </div>
        <div class="card-actions">
          <button type="button" class="btn-lite primary" data-action="preview" data-id="${escapeHtml(skill.id)}">${escapeHtml(t("view"))}</button>
          <button type="button" class="btn-lite" data-action="download" data-id="${escapeHtml(skill.id)}">${escapeHtml(t("download"))}</button>
        </div>
      </div>
    </article>`;
  }

  function getSkill(id) {
    return state.byId?.get(id);
  }

  function ensureSorted(key) {
    if (state.sorted[key]) return state.sorted[key];
    const arr = state.skills.slice();
    if (key === "hot") arr.sort((a, b) => b.hot - a.hot);
    else if (key === "recent") arr.sort((a, b) => b.updated_ts - a.updated_ts);
    else if (key === "name") arr.sort((a, b) => a.name.localeCompare(b.name));
    else arr.sort((a, b) => b.hot - a.hot);
    state.sorted[key] = arr;
    return arr;
  }

  function filterKey() {
    return `${state.tab}|${state.sort}|${state.category}|${state.query.trim().toLowerCase()}`;
  }

  /** Loaded from data/search-synonyms.json — category + term aliases */
  let searchSynonyms = { terms: {}, category_keywords: {} };

  function expandSearchQuery(q) {
    const raw = String(q || "").trim().toLowerCase();
    if (!raw) return [];
    const terms = new Set([raw]);
    for (const syn of searchSynonyms.terms[raw] || []) {
      terms.add(String(syn).toLowerCase());
    }
    return [...terms];
  }

  function textHasSearchTerm(text, term) {
    if (!text || !term) return false;
    if (term.length <= 2 && /^[a-z0-9]+$/i.test(term)) {
      return new RegExp(`(?:^|[^a-z0-9])${term}(?:[^a-z0-9]|$)`, "i").test(text);
    }
    return text.includes(term);
  }

  function skillMatchesQuery(skill, q) {
    const terms = expandSearchQuery(q);
    if (!terms.length) return true;
    const hay = skill._q || "";
    return terms.some((t) => textHasSearchTerm(hay, t));
  }

  function resolveAskSkills(payloadSkills) {
    return (payloadSkills || [])
      .map((s) => {
        const full = getSkill(s.id);
        if (full) return full;
        return {
          id: s.id,
          name: s.name,
          title: s.title || s.name,
          description: s.description || "",
          description_zh: s.description_zh || "",
          category: s.category || "",
          category_label: s.category_label || "",
          popularity: s.popularity || 0,
          hot: s.hot || 0,
          rank: s.rank || 999,
          updated: s.updated || "",
          path: s.path || s.id,
          files: s.files || ["SKILL.md"],
          _q: `${s.name || ""} ${s.title || ""} ${s.description || ""} ${s.description_zh || ""}`.toLowerCase(),
        };
      })
      .filter((s) => s && s.id);
  }

  const ASK_PAGE_SIZE = 9;

  function clearAskMode({ rerender = true } = {}) {
    state.ask = null;
    const panel = $("#askPanel");
    const skillsEl = $("#askSkills");
    const webEl = $("#askWeb");
    const pagerEl = $("#askPager");
    const loadingEl = $("#askLoading");
    if (panel) {
      panel.hidden = true;
      panel.classList.remove("is-loading");
    }
    if (loadingEl) loadingEl.hidden = true;
    if (skillsEl) skillsEl.innerHTML = "";
    if (webEl) {
      webEl.hidden = true;
      webEl.innerHTML = "";
    }
    if (pagerEl) {
      pagerEl.hidden = true;
      pagerEl.innerHTML = "";
    }
    const tips = $("#askTips");
    if (tips) tips.hidden = false;
    if (rerender) {
      /* panel already cleared */
    }
  }

  function renderAskSkillsPage() {
    const skillsEl = $("#askSkills");
    const pagerEl = $("#askPager");
    if (!skillsEl || !state.ask?.skills?.length) {
      if (skillsEl) skillsEl.innerHTML = "";
      if (pagerEl) {
        pagerEl.hidden = true;
        pagerEl.innerHTML = "";
      }
      return;
    }

    const skills = state.ask.skills;
    const total = skills.length;
    const pageSize = ASK_PAGE_SIZE;
    const totalPages = Math.max(1, Math.ceil(total / pageSize));
    let page = Math.min(Math.max(1, state.ask.page || 1), totalPages);
    state.ask.page = page;

    const start = (page - 1) * pageSize;
    const slice = skills.slice(start, start + pageSize);
    skillsEl.innerHTML = slice.map((s) => cardHtml(s, { showRank: true })).join("");

    if (!pagerEl) return;
    if (totalPages <= 1) {
      pagerEl.hidden = true;
      pagerEl.innerHTML = "";
      return;
    }

    pagerEl.hidden = false;
    const pages = Array.from({ length: totalPages }, (_, i) => i + 1)
      .map(
        (p) =>
          `<button type="button" class="ask-page-btn${p === page ? " is-active" : ""}" data-ask-page="${p}">${p}</button>`
      )
      .join("");
    pagerEl.innerHTML = `
      <button type="button" class="ask-page-nav" data-ask-page="${page - 1}" ${page <= 1 ? "disabled" : ""}>${escapeHtml(
        t("askPagePrev")
      )}</button>
      <div class="ask-page-nums">${pages}</div>
      <button type="button" class="ask-page-nav" data-ask-page="${page + 1}" ${
      page >= totalPages ? "disabled" : ""
    }>${escapeHtml(t("askPageNext"))}</button>
      <span class="ask-page-meta">${escapeHtml(t("askPageMeta").replace("{page}", String(page)).replace("{total}", String(totalPages)).replace("{count}", String(total)))}</span>
    `;
  }

  function renderAskPanel(data) {
    const panel = $("#askPanel");
    const statusEl = $("#askStatus");
    const summaryEl = $("#askSummary");
    const skillsEl = $("#askSkills");
    const webEl = $("#askWeb");
    if (!panel || !statusEl || !summaryEl || !skillsEl || !webEl) return;

    const skills = resolveAskSkills(data.skills);
    const mode = data.mode || "local";
    const summary = data.reply || data.summary || "";
    const keepPage = data === state.ask && state.ask?.page;

    state.ask = {
      active: true,
      mode,
      summary,
      skills,
      web: data.web || null,
      page: keepPage || 1,
    };

    panel.hidden = false;
    panel.classList.remove("is-loading");
    const loadingEl = $("#askLoading");
    if (loadingEl) loadingEl.hidden = true;
    statusEl.textContent = mode === "web" ? t("askModeWeb") : t("askModeLocal");
    statusEl.className = "ask-badge" + (mode === "web" ? " is-web" : "");
    summaryEl.textContent = summary;

    renderAskSkillsPage();

    if (mode === "web" && data.web) {
      webEl.hidden = false;
      const sources = (data.web.sources || [])
        .filter((s) => s.url)
        .map(
          (s) =>
            `<a href="${escapeHtml(s.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(
              s.title || s.url
            )}</a>`
        )
        .join("");
      webEl.innerHTML = `<p class="ask-web-body">${escapeHtml(data.web.text || summary || t("askEmpty"))}</p>${
        sources
          ? `<div class="ask-web-sources"><span class="ask-web-sources-label">${escapeHtml(
              t("askSources")
            )}</span>${sources}</div>`
          : ""
      }`;
      if (!skills.length && data.web.text) {
        summaryEl.textContent = summary.slice(0, 120) || t("askEmpty");
      }
    } else {
      webEl.hidden = true;
      webEl.innerHTML = "";
    }

    const tips = $("#askTips");
    if (tips) tips.hidden = true;
  }

  function getFilteredList() {
    const key = filterKey();
    if (state.filteredCache && state.filteredKey === key) return state.filteredCache;

    const q = state.query.trim().toLowerCase();
    const sortKey =
      state.tab === "hot" ? "hot" :
      state.tab === "recent" ? "recent" :
      state.sort || "hot";

    let list = ensureSorted(sortKey);

    if (state.category) {
      list = list.filter((s) => s.category === state.category);
    }
    if (q) {
      list = list.filter((s) => skillMatchesQuery(s, q));
    }

    if (!q && !state.category && (state.tab === "hot" || state.tab === "recent")) {
      list = list.slice(0, 120);
    }

    state.filteredKey = key;
    state.filteredCache = list;
    return list;
  }

  function trackPage(url, title) {
    try {
      window.umami?.track((props) => ({
        ...props,
        url: url || location.pathname + location.search + location.hash,
        title: title || document.title,
      }));
    } catch (_) {
      /* analytics optional */
    }
  }

  function trackEvent(name, data) {
    try {
      window.umami?.track(name, data);
    } catch (_) {
      /* analytics optional */
    }
  }

  function setView(view) {
    state.view = view;
    document.body.dataset.cafeView = view;
    document.querySelectorAll(".view").forEach((v) => {
      v.classList.toggle("active", v.id === `view-${view}`);
    });
    document.querySelectorAll(".nav-links a[data-view]").forEach((a) => {
      a.classList.toggle("active", a.dataset.view === view);
    });
    $("#nav")?.classList.remove("open");
    if (view === "all") {
      state.page = 1;
      syncTabGroup();
      scheduleRenderExplore();
    } else if (view === "explore") {
      setupInfiniteScroll(false);
      if (state.data) renderHome();
    } else {
      setupInfiniteScroll(false);
    }
    window.scrollTo({ top: 0, behavior: "smooth" });
    const path =
      view === "home"
        ? "/"
        : view === "all"
          ? `/all${state.tab && state.tab !== "all" ? `/${state.tab}` : ""}`
          : `/${view}`;
    trackPage(path, `Skill Café · ${view}`);
  }

  function syncTabGroup() {
    const tg = $("#exploreTabs");
    if (!tg) return;
    const tab = tg.querySelector(`sl-tab[data-tab="${state.tab}"]`);
    if (tab) tg.show(tab.panel);
  }

  function setTab(tab) {
    if (tab === "rank") tab = "hot";
    state.tab = tab;
    state.page = 1;
    state.filteredCache = null;
    const sort = $("#sortSelect");
    if (sort) {
      if (tab === "hot") sort.value = "hot";
      else if (tab === "recent") sort.value = "recent";
      state.sort = sort.value || state.sort;
    }
    if (state.view !== "all") setView("all");
    else {
      syncTabGroup();
      scheduleRenderExplore();
      trackPage(`/all/${tab}`, `Skill Café · all · ${tab}`);
    }
  }

  function renderHome() {
    const byHot = ensureSorted("hot");
    const byRecent = ensureSorted("recent");

    $("#statTotal").textContent = state.data.total.toLocaleString();
    $("#statCats").textContent = state.data.categories.length;
    $("#statHot").textContent = "60";

    $("#homeHot").innerHTML = byHot.slice(0, 6).map((s) => cardHtml(s)).join("");
    $("#homeRecent").innerHTML = byRecent.slice(0, 6).map((s) => cardHtml(s, { showRank: false })).join("");

    $("#heroFeatured").innerHTML = byHot.slice(0, 3).map((s) => `
      <button type="button" class="mini-skill" data-action="preview" data-id="${escapeHtml(s.id)}">
        <span class="mi">${catSvg(s.category)}</span>
        <span>
          <strong>${escapeHtml(s.title)}</strong>
          <span>${formatInstalls(s.popularity)} ${escapeHtml(t("installs"))}</span>
        </span>
      </button>`).join("");

    $("#homeCats").innerHTML = state.data.categories.map((c) => `
      <button type="button" class="cat-pill" data-cat="${escapeHtml(c.id)}">
        <span class="cat-pill-ico">${catSvg(c.id)}</span>
        ${escapeHtml(I18n().catLabel(c.id, c.label))}
      </button>`).join("");
  }

  function scheduleRenderExplore() {
    const token = ++state.renderToken;
    requestAnimationFrame(() => {
      if (token !== state.renderToken) return;
      renderExplore();
    });
  }

  function renderExplore() {
    const list = getFilteredList();
    const total = list.length;
    const visible = list.slice(0, state.page * PAGE_SIZE);
    const grid = $("#exploreGrid");
    const empty = $("#exploreEmpty");
    const pager = $("#pager");

    const catLabel = state.category
      ? I18n().catLabel(state.category, state.data.categories.find((c) => c.id === state.category)?.label || "")
      : "";

    $("#resultMeta").innerHTML = `${escapeHtml(t("found"))} <strong>${total}</strong> ${escapeHtml(t("skillsUnit"))} · ${escapeHtml(t("showing"))} ${visible.length}${
      state.query ? ` · “${escapeHtml(state.query)}”` : ""
    }${catLabel ? ` · ${escapeHtml(catLabel)}` : ""}`;

    if (!total) {
      grid.hidden = true;
      empty.hidden = false;
      pager.hidden = true;
      state.loadingMore = false;
      setupInfiniteScroll(false);
      return;
    }
    empty.hidden = true;
    grid.hidden = false;
    grid.innerHTML = visible.map((s) => cardHtml(s)).join("");

    const hasMore = visible.length < total;
    const spinner = $("#pagerSpinner");

    if (!total) {
      pager.hidden = true;
      if (spinner) spinner.hidden = true;
    } else {
      pager.hidden = false;
      if (spinner) spinner.hidden = !state.loadingMore;
      $("#pagerMeta").textContent = hasMore
        ? `${t("shownOf")} ${visible.length} / ${total}`
        : `${t("totalOf")} ${total} ${t("items")}`.trim();
    }

    state.loadingMore = false;
    setupInfiniteScroll(hasMore);
  }

  function setupInfiniteScroll(hasMore) {
    const sentinel = $("#pagerSentinel");
    if (!sentinel) return;

    if (state.io) {
      state.io.disconnect();
      state.io = null;
    }

    if (!hasMore || state.view !== "all") return;

    state.io = new IntersectionObserver(
      (entries) => {
        const hit = entries.some((e) => e.isIntersecting);
        if (!hit || state.loadingMore || state.view !== "all") return;
        const list = getFilteredList();
        if (state.page * PAGE_SIZE >= list.length) return;
        state.loadingMore = true;
        const spinner = $("#pagerSpinner");
        if (spinner) spinner.hidden = false;
        state.page += 1;
        scheduleRenderExplore();
      },
      {
        root: null,
        rootMargin: "240px 0px",
        threshold: 0,
      }
    );
    state.io.observe(sentinel);
  }

  function fillCategories() {
    const sel = $("#categoryFilter");
    if (!sel) return;
    sel.querySelectorAll("sl-option").forEach((o, i) => {
      if (i > 0) o.remove();
    });
    const frag = document.createDocumentFragment();
    state.data.categories.forEach((c) => {
      const opt = document.createElement("sl-option");
      opt.value = c.id;
      opt.textContent = I18n().catLabel(c.id, c.label);
      frag.appendChild(opt);
    });
    sel.appendChild(frag);
  }

  function lockBodyScroll(lock) {
    const body = document.body;
    // 不改 overflow / 不隐藏滚动条，避免开关弹窗时滚动条显隐导致页面左右抖动
    // 背景滚动由弹窗上的 wheel 拦截 + 下方 touch 拦截完成
    if (lock) {
      if (body.dataset.scrollLocked === "1") return;
      body.dataset.scrollLocked = "1";
      body.dataset.scrollY = String(window.scrollY || window.pageYOffset || 0);
    } else {
      if (body.dataset.scrollLocked !== "1") return;
      body.dataset.scrollLocked = "0";
      body.dataset.scrollY = "";
    }
  }

  function onLockTouchMove(e) {
    if (document.body.dataset.scrollLocked !== "1") return;
    // 允许预览区内部滚动
    if (e.target.closest?.(".modal-preview")) return;
    e.preventDefault();
  }

  function onLockWheel(e) {
    if (document.body.dataset.scrollLocked !== "1") return;
    if (e.target.closest?.("sl-dialog") || e.target.closest?.(".skill-dialog")) return;
    e.preventDefault();
  }

  function onLockScroll() {
    if (document.body.dataset.scrollLocked !== "1") return;
    const y = parseInt(document.body.dataset.scrollY || "0", 10) || 0;
    if ((window.scrollY || 0) !== y) window.scrollTo(0, y);
  }

  function splitFrontmatter(md) {
    if (!md.startsWith("---\n") && !md.startsWith("---\r\n")) {
      return { frontmatter: null, body: md };
    }
    const match = md.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n?([\s\S]*)$/);
    if (!match) return { frontmatter: null, body: md };
    return { frontmatter: match[1].trim(), body: match[2].trim() };
  }

  function renderMarkdown(md) {
    const el = $("#modalPreview");
    if (!window.marked?.parse) {
      el.textContent = md;
      return;
    }

    const { frontmatter, body } = splitFrontmatter(md);
    let html = "";
    if (frontmatter) {
      html += `<details class="md-frontmatter"><summary>YAML frontmatter</summary><pre><code class="language-yaml">${escapeHtml(frontmatter)}</code></pre></details>`;
    }

    try {
      window.marked.setOptions?.({ gfm: true, breaks: false });
      html += window.marked.parse(body || md);
    } catch (err) {
      el.innerHTML = `<p class="md-error">Markdown 渲染失败：${escapeHtml(err.message)}</p>`;
      return;
    }

    el.innerHTML = window.DOMPurify?.sanitize
      ? window.DOMPurify.sanitize(html, { USE_PROFILES: { html: true } })
      : html;

    if (window.hljs?.highlightElement) {
      el.querySelectorAll("pre code").forEach((block) => {
        try {
          window.hljs.highlightElement(block);
        } catch (_) {
          /* ignore unknown langs */
        }
      });
    }
  }

  async function openPreview(skill) {
    state.current = skill;
    const dialog = $("#modal");
    $("#modalTitle").textContent = skill.title;
    $("#modalDesc").textContent = skillDesc(skill);
    $("#modalIcon").innerHTML = catSvg(skill.category);
    $("#modalMeta").innerHTML = `
      <span class="chip cat">${escapeHtml(skillCat(skill))}</span>
      <span class="chip">#${skill.rank}</span>
      <span class="chip hot">${formatInstalls(skill.popularity)} ${escapeHtml(t("installs"))}</span>
      <span class="chip">${escapeHtml(t("updated"))} ${escapeHtml(skill.updated)}</span>
      <span class="chip">${(skill.files?.length || 1)} ${escapeHtml(t("files"))}</span>`;
    $("#modalPreview").innerHTML = `<p class="md-muted">${escapeHtml(t("loadingPreview"))}</p>`;
    lockBodyScroll(true);
    dialog.show();
    trackEvent("preview-skill", { id: skill.id, name: skill.name });

    try {
      const res = await fetch(skillUrl(skill));
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const text = await res.text();
      renderMarkdown(text);
    } catch (err) {
      $("#modalPreview").innerHTML = `<pre class="md-error">${escapeHtml(
        `无法加载预览（${err.message}）。\n请从 skills 根目录启动：\ncd ~/Desktop/skills && python3 -m http.server 8765\n访问 http://localhost:8765/site/`
      )}</pre>`;
    }
  }

  function downloadBlob(filename, blob) {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 1500);
  }

  async function downloadMd(skill) {
    const res = await fetch(skillUrl(skill));
    if (!res.ok) throw new Error(`无法下载 SKILL.md (${res.status})`);
    downloadBlob(
      `${skill.name}-SKILL.md`,
      new Blob([await res.text()], { type: "text/markdown;charset=utf-8" })
    );
    toast(t("dlDone"), `${skill.name}-SKILL.md`);
  }

  async function downloadZip(skill) {
    if (typeof JSZip === "undefined") {
      await downloadMd(skill);
      return;
    }
    const zip = new JSZip();
    const folder = zip.folder(skill.name);
    // Prefer SKILL.md first; cap concurrent-ish sequential fetch for small folders
    const files = (skill.files?.length ? skill.files : ["SKILL.md"]).slice(0, 30);
    let ok = 0;
    await Promise.all(
      files.map(async (file) => {
        try {
          const res = await fetch(skillUrl(skill, file));
          if (!res.ok) return;
          folder.file(file, await res.arrayBuffer());
          ok += 1;
        } catch { /* skip */ }
      })
    );
    if (!ok) throw new Error("没有成功打包任何文件，请确认本地服务器已启动");
    downloadBlob(`${skill.name}.zip`, await zip.generateAsync({ type: "blob" }));
    toast(t("zipDone"), `${skill.name}.zip · ${ok} ${t("filesUnit")}`);
  }

  async function handleDownload(skill, mdOnly = false) {
    try {
      if (mdOnly) await downloadMd(skill);
      else await downloadZip(skill);
      trackEvent(mdOnly ? "download-md" : "download-zip", { id: skill.id, name: skill.name });
    } catch (err) {
      toast(t("dlFail"), err.message || String(err), "danger");
    }
  }

  function bindAskUi() {
    const form = $("#askForm");
    const input = $("#askInput");
    const send = $("#askSend");
    const panel = $("#askPanel");
    const statusEl = $("#askStatus");
    const summaryEl = $("#askSummary");
    const skillsEl = $("#askSkills");
    const webEl = $("#askWeb");
    if (!form || !input || !panel) return;

    let busy = false;

    function resizeAskInput() {
      if (!(input instanceof HTMLTextAreaElement)) return;
      input.style.height = "auto";
      input.style.height = `${Math.min(input.scrollHeight, 160)}px`;
    }

    function setBusy(v) {
      busy = v;
      if (send) send.disabled = v;
      input.disabled = v;
    }

    function showAskError(message) {
      panel.hidden = false;
      panel.classList.remove("is-loading");
      const loadingEl = $("#askLoading");
      if (loadingEl) loadingEl.hidden = true;
      if (statusEl) {
        statusEl.textContent = t("askError");
        statusEl.className = "ask-badge is-web";
      }
      if (summaryEl) summaryEl.textContent = message;
      if (skillsEl) skillsEl.innerHTML = "";
      if (webEl) {
        webEl.hidden = true;
        webEl.innerHTML = "";
      }
      state.ask = { active: true, mode: "error", skills: [] };
    }

    async function runAsk(query) {
      const q = String(query || "").trim();
      if (!q || busy) return;

      if (state.view !== "home") setView("home");

      input.value = q;
      resizeAskInput();
      setBusy(true);

      panel.hidden = false;
      panel.classList.add("is-loading");
      const loadingEl = $("#askLoading");
      if (loadingEl) loadingEl.hidden = false;
      if (statusEl) {
        statusEl.textContent = t("askSearching");
        statusEl.className = "ask-badge is-loading";
      }
      if (summaryEl) summaryEl.textContent = "";
      if (skillsEl) skillsEl.innerHTML = "";
      const pagerEl = $("#askPager");
      if (pagerEl) {
        pagerEl.hidden = true;
        pagerEl.innerHTML = "";
      }
      if (webEl) {
        webEl.hidden = true;
        webEl.innerHTML = "";
      }

      try {
        const res = await fetch(apiUrl("/api/ask"), {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ query: q }),
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          showAskError(data.error || (res.status >= 500 ? t("askNeedServer") : t("askError")));
          return;
        }
        renderAskPanel(data);
        trackEvent("ask", { mode: data.mode });
      } catch (_err) {
        showAskError(t("askNeedServer"));
      } finally {
        setBusy(false);
        input.focus();
      }
    }

    form.addEventListener("submit", (e) => {
      e.preventDefault();
      runAsk(input.value);
    });

    input.addEventListener("input", resizeAskInput);
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        if (!busy) runAsk(input.value);
      }
    });
    resizeAskInput();

    $("#askTips")?.addEventListener("click", (e) => {
      const tip = e.target.closest("[data-ask]");
      if (!tip) return;
      runAsk(tip.getAttribute("data-ask"));
    });

    $("#askClear")?.addEventListener("click", () => {
      clearAskMode();
      input.focus();
    });

    $("#askPager")?.addEventListener("click", (e) => {
      const btn = e.target.closest("[data-ask-page]");
      if (!btn || btn.disabled || !state.ask?.skills?.length) return;
      const page = Number(btn.getAttribute("data-ask-page"));
      if (!Number.isFinite(page) || page < 1) return;
      state.ask.page = page;
      renderAskSkillsPage();
      skillsEl?.scrollIntoView({ behavior: "smooth", block: "nearest" });
    });

    document.addEventListener("keydown", (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "j") {
        e.preventDefault();
        if (state.view !== "home") setView("home");
        requestAnimationFrame(() => {
          input.focus();
          $("#ask-section")?.scrollIntoView({ behavior: "smooth", block: "start" });
        });
      }
    });
  }

  function bindEvents() {
    document.body.addEventListener("click", (e) => {
      const langBtn = e.target.closest("[data-set-lang]");
      if (langBtn) {
        I18n().setLang(langBtn.getAttribute("data-set-lang"));
        return;
      }

      const catBtn = e.target.closest("[data-cat]");
      if (catBtn) {
        state.category = catBtn.dataset.cat;
        state.page = 1;
        state.filteredCache = null;
        const sel = $("#categoryFilter");
        if (sel) sel.value = state.category;
        setTab("all");
        return;
      }

      const viewBtn = e.target.closest("a[data-view], button[data-view], sl-button[data-view]");
      if (viewBtn) {
        e.preventDefault();
        const tab = viewBtn.dataset.tab;
        if (tab) setTab(tab);
        else setView(viewBtn.dataset.view);
        return;
      }

      const actionBtn = e.target.closest("[data-action]");
      if (actionBtn) {
        const skill = getSkill(actionBtn.dataset.id);
        if (!skill) return;
        if (actionBtn.dataset.action === "preview") openPreview(skill);
        if (actionBtn.dataset.action === "download") handleDownload(skill);
      }
    });

    $("#navToggle")?.addEventListener("click", () => $("#nav").classList.toggle("open"));

    const onSearch = debounce((value) => {
      state.query = value || "";
      state.page = 1;
      state.filteredCache = null;
      if (state.view !== "all") setView("all");
      else scheduleRenderExplore();
    }, SEARCH_DEBOUNCE_MS);

    $("#searchInput")?.addEventListener("sl-input", (e) => onSearch(e.target.value));

    $("#categoryFilter")?.addEventListener("sl-change", (e) => {
      state.category = e.target.value || "";
      state.page = 1;
      state.filteredCache = null;
      if (state.view !== "all") setView("all");
      else scheduleRenderExplore();
    });

    $("#sortSelect")?.addEventListener("sl-change", (e) => {
      state.sort = e.target.value || "hot";
      state.tab = "all";
      state.page = 1;
      state.filteredCache = null;
      syncTabGroup();
      if (state.view !== "all") setView("all");
      else scheduleRenderExplore();
    });

    $("#exploreTabs")?.addEventListener("sl-tab-show", (e) => {
      const name = e.detail.name;
      if (name && name !== state.tab) {
        state.tab = name;
        state.page = 1;
        state.filteredCache = null;
        if (state.view !== "all") setView("all");
        else scheduleRenderExplore();
      }
    });

    $("#btnFocusSearch")?.addEventListener("click", () => {
      setView("all");
      setTab("all");
      setTimeout(() => $("#searchInput")?.focus(), 50);
    });

    $("#heroAskCta")?.addEventListener("click", () => {
      if (state.view !== "home") setView("home");
      requestAnimationFrame(() => {
        $("#ask-section")?.scrollIntoView({ behavior: "smooth", block: "start" });
        $("#askInput")?.focus();
      });
    });

    $("#modalClose2")?.addEventListener("click", () => $("#modal")?.hide());
    $("#modal")?.addEventListener("sl-after-show", () => {
      // Shoelace 会给 body 加 paddingRight 补偿滚动条；已有 scrollbar-gutter 时会「双重缩进」
      document.body.style.paddingRight = "0px";
      document.documentElement.style.paddingRight = "0px";
    });
    $("#modal")?.addEventListener("sl-after-hide", () => {
      lockBodyScroll(false);
      state.current = null;
      document.body.style.paddingRight = "";
      document.documentElement.style.paddingRight = "";
      document.body.style.overflow = "";
      document.documentElement.style.overflow = "";
    });
    // 弹窗打开时拦截背景滚动（不隐藏滚动条，避免布局抖动）
    document.addEventListener("touchmove", onLockTouchMove, { passive: false });
    document.addEventListener("wheel", onLockWheel, { passive: false });
    window.addEventListener("scroll", onLockScroll, { passive: true });
    $("#modal")?.addEventListener(
      "wheel",
      (e) => {
        const preview = e.target.closest?.(".modal-preview");
        if (preview) {
          const el = preview;
          const atTop = el.scrollTop <= 0 && e.deltaY < 0;
          const atBottom =
            el.scrollTop + el.clientHeight >= el.scrollHeight - 1 && e.deltaY > 0;
          if (atTop || atBottom) e.preventDefault();
          return;
        }
        e.preventDefault();
      },
      { passive: false }
    );
    $("#modalDownload")?.addEventListener("click", () => {
      if (state.current) handleDownload(state.current, false);
    });
    $("#modalDownloadMd")?.addEventListener("click", () => {
      if (state.current) handleDownload(state.current, true);
    });

    document.addEventListener("keydown", (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setView("all");
        setTimeout(() => $("#searchInput")?.focus(), 50);
      }
    });

    window.addEventListener("skillcafe:lang", () => {
      // Rebuild search index language fields + UI lists
      state.filteredCache = null;
      state.skills.forEach((s) => {
        s._q = `${s.name} ${s.title} ${s.description || ""} ${s.description_zh || ""} ${s.category_label || ""} ${s.category}`.toLowerCase();
      });
      if (state.data) {
        if (state.view === "home") {
          renderHome();
          if (state.ask?.active) renderAskPanel(state.ask);
        } else if (state.view === "all") scheduleRenderExplore();
        else if (state.view === "explore") renderHome();
        if (state.current && $("#modal")?.open) openPreview(state.current);
      }
      refreshChromeIcons(document.querySelector(".nav"));
      refreshChromeIcons(document.querySelector(".subnav"));
    });
  }

  function indexSkills(skills) {
    const byId = new Map();
    for (const s of skills) {
      const kw = Array.isArray(s.search_keywords) ? s.search_keywords.join(" ") : "";
      s._q = `${s.name} ${s.title} ${s.description || ""} ${s.description_zh || ""} ${s.category_label || ""} ${s.category} ${kw}`.toLowerCase();
      if (s.files && s.files.length > 12) s.files = s.files.slice(0, 12);
      byId.set(s.id, s);
    }
    return byId;
  }

  function initHeroMarquee() {
    const root = $("#heroIconGrid");
    if (!root || root.dataset.ready) return;

    // 路径复用 symbol，减少重复 path 解析
    const paths = [
      "M17.6 9.5c-.2-1.8-1.5-2.7-2.9-2.7-1.3 0-2.1.7-2.6.7s-1.2-.7-2.5-.7C7.7 6.8 6 8.3 6 11.1c0 1.8.7 3.7 1.6 5 .7 1 1.5 2 2.6 2 1 0 1.4-.7 2.6-.7s1.5.7 2.6.7c1.1 0 1.9-1 2.6-2 .5-.7.8-1.4 1-2.1-2.3-1-2.7-4.7-.4-5.5zM14.8 5.2c.5-.6.9-1.5.8-2.4-1 .1-2.1.7-2.7 1.4-.5.6-1 1.5-.8 2.3 1.1.1 2.1-.5 2.7-1.3z",
      "M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10 10-4.5 10-10S17.5 2 12 2zm0 3.2a2.8 2.8 0 110 5.6 2.8 2.8 0 010-5.6zM12 20c-2.4 0-4.5-1.1-5.9-2.8.1-2 4-3.1 5.9-3.1s5.8 1.1 5.9 3.1A7.9 7.9 0 0112 20z",
      "M12 2L3 7v10l9 5 9-5V7L12 2zm0 2.2l6.8 3.8L12 12 5.2 8 12 4.2zM5 9.7l6 3.4v6.7l-6-3.3V9.7zm8 10.1v-6.7l6-3.4v6.8l-6 3.3z",
      "M4 4h7v7H4V4zm9 0h7v7h-7V4zM4 13h7v7H4v-7zm9 0h7v7h-7v-7z",
      "M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 15l-5-5 1.41-1.41L11 14.17l7.59-7.59L20 8l-9 9z",
      "M12 2l2.4 7.4H22l-6 4.6 2.3 7-6.3-4.6L5.7 21l2.3-7-6-4.6h7.6L12 2z",
      "M12 3a9 9 0 00-9 9c0 4 2.6 7.4 6.2 8.6.5.1.6-.2.6-.4v-1.5c-2.5.5-3-1.2-3-1.2-.4-1-1-1.3-1-1.3-.8-.6.1-.6.1-.6.9.1 1.4.9 1.4.9.8 1.4 2.1 1 2.6.8.1-.6.3-1 .6-1.2-2-.2-4.1-1-4.1-4.5 0-1 .4-1.8 1-2.4-.1-.2-.4-1.2.1-2.4 0 0 .8-.3 2.5.9a8.6 8.6 0 014.6 0c1.7-1.2 2.5-.9 2.5-.9.5 1.2.2 2.2.1 2.4.6.6 1 1.4 1 2.4 0 3.5-2.1 4.3-4.1 4.5.3.3.6.8.6 1.6v2.4c0 .2.2.5.6.4A9 9 0 0012 3z",
      "M4 6h16v2H4V6zm0 5h16v2H4v-2zm0 5h10v2H4v-2z",
      "M12 2C8 2 5 5.1 5 9.2c0 5.2 7 12.8 7 12.8s7-7.6 7-12.8C19 5.1 16 2 12 2zm0 10a2.8 2.8 0 110-5.6 2.8 2.8 0 010 5.6z",
      "M19 4H5a2 2 0 00-2 2v12a2 2 0 002 2h14a2 2 0 002-2V6a2 2 0 00-2-2zm0 14H5V8h14v10z",
      "M12 1L3 5v6c0 5.5 3.8 10.7 9 12 5.2-1.3 9-6.5 9-12V5l-9-4zm0 10.99h7c-.5 4.3-3.4 8.1-7 9.14V12H5V6.3l7-3.11V12z",
      "M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z",
      "M20 6h-4V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2H4v14a2 2 0 002 2h12a2 2 0 002-2V6zM10 4h4v2h-4V4zm6 14H8v-2h8v2zm0-4H8v-2h8v2z",
      "M19.14 12.94a7.14 7.14 0 000-1.88l2.03-1.58a.5.5 0 00.12-.64l-1.92-3.32a.5.5 0 00-.6-.22l-2.39.96a7.1 7.1 0 00-1.63-.94l-.36-2.54a.5.5 0 00-.5-.42h-3.84a.5.5 0 00-.5.42l-.36 2.54c-.58.23-1.12.54-1.63.94l-2.39-.96a.5.5 0 00-.6.22L2.71 8.84a.5.5 0 00.12.64l2.03 1.58c-.05.31-.08.63-.08.94s.03.63.08.94L2.83 14.5a.5.5 0 00-.12.64l1.92 3.32c.12.22.39.3.6.22l2.39-.96c.5.4 1.05.71 1.63.94l.36 2.54c.05.24.26.42.5.42h3.84c.24 0 .45-.18.5-.42l.36-2.54c.58-.23 1.12-.54 1.63-.94l2.39.96c.22.08.48 0 .6-.22l1.92-3.32a.5.5 0 00-.12-.64l-2.03-1.58zM12 15.5A3.5 3.5 0 1112 8.5a3.5 3.5 0 010 7z",
      "M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z",
      "M12 3v10.55A4 4 0 1014 17V7h4V3h-6z",
      "M15.5 14h-.8l-.3-.3a6.5 6.5 0 10-.7.7l.3.3v.8l5 5 1.5-1.5-5-5zm-6 0A4.5 4.5 0 1114 9.5 4.5 4.5 0 019.5 14z",
      "M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z",
      "M4 8h4V4H4v4zm6 12h4v-4h-4v4zm-6 0h4v-4H4v4zm0-6h4v-4H4v4zm6 0h4v-4h-4v4zm6-10v4h4V4h-4zm-6 4h4V4h-4v4zm6 6h4v-4h-4v4zm0 6h4v-4h-4v4z",
      "M12 2C8.1 2 5 5.1 5 9v6l-2 2v1h18v-1l-2-2V9c0-3.9-3.1-7-7-7zm0 18c1.1 0 2-.9 2-2h-4c0 1.1.9 2 2 2z",
    ];

    const defs = paths
      .map((d, i) => `<symbol id="hi${i}" viewBox="0 0 24 24"><path fill="currentColor" d="${d}"/></symbol>`)
      .join("");

    // 约 36 个/半轨，覆盖 120vmax；双份无缝。行数压缩，DOM 约原 1/4
    const half = paths
      .map((_, i) => `<svg viewBox="0 0 24 24" aria-hidden="true"><use href="#hi${i % paths.length}"/></svg>`)
      .join("")
      .repeat(2);
    const track = half + half;
    const rows = 22;
    const rowHtml = Array.from({ length: rows }, (_, i) => {
      const dir = i % 2 === 0 ? "is-ltr" : "is-rtl";
      const dur = 110 + (i % 3) * 14;
      const delay = i % 2 === 0 ? `-${(i % 5) * 9}s` : `-${55 + (i % 5) * 8}s`;
      return `<div class="hero-icon-row ${dir}" style="--marquee-dur:${dur}s;--marquee-delay:${delay}"><div class="hero-icon-track">${track}</div></div>`;
    }).join("");

    root.innerHTML =
      `<svg class="hero-icon-defs" aria-hidden="true"><defs>${defs}</defs></svg>` +
      `<div class="hero-icon-stage">${rowHtml}</div>`;
    root.dataset.ready = "1";

    // 离开视口暂停动画，减少后台合成开销
    const hero = root.closest(".hero") || root;
    const io = new IntersectionObserver(
      ([entry]) => {
        root.classList.toggle("is-paused", !entry.isIntersecting);
      },
      { rootMargin: "80px", threshold: 0 }
    );
    io.observe(hero);
  }

  async function init() {
    // Apply browser / saved language before first paint of dynamic content
    I18n()?.applyDom();
    initHeroMarquee();

    bindEvents();
    bindAskUi();
    refreshChromeIcons(document.querySelector(".nav"));
    refreshChromeIcons(document.querySelector(".hero-copy"));
    refreshChromeIcons(document.querySelector(".ask-section"));
    refreshChromeIcons(document.querySelector(".subnav"));

    try {
      const [res, synRes] = await Promise.all([
        fetch(DATA_URL),
        fetch(SYNONYMS_URL).catch(() => null),
      ]);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      if (synRes?.ok) {
        searchSynonyms = await synRes.json().catch(() => searchSynonyms);
      }
      state.data = await res.json();
      state.skills = state.data.skills || [];
      state.byId = indexSkills(state.skills);
      const warmSort = () => {
        ensureSorted("hot");
        ensureSorted("recent");
        ensureSorted("name");
      };
      // Safari 等浏览器无 requestIdleCallback，不能直接引用该标识符
      if (typeof window.requestIdleCallback === "function") {
        window.requestIdleCallback(warmSort);
      } else {
        setTimeout(warmSort, 0);
      }

      fillCategories();
      I18n()?.applyDom();
      renderHome();
    } catch (err) {
      const localHint =
        location.hostname === "localhost" || location.hostname === "127.0.0.1"
          ? `<pre style="text-align:left;background:#fff;padding:1rem;border-radius:12px;display:inline-block;margin-top:1rem">cd ~/Desktop/skills
python3 -m http.server 8765
# → http://localhost:8765/site/</pre>`
          : `<p style="margin-top:1rem;color:rgba(0,0,0,.55)">请稍后刷新重试。若持续失败，可能是部署尚未完成或网络异常。</p>`;
      $("main").innerHTML = `
        <div class="container state-box" style="padding:4rem 1rem">
          <strong>Unable to load skills data / 无法加载数据</strong>
          <p>${escapeHtml(err.message)}</p>
          ${localHint}
        </div>`;
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();

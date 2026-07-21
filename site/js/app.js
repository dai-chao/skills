/* Skill Café — search, rank, hot, recent, download */
(() => {
  const DATA_URL = "data/skills.json";
  /** Skills live one level above /site when served from Desktop/skills */
  const SKILL_ROOT = "..";

  const state = {
    data: null,
    skills: [],
    view: "home",
    tab: "all",
    query: "",
    category: "",
    sort: "rank",
    current: null,
  };

  const $ = (sel, el = document) => el.querySelector(sel);
  const $$ = (sel, el = document) => [...el.querySelectorAll(sel)];

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

  function skillUrl(skill, file = "SKILL.md") {
    return `${SKILL_ROOT}/${skill.path}/${file}`;
  }

  function cardHtml(skill, { showRank = true } = {}) {
    const gold = skill.rank <= 3 ? " gold" : "";
    const hotChip =
      skill.rank <= 30
        ? `<span class="chip hot">热门</span>`
        : "";
    return `
      <article class="card" data-id="${escapeHtml(skill.id)}">
        <div class="card-top">
          <h3>${escapeHtml(skill.title)}</h3>
          ${
            showRank
              ? `<span class="rank-badge${gold}">#${skill.rank}</span>`
              : ""
          }
        </div>
        <p class="card-desc">${escapeHtml(skill.description)}</p>
        <div class="card-meta">
          <span class="chip cat">${escapeHtml(skill.category_label)}</span>
          ${hotChip}
          <span>${escapeHtml(skill.updated)}</span>
          <span>${formatInstalls(skill.popularity)} installs</span>
        </div>
        <div class="card-actions">
          <button class="btn btn-primary btn-sm btn-block-sm" data-action="preview" data-id="${escapeHtml(skill.id)}">查看</button>
          <button class="btn btn-outline btn-sm btn-block-sm" data-action="download" data-id="${escapeHtml(skill.id)}">下载</button>
        </div>
      </article>`;
  }

  function rankItemHtml(skill) {
    return `
      <div class="rank-item" data-id="${escapeHtml(skill.id)}">
        <div class="rank-num">${skill.rank}</div>
        <div>
          <h3>${escapeHtml(skill.title)}</h3>
          <p>${escapeHtml(skill.description)}</p>
        </div>
        <div class="rank-stats">
          <strong>${formatInstalls(skill.popularity)}</strong>
          installs · ${escapeHtml(skill.updated)}
          <div style="margin-top:6px;display:flex;gap:6px;justify-content:flex-end;flex-wrap:wrap">
            <button class="btn btn-primary btn-sm" data-action="preview" data-id="${escapeHtml(skill.id)}">查看</button>
            <button class="btn btn-outline btn-sm" data-action="download" data-id="${escapeHtml(skill.id)}">下载</button>
          </div>
        </div>
      </div>`;
  }

  function getSkill(id) {
    return state.skills.find((s) => s.id === id);
  }

  function filteredSkills() {
    let list = [...state.skills];
    const q = state.query.trim().toLowerCase();
    if (q) {
      list = list.filter((s) => {
        const blob = `${s.name} ${s.title} ${s.description} ${s.category_label} ${s.category}`.toLowerCase();
        return blob.includes(q);
      });
    }
    if (state.category) {
      list = list.filter((s) => s.category === state.category);
    }

    const sortKey =
      state.tab === "hot" ? "hot" :
      state.tab === "recent" ? "recent" :
      state.tab === "rank" ? "rank" :
      state.sort;

    if (sortKey === "hot") list.sort((a, b) => b.hot - a.hot);
    else if (sortKey === "recent") list.sort((a, b) => b.updated_ts - a.updated_ts);
    else if (sortKey === "name") list.sort((a, b) => a.name.localeCompare(b.name));
    else list.sort((a, b) => a.rank - b.rank);

    // preset tabs show a focused slice when not searching
    if (!q && !state.category) {
      if (state.tab === "hot") list = list.slice(0, 60);
      else if (state.tab === "recent") list = list.slice(0, 60);
      else if (state.tab === "rank") list = list.slice(0, 50);
    }
    return list;
  }

  function setView(view) {
    state.view = view;
    $$(".view").forEach((v) => v.classList.toggle("active", v.id === `view-${view}`));
    $("#nav").classList.remove("open");
    if (view === "explore") renderExplore();
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function setTab(tab) {
    state.tab = tab;
    $$(".tab").forEach((t) => t.classList.toggle("active", t.dataset.tab === tab));
    // sync sort dropdown for clarity
    const sort = $("#sortSelect");
    if (tab === "hot") sort.value = "hot";
    else if (tab === "recent") sort.value = "recent";
    else if (tab === "rank") sort.value = "rank";
    state.sort = sort.value;
    if (state.view !== "explore") setView("explore");
    else renderExplore();
  }

  function renderHome() {
    const byHot = [...state.skills].sort((a, b) => b.hot - a.hot);
    const byRecent = [...state.skills].sort((a, b) => b.updated_ts - a.updated_ts);
    const byRank = [...state.skills].sort((a, b) => a.rank - b.rank);

    $("#statTotal").textContent = state.data.total.toLocaleString();
    $("#statCats").textContent = state.data.categories.length;
    $("#statHot").textContent = "60";
    $("#footerStamp").textContent = `更新于 ${state.data.generated_at || "—"} · ${state.data.total} skills`;

    $("#homeHot").innerHTML = byHot.slice(0, 6).map((s) => cardHtml(s)).join("");
    $("#homeRecent").innerHTML = byRecent.slice(0, 6).map((s) => cardHtml(s, { showRank: false })).join("");
    $("#homeRank").innerHTML = byRank.slice(0, 10).map(rankItemHtml).join("");
  }

  function renderExplore() {
    const list = filteredSkills();
    const grid = $("#exploreGrid");
    const rank = $("#exploreRank");
    const empty = $("#exploreEmpty");

    $("#resultMeta").innerHTML = `找到 <strong>${list.length}</strong> 个 skill${
      state.query ? ` · “${escapeHtml(state.query)}”` : ""
    }${state.category ? ` · ${escapeHtml(state.data.categories.find((c) => c.id === state.category)?.label || state.category)}` : ""}`;

    if (!list.length) {
      grid.hidden = true;
      rank.hidden = true;
      empty.hidden = false;
      return;
    }
    empty.hidden = true;

    if (state.tab === "rank" && !state.query) {
      grid.hidden = true;
      rank.hidden = false;
      rank.innerHTML = list.map(rankItemHtml).join("");
    } else {
      rank.hidden = true;
      grid.hidden = false;
      grid.innerHTML = list.map((s) => cardHtml(s)).join("");
    }
  }

  function fillCategories() {
    const sel = $("#categoryFilter");
    const opts = state.data.categories
      .map((c) => `<option value="${escapeHtml(c.id)}">${escapeHtml(c.label)}</option>`)
      .join("");
    sel.innerHTML = `<option value="">全部分类</option>${opts}`;
  }

  async function openPreview(skill) {
    state.current = skill;
    $("#modalTitle").textContent = skill.title;
    $("#modalDesc").textContent = skill.description;
    $("#modalMeta").innerHTML = `
      <span class="chip cat">${escapeHtml(skill.category_label)}</span>
      <span class="chip">#${skill.rank}</span>
      <span class="chip">${formatInstalls(skill.popularity)} installs</span>
      <span class="chip">更新 ${escapeHtml(skill.updated)}</span>
      <span class="chip">${skill.files.length} 文件</span>`;
    $("#modalPreview").textContent = "加载预览…";
    $("#modal").classList.add("open");

    try {
      const res = await fetch(skillUrl(skill));
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const text = await res.text();
      $("#modalPreview").textContent = text.slice(0, 6000) + (text.length > 6000 ? "\n\n…（已截断）" : "");
    } catch (err) {
      $("#modalPreview").textContent =
        `无法加载预览（${err.message}）。\n请用本地服务器打开站点：\ncd ~/Desktop/skills && python3 -m http.server 8765\n然后访问 http://localhost:8765/site/`;
    }
  }

  function closeModal() {
    $("#modal").classList.remove("open");
    state.current = null;
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
    const text = await res.text();
    downloadBlob(`${skill.name}-SKILL.md`, new Blob([text], { type: "text/markdown;charset=utf-8" }));
  }

  async function downloadZip(skill) {
    if (typeof JSZip === "undefined") {
      await downloadMd(skill);
      return;
    }
    const zip = new JSZip();
    const folder = zip.folder(skill.name);
    const files = skill.files?.length ? skill.files : ["SKILL.md"];
    let ok = 0;
    for (const file of files) {
      try {
        const res = await fetch(skillUrl(skill, file));
        if (!res.ok) continue;
        const buf = await res.arrayBuffer();
        folder.file(file, buf);
        ok += 1;
      } catch {
        /* skip missing */
      }
    }
    if (!ok) throw new Error("没有成功打包任何文件，请确认本地服务器已启动");
    const blob = await zip.generateAsync({ type: "blob" });
    downloadBlob(`${skill.name}.zip`, blob);
  }

  async function handleDownload(skill, mdOnly = false) {
    try {
      if (mdOnly) await downloadMd(skill);
      else await downloadZip(skill);
    } catch (err) {
      alert(err.message || String(err));
    }
  }

  function bindEvents() {
    document.body.addEventListener("click", (e) => {
      const viewBtn = e.target.closest("[data-view]");
      if (viewBtn) {
        e.preventDefault();
        const view = viewBtn.dataset.view;
        const tab = viewBtn.dataset.tab;
        if (tab) setTab(tab);
        else setView(view);
        return;
      }

      const tabBtn = e.target.closest(".tab[data-tab]");
      if (tabBtn) {
        setTab(tabBtn.dataset.tab);
        return;
      }

      const actionBtn = e.target.closest("[data-action]");
      if (actionBtn) {
        const skill = getSkill(actionBtn.dataset.id);
        if (!skill) return;
        if (actionBtn.dataset.action === "preview") openPreview(skill);
        if (actionBtn.dataset.action === "download") handleDownload(skill);
        return;
      }
    });

    $("#navToggle").addEventListener("click", () => {
      $("#nav").classList.toggle("open");
    });

    $("#searchInput").addEventListener("input", (e) => {
      state.query = e.target.value;
      if (state.view !== "explore") setView("explore");
      renderExplore();
    });

    $("#categoryFilter").addEventListener("change", (e) => {
      state.category = e.target.value;
      renderExplore();
    });

    $("#sortSelect").addEventListener("change", (e) => {
      state.sort = e.target.value;
      if (state.tab === "all") renderExplore();
      else {
        // switching sort from preset tabs moves to all+sort
        state.tab = "all";
        $$(".tab").forEach((t) => t.classList.toggle("active", t.dataset.tab === "all"));
        renderExplore();
      }
    });

    $("#btnFocusSearch").addEventListener("click", () => {
      setView("explore");
      setTab("all");
      $("#searchInput").focus();
    });

    $("#frapBtn").addEventListener("click", () => {
      setView("explore");
      setTab("all");
      $("#searchInput").focus();
      window.scrollTo({ top: 0, behavior: "smooth" });
    });

    $("#modalClose").addEventListener("click", closeModal);
    $("#modalClose2").addEventListener("click", closeModal);
    $("#modal").addEventListener("click", (e) => {
      if (e.target.id === "modal") closeModal();
    });
    $("#modalDownload").addEventListener("click", () => {
      if (state.current) handleDownload(state.current, false);
    });
    $("#modalDownloadMd").addEventListener("click", () => {
      if (state.current) handleDownload(state.current, true);
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") closeModal();
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setView("explore");
        $("#searchInput").focus();
      }
    });
  }

  async function init() {
    bindEvents();
    try {
      const res = await fetch(DATA_URL);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      state.data = await res.json();
      state.skills = state.data.skills || [];
      fillCategories();
      renderHome();
    } catch (err) {
      document.querySelector("main").innerHTML = `
        <div class="container state-box" style="padding:4rem 1rem">
          <strong>无法加载 skills 数据</strong>
          <p>${escapeHtml(err.message)}</p>
          <p style="margin-top:1rem">请在终端运行：</p>
          <pre style="text-align:left;background:#fff;padding:1rem;border-radius:12px;display:inline-block">cd ~/Desktop/skills
python3 -m http.server 8765</pre>
          <p style="margin-top:1rem">然后打开 <a href="http://localhost:8765/site/">http://localhost:8765/site/</a></p>
        </div>`;
    }
  }

  init();
})();

/* UI strings + language helpers */
window.SkillCafeI18n = (() => {
  const STR = {
    zh: {
      docTitle: "Skill Café — Agent Skills 目录 | 搜索、浏览、下载",
      docDesc: "Skill Café 精选 Agent Skills 目录：按分类搜索、预览 SKILL.md、一键下载 Zip。覆盖 Cursor、工程、设计、营销与云集成。",
      stripMain: "Skill Café · 精选 Agent Skills",
      stripSub: "搜索 · 热门 · 一键下载",
      brandSub: "本地技能目录",
      navExplore: "探索",
      navHot: "热门",
      navRecent: "最近",
      browseAll: "浏览全部",
      search: "搜索",
      menu: "菜单",
      heroBadge: "Agent Skills 目录",
      heroTitle1: "像点单一样，",
      heroTitle2: "找到下一个 Skill",
      startExplore: "开始探索",
      viewHot: "查看热门",
      askLabel: "AI 点单",
      askSectionTitle: "AI 点单",
      askGreeting: "想点什么？",
      askSectionSub: "用一句话说需求，优先匹配站内 skill；没有再帮你联网找",
      askPh: "今天想让 Skill 帮你做什么？",
      askHint: "Enter 发送 · Shift+Enter 换行",
      askSend: "发送",
      askSearching: "正在理解需求并搜索站内 skills…",
      askModeLocal: "Café 现货",
      askModeWeb: "站外发现",
      askEmpty: "站内暂无匹配，已尝试联网搜索。",
      askError: "请求失败",
      askNeedServer: "需要启动后端 API：cd ~/Desktop/skillsServer && npm start（前端保持 http://localhost:8765/site/）",
      askView: "查看",
      askSources: "来源",
      askWebOpen: "打开来源",
      askTipVideo: "做视频",
      askTipReview: "代码审查",
      askTipCommit: "写 commit",
      askTipFigma: "Figma 转代码",
      askClear: "退出点单",
      askPagePrev: "上一页",
      askPageNext: "下一页",
      askPageMeta: "第 {page}/{total} 页 · 共 {count} 个",
      askMatchMeta: "AI 点单",
      trustSkills: "skills",
      trustCats: "分类",
      trustHot: "热门 Top",
      todaySpecial: "今日特调",
      todaySpecialDesc: "覆盖 Cursor、工程方法论、设计、营销与云集成的精选技能包。",
      browseByCat: "按分类逛",
      browseByCatSub: "点一下即可进入全部页筛选",
      hotPicks: "热门精选",
      hotPicksSub: "安装量 × 新鲜度加权",
      viewMore: "查看更多",
      recentUpdates: "最近更新",
      recentSub: "刚烘焙出炉",
      allRecent: "全部最近",
      tabAll: "全部",
      tabHot: "热门",
      tabRecent: "最近更新",
      searchPh: "搜索 skill 名称、描述、分类…",
      allCats: "全部分类",
      sortHot: "按热门",
      sortRecent: "按最近更新",
      sortName: "按名称",
      loading: "加载中…",
      emptyTitle: "没有找到相关 skill",
      emptyHint: "试试别的关键词，或清空筛选。",
      loadMore: "加载更多",
      found: "找到",
      skillsUnit: "个 skill",
      showing: "显示",
      shownOf: "已显示",
      totalOf: "共",
      items: "条",
      view: "查看",
      download: "下载",
      hot: "热门",
      installs: "installs",
      updated: "更新",
      files: "文件",
      previewLabel: "SKILL.md 预览",
      loadingPreview: "加载预览…",
      downloadZip: "下载 Zip",
      downloadMd: "仅 SKILL.md",
      close: "关闭",
      footerAbout: "About",
      footerBrowse: "Browse",
      footerAll: "全部 Skills",
      footerInstall: "Install",
      footerTagline: "像点单一样找 Skill",
      footerInstallPrefix: "下载后复制到",
      footerInstallOr: "或项目",
      footerInstallText: "下载后复制到 ~/.cursor/skills/ 或项目 .cursor/skills/。",
      updatedAt: "更新于",
      langZh: "中文",
      langEn: "EN",
      done: "完成",
      dlDone: "下载完成",
      zipDone: "打包完成",
      dlFail: "下载失败",
      filesUnit: "个文件",
      cat: {
        "01-cursor-native": "Cursor 原生能力",
        "02-workflow-git": "Git / PR / 工作流",
        "03-code-quality": "代码质量 / 安全 / Review",
        "04-frontend-ui": "前端 / UI / 设计",
        "05-testing": "测试 / QA",
        "06-devops-infra": "DevOps / 基础设施",
        "07-docs-office": "文档 / Office / 内容",
        "08-research-web": "调研 / 联网 / 搜索",
        "09-analytics": "分析 / 可观测 / 监控",
        "10-payments-auth": "支付 / 认证",
        "11-planning": "规划 / 架构",
        "12-meta": "Skill 创作 / Meta",
        "13-integrations": "厂商集成 / 平台",
        "14-finance": "金融 / 投资",
        "99-misc": "其他 / 未分类",
      },
    },
    en: {
      docTitle: "Skill Café — Agent Skills Directory | Search & Download",
      docDesc: "Curated Agent Skills directory: search by category, preview SKILL.md, download Zip. Cursor, engineering, design, marketing, and cloud.",
      stripMain: "Skill Café · Curated Agent Skills",
      stripSub: "Search · Trending · Download",
      brandSub: "Local Skills Directory",
      navExplore: "Explore",
      navHot: "Trending",
      navRecent: "Recent",
      browseAll: "Browse all",
      search: "Search",
      menu: "Menu",
      heroBadge: "Agent Skills Directory",
      heroTitle1: "Order your next",
      heroTitle2: "Skill like coffee",
      startExplore: "Start exploring",
      viewHot: "View trending",
      askLabel: "AI order",
      askSectionTitle: "AI Order",
      askGreeting: "What can I get you?",
      askSectionSub: "Describe what you need in one sentence. We match local skills first, then search the web.",
      askPh: "How can Skill Café help you today?",
      askHint: "Enter to send · Shift+Enter for newline",
      askSend: "Send",
      askSearching: "Understanding your need and searching local skills…",
      askModeLocal: "In stock",
      askModeWeb: "Found elsewhere",
      askEmpty: "Nothing local — tried the web.",
      askError: "Request failed",
      askNeedServer: "Start the API first: cd ~/Desktop/skillsServer && npm start (keep frontend at http://localhost:8765/site/)",
      askView: "View",
      askSources: "Sources",
      askWebOpen: "Open source",
      askTipVideo: "Make video",
      askTipReview: "Code review",
      askTipCommit: "Write commit",
      askTipFigma: "Figma to code",
      askClear: "Clear ask",
      askPagePrev: "Prev",
      askPageNext: "Next",
      askPageMeta: "Page {page}/{total} · {count} skills",
      askMatchMeta: "AI ask",
      trustSkills: "skills",
      trustCats: "categories",
      trustHot: "Trending Top",
      todaySpecial: "Today's special",
      todaySpecialDesc: "Curated packs across Cursor, engineering methods, design, marketing, and cloud integrations.",
      browseByCat: "Browse by category",
      browseByCatSub: "Tap to filter in All",
      hotPicks: "Trending picks",
      hotPicksSub: "Installs × freshness weighted",
      viewMore: "View more",
      recentUpdates: "Recently updated",
      recentSub: "Fresh out of the oven",
      allRecent: "All recent",
      tabAll: "All",
      tabHot: "Trending",
      tabRecent: "Recent",
      searchPh: "Search name, description, category…",
      allCats: "All categories",
      sortHot: "By trending",
      sortRecent: "By recent",
      sortName: "By name",
      loading: "Loading…",
      emptyTitle: "No skills found",
      emptyHint: "Try another keyword, or clear filters.",
      loadMore: "Load more",
      found: "Found",
      skillsUnit: "skills",
      showing: "showing",
      shownOf: "Showing",
      totalOf: "Total",
      items: "",
      view: "View",
      download: "Download",
      hot: "Hot",
      installs: "installs",
      updated: "Updated",
      files: "files",
      previewLabel: "SKILL.md preview",
      loadingPreview: "Loading preview…",
      downloadZip: "Download Zip",
      downloadMd: "SKILL.md only",
      close: "Close",
      footerAbout: "About",
      footerBrowse: "Browse",
      footerAll: "All Skills",
      footerInstall: "Install",
      footerTagline: "Find skills like ordering coffee",
      footerInstallPrefix: "After download, copy into",
      footerInstallOr: "or project",
      footerInstallText: "Copy into ~/.cursor/skills/ or your project's .cursor/skills/.",
      updatedAt: "Updated",
      langZh: "中文",
      langEn: "EN",
      done: "Done",
      dlDone: "Downloaded",
      zipDone: "Packed",
      dlFail: "Download failed",
      filesUnit: "files",
      cat: {
        "01-cursor-native": "Cursor Native",
        "02-workflow-git": "Git / PR / Workflow",
        "03-code-quality": "Code Quality / Security",
        "04-frontend-ui": "Frontend / UI / Design",
        "05-testing": "Testing / QA",
        "06-devops-infra": "DevOps / Infra",
        "07-docs-office": "Docs / Office / Content",
        "08-research-web": "Research / Web / Search",
        "09-analytics": "Analytics / Observability",
        "10-payments-auth": "Payments / Auth",
        "11-planning": "Planning / Architecture",
        "12-meta": "Skill Authoring / Meta",
        "13-integrations": "Integrations / Platforms",
        "14-finance": "Finance / Investing",
        "99-misc": "Misc",
      },
    },
  };

  function detectLang() {
    const saved = localStorage.getItem("skillcafe-lang");
    if (saved === "zh" || saved === "en") return saved;
    const nav = (navigator.language || navigator.userLanguage || "en").toLowerCase();
    return nav.startsWith("zh") ? "zh" : "en";
  }

  let lang = detectLang();

  function t(key) {
    const table = STR[lang] || STR.en;
    const val = table[key] ?? STR.en[key];
    return val == null ? key : val;
  }

  function hasTranslation(key) {
    const table = STR[lang] || STR.en;
    return Object.prototype.hasOwnProperty.call(table, key) || Object.prototype.hasOwnProperty.call(STR.en, key);
  }

  function catLabel(catId, fallback) {
    const table = STR[lang] || STR.en;
    return table.cat?.[catId] || fallback || catId;
  }

  function setLang(next) {
    lang = next === "zh" ? "zh" : "en";
    localStorage.setItem("skillcafe-lang", lang);
    document.documentElement.lang = lang === "zh" ? "zh-CN" : "en";
    applyDom();
    window.dispatchEvent(new CustomEvent("skillcafe:lang", { detail: { lang } }));
  }

  function getLang() {
    return lang;
  }

  function applyDom() {
    document.title = t("docTitle");
    const meta = document.querySelector('meta[name="description"]');
    if (meta) meta.setAttribute("content", t("docDesc"));

    document.querySelectorAll("[data-i18n]").forEach((el) => {
      const key = el.getAttribute("data-i18n");
      if (!hasTranslation(key)) return;
      const val = t(key);
      if (el.hasAttribute("data-i18n-text")) {
        el.textContent = val;
        return;
      }
      const inner = el.querySelector("[data-i18n-text]");
      if (inner) {
        inner.textContent = val;
        return;
      }
      if (!el.querySelector("i, svg")) el.textContent = val;
    });

    document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
      const key = el.getAttribute("data-i18n-placeholder");
      if (!hasTranslation(key)) return;
      const val = t(key);
      el.setAttribute("placeholder", val);
      if ("placeholder" in el) el.placeholder = val;
    });

    document.querySelectorAll("[data-i18n-aria]").forEach((el) => {
      const key = el.getAttribute("data-i18n-aria");
      if (!hasTranslation(key)) return;
      el.setAttribute("aria-label", t(key));
    });

    document.querySelectorAll("[data-set-lang]").forEach((btn) => {
      btn.classList.toggle("active", btn.getAttribute("data-set-lang") === lang);
    });

    const sort = document.getElementById("sortSelect");
    if (sort) {
      const map = { hot: "sortHot", recent: "sortRecent", name: "sortName" };
      sort.querySelectorAll("sl-option").forEach((opt) => {
        const k = map[opt.value];
        if (k) opt.textContent = t(k);
      });
    }
    const cat = document.getElementById("categoryFilter");
    if (cat) {
      const first = cat.querySelector('sl-option[value=""]');
      if (first) first.textContent = t("allCats");
      cat.querySelectorAll("sl-option").forEach((opt) => {
        if (!opt.value) return;
        opt.textContent = catLabel(opt.value, opt.textContent);
      });
    }
  }

  return { t, setLang, getLang, detectLang, applyDom, catLabel, STR };
})();

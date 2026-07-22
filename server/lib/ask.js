const { searchLocal } = require("./search");
const { chat, parseJsonLoose } = require("./bailian");

const LOCAL_MAX = 5;
const CLARIFY_THRESHOLD = 5;
const TOP_FOR_CLARIFY = 5;

async function rewriteQuery(query, clarify) {
  const userContent = clarify
    ? `原始需求：${query}\n用户已选择澄清方向：${clarify}\n请据此收窄关键词。`
    : `用户需求：${query}`;

  const { text } = await chat({
    enableSearch: false,
    messages: [
      {
        role: "system",
        content: `你是 Skill Café 的检索助手。根据用户口语需求，输出 JSON（不要其它文字）：
{"keywords":["中英文检索词",...],"clarify_options":["短标签1","短标签2","短标签3"]}
规则：
- keywords 5～10 个，中英混合，面向 Agent Skill / Cursor skill 目录检索（如 video、remotion、manim、审查、audit）
- 若意图很宽（如「做视频」「写文档」），clarify_options 给 3～5 个互斥短标签；意图已够具体则 clarify_options 可为 []
- 不要编造具体 skill 文件名；不要联网`,
      },
      { role: "user", content: userContent },
    ],
  });

  const parsed = parseJsonLoose(text) || {};
  const keywords = Array.isArray(parsed.keywords)
    ? parsed.keywords.map(String).filter(Boolean).slice(0, 12)
    : [];
  const clarify_options = Array.isArray(parsed.clarify_options)
    ? parsed.clarify_options.map(String).filter(Boolean).slice(0, 5)
    : [];

  // Fallback: tokenize raw query if model failed
  if (!keywords.length) {
    const bits = String(query + " " + (clarify || ""))
      .split(/[\s,，、]+/)
      .filter((t) => t.length >= 2)
      .slice(0, 8);
    keywords.push(...bits);
  }

  return { keywords, clarify_options };
}

async function summarizeLocal(query, skills) {
  const list = skills
    .slice(0, LOCAL_MAX)
    .map(
      (s, i) =>
        `${i + 1}. ${s.title} (${s.name}) — ${s.description_zh || s.description || ""}`
    )
    .join("\n");

  try {
    const { text } = await chat({
      enableSearch: false,
      messages: [
        {
          role: "system",
          content:
            "你是 Skill Café 助手。只能根据给出的站内 skill 列表推荐，禁止编造未列出的 skill，禁止提及联网。用 1～2 句中文说明最匹配的，并点名 skill 名称。",
        },
        {
          role: "user",
          content: `用户需求：${query}\n\n站内检索结果：\n${list}`,
        },
      ],
    });
    return (text || "").trim() || `为你找到 ${skills.length} 个相关 skill，推荐优先看「${skills[0].title}」。`;
  } catch {
    return `为你找到 ${skills.length} 个相关 skill，推荐优先看「${skills[0].title}」。`;
  }
}

async function webFallback(query) {
  const { text, sources } = await chat({
    enableSearch: true,
    forcedSearch: true,
    timeoutMs: 60000,
    messages: [
      {
        role: "system",
        content:
          "Skill Café 站内已无匹配。请联网搜索公开的 Agent Skills / SKILL.md / Cursor skills。优先 GitHub 与公开 skill 目录；返回名称、简介、来源链接。不要假装来自本站。用简洁中文回答。",
      },
      {
        role: "user",
        content: `请搜索与以下需求相关的 Agent Skill：${query}`,
      },
    ],
  });

  const normalizedSources = (Array.isArray(sources) ? sources : [])
    .slice(0, 8)
    .map((s) => ({
      title: s.title || s.site_name || "",
      url: s.url || s.link || "",
    }))
    .filter((s) => s.url);

  return {
    text: (text || "").trim() || "联网搜索未返回有效结果，请换个说法再试。",
    sources: normalizedSources,
  };
}

/**
 * Main ask pipeline.
 * @param {{ query: string, clarify?: string|null }} input
 */
async function ask({ query, clarify = null }) {
  const q = String(query || "").trim();
  const c = clarify ? String(clarify).trim() : null;

  const { keywords, clarify_options } = await rewriteQuery(q, c);
  const searchQuery = c ? `${q} ${c}` : q;
  const hits = searchLocal(keywords, { limit: 20, boostQuery: searchQuery });

  if (hits.length === 0) {
    const web = await webFallback(searchQuery);
    return {
      mode: "web",
      summary: web.text.slice(0, 80),
      keywords,
      clarify_options: [],
      skills: [],
      web: { text: web.text, sources: web.sources },
    };
  }

  // User already clarified → prefer local reply even if many hits
  if (c || hits.length <= CLARIFY_THRESHOLD) {
    const top = hits.slice(0, LOCAL_MAX);
    const summary = await summarizeLocal(searchQuery, top);
    return {
      mode: "local",
      summary,
      keywords,
      clarify_options: [],
      skills: top,
      web: null,
    };
  }

  // Too many hits and no clarify yet
  const options =
    clarify_options.length >= 2
      ? clarify_options
      : ["更具体一点", "偏开发工具", "偏内容创作", "偏自动化"];

  return {
    mode: "clarify",
    summary: `找到 ${hits.length} 个相关 skill，范围有点宽，选一个方向帮你收窄：`,
    keywords,
    clarify_options: options,
    skills: hits.slice(0, TOP_FOR_CLARIFY),
    web: null,
  };
}

module.exports = { ask };

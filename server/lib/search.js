const fs = require("fs");
const path = require("path");

const ROOT = path.join(__dirname, "..", "..");
const SKILLS_JSON = path.join(ROOT, "site", "data", "skills.json");

let cache = null;
let cacheMtime = 0;

function loadSkills() {
  const stat = fs.statSync(SKILLS_JSON);
  if (cache && stat.mtimeMs === cacheMtime) return cache;

  const raw = JSON.parse(fs.readFileSync(SKILLS_JSON, "utf8"));
  const skills = (raw.skills || []).map((s) => {
    const blob = [
      s.name || "",
      s.title || "",
      s.description || "",
      s.description_zh || "",
      s.category_label || "",
      s.category || "",
    ]
      .join(" ")
      .toLowerCase();
    return { ...s, _blob: blob };
  });

  cache = { generated_at: raw.generated_at, total: raw.total, skills };
  cacheMtime = stat.mtimeMs;
  return cache;
}

function tokenize(text) {
  return String(text || "")
    .toLowerCase()
    .split(/[\s,，、|/;；+]+/)
    .map((t) => t.trim())
    .filter((t) => t.length >= 2);
}

/**
 * Score skills against keywords. Higher is better.
 */
function searchLocal(keywords, { limit = 20, boostQuery = "" } = {}) {
  const { skills } = loadSkills();
  const terms = [
    ...new Set([
      ...tokenize(Array.isArray(keywords) ? keywords.join(" ") : keywords),
      ...tokenize(boostQuery),
    ]),
  ];
  if (!terms.length) return [];

  const scored = [];
  for (const s of skills) {
    let score = 0;
    const name = (s.name || "").toLowerCase();
    const title = (s.title || "").toLowerCase();

    for (const term of terms) {
      if (name === term || title === term) score += 12;
      else if (name.includes(term) || title.includes(term)) score += 8;
      if (s._blob.includes(term)) score += 3;
    }

    // light popularity boost
    if (score > 0 && s.hot) score += 1;
    if (score > 0 && typeof s.popularity === "number") {
      score += Math.min(2, Math.log10(s.popularity + 1) / 2);
    }

    if (score > 0) {
      scored.push({
        id: s.id,
        name: s.name,
        title: s.title,
        description: s.description || "",
        description_zh: s.description_zh || "",
        category: s.category,
        category_label: s.category_label || "",
        path: s.path,
        popularity: s.popularity,
        hot: !!s.hot,
        score: Math.round(score * 10) / 10,
      });
    }
  }

  scored.sort((a, b) => b.score - a.score || (b.popularity || 0) - (a.popularity || 0));
  return scored.slice(0, limit);
}

function getStats() {
  const data = loadSkills();
  return { total: data.total, generated_at: data.generated_at };
}

module.exports = { loadSkills, searchLocal, tokenize, getStats, ROOT };

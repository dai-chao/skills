const path = require("path");
const fs = require("fs");
const express = require("express");
const rateLimit = require("express-rate-limit");
const { ask } = require("./lib/ask");
const { getStats, ROOT } = require("./lib/search");
const { getApiKey } = require("./lib/bailian");

// Load server/.env if present (no dotenv dependency)
(function loadDotEnv() {
  const envPath = path.join(__dirname, ".env");
  if (!fs.existsSync(envPath)) return;
  for (const line of fs.readFileSync(envPath, "utf8").split("\n")) {
    const m = line.match(/^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$/);
    if (!m) continue;
    const key = m[1];
    let val = m[2].trim();
    if (
      (val.startsWith('"') && val.endsWith('"')) ||
      (val.startsWith("'") && val.endsWith("'"))
    ) {
      val = val.slice(1, -1);
    }
    if (process.env[key] === undefined) process.env[key] = val;
  }
})();

const app = express();
const PORT = Number(process.env.PORT) || 3000;
const MAX_QUERY_LEN = 200;

app.set("trust proxy", 1);
app.use(express.json({ limit: "16kb" }));

const askLimiter = rateLimit({
  windowMs: 60 * 1000,
  max: 20,
  standardHeaders: true,
  legacyHeaders: false,
  message: { error: "Too many requests, please try again in a minute." },
});

app.get("/api/health", (_req, res) => {
  const stats = getStats();
  res.json({
    ok: true,
    hasApiKey: Boolean(getApiKey()),
    skills: stats.total,
    generated_at: stats.generated_at,
  });
});

app.post("/api/ask", askLimiter, async (req, res) => {
  try {
    const query = String(req.body?.query || "").trim();
    const clarify = req.body?.clarify != null ? String(req.body.clarify).trim() : null;

    if (!query) {
      return res.status(400).json({ error: "query is required" });
    }
    if (query.length > MAX_QUERY_LEN) {
      return res.status(400).json({ error: `query too long (max ${MAX_QUERY_LEN})` });
    }
    if (clarify && clarify.length > MAX_QUERY_LEN) {
      return res.status(400).json({ error: "clarify too long" });
    }

    const result = await ask({ query, clarify: clarify || null });
    res.json(result);
  } catch (err) {
    const code = err.code || "INTERNAL";
    const status =
      code === "NO_API_KEY" ? 503 : code === "TIMEOUT" ? 504 : code === "BAILIAN_HTTP" ? 502 : 500;
    console.error("[/api/ask]", code, err.message);
    res.status(status).json({
      error:
        code === "NO_API_KEY"
          ? "AI 服务未配置密钥，请设置 DASHSCOPE_API_KEY"
          : code === "TIMEOUT"
            ? "AI 请求超时，请稍后重试"
            : "AI 请求失败，请稍后重试",
      code,
    });
  }
});

// Static: site UI
const siteDir = path.join(ROOT, "site");
app.use("/site", express.static(siteDir, { index: "index.html", fallthrough: true }));

// Skill source folders for preview/download (browser resolves ../path from /site/)
const CATEGORY_DIRS = [
  "01-cursor-native",
  "02-workflow-git",
  "03-code-quality",
  "04-frontend-ui",
  "05-testing",
  "06-devops-infra",
  "07-docs-office",
  "08-research-web",
  "09-analytics",
  "10-payments-auth",
  "11-planning",
  "12-meta",
  "13-integrations",
  "14-finance",
  "99-misc",
];
for (const dir of CATEGORY_DIRS) {
  const abs = path.join(ROOT, dir);
  app.use(`/${dir}`, express.static(abs, { fallthrough: true }));
}

// Root redirects (replace Static Site _redirects)
app.get("/", (_req, res) => res.redirect(302, "/site/"));
app.get("/site", (_req, res) => res.redirect(302, "/site/"));
app.get("/favicon.ico", (_req, res) =>
  res.sendFile(path.join(siteDir, "favicon.svg"))
);
app.get("/favicon.svg", (_req, res) =>
  res.sendFile(path.join(siteDir, "favicon.svg"))
);

app.use((err, _req, res, _next) => {
  console.error("[express]", err.message);
  res.status(500).json({ error: "Internal server error" });
});

app.listen(PORT, () => {
  console.log(`Skill Café listening on http://localhost:${PORT}/site/`);
  console.log(`API key configured: ${Boolean(getApiKey())}`);
});

const DEFAULT_MODEL = process.env.BAILIAN_MODEL || "qwen-plus";
const API_URL =
  process.env.DASHSCOPE_API_URL ||
  "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions";

function getApiKey() {
  return process.env.DASHSCOPE_API_KEY || "";
}

/**
 * Call Bailian OpenAI-compatible Chat Completions.
 * @param {object} opts
 * @param {Array} opts.messages
 * @param {boolean} [opts.enableSearch]
 * @param {boolean} [opts.forcedSearch]
 * @param {number} [opts.timeoutMs]
 */
async function chat({
  messages,
  enableSearch = false,
  forcedSearch = false,
  timeoutMs = 45000,
  model = DEFAULT_MODEL,
} = {}) {
  const apiKey = getApiKey();
  if (!apiKey) {
    const err = new Error("DASHSCOPE_API_KEY is not configured");
    err.code = "NO_API_KEY";
    throw err;
  }

  const body = {
    model,
    messages,
    temperature: 0.3,
  };

  if (enableSearch) {
    body.enable_search = true;
    if (forcedSearch) {
      body.search_options = { forced_search: true };
    }
  }

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(API_URL, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
      signal: controller.signal,
    });

    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const msg =
        data?.error?.message || data?.message || `Bailian HTTP ${res.status}`;
      const err = new Error(msg);
      err.code = "BAILIAN_HTTP";
      err.status = res.status;
      throw err;
    }

    const choice = data.choices?.[0]?.message;
    const text = choice?.content || "";
    const sources =
      data.search_info?.search_results ||
      data.output?.search_info?.search_results ||
      [];

    return { text, sources, raw: data };
  } catch (e) {
    if (e.name === "AbortError") {
      const err = new Error("Bailian request timed out");
      err.code = "TIMEOUT";
      throw err;
    }
    throw e;
  } finally {
    clearTimeout(timer);
  }
}

/**
 * Extract JSON object from model output (may be wrapped in markdown fences).
 */
function parseJsonLoose(text) {
  if (!text) return null;
  const trimmed = String(text).trim();
  try {
    return JSON.parse(trimmed);
  } catch (_) {
    /* continue */
  }
  const fence = trimmed.match(/```(?:json)?\s*([\s\S]*?)```/i);
  if (fence) {
    try {
      return JSON.parse(fence[1].trim());
    } catch (_) {
      /* continue */
    }
  }
  const start = trimmed.indexOf("{");
  const end = trimmed.lastIndexOf("}");
  if (start >= 0 && end > start) {
    try {
      return JSON.parse(trimmed.slice(start, end + 1));
    } catch (_) {
      /* continue */
    }
  }
  return null;
}

module.exports = { chat, parseJsonLoose, getApiKey, DEFAULT_MODEL };

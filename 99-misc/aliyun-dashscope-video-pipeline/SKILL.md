---
name: aliyun-dashscope-video-pipeline
description: Aliyun DashScope (Bailian) AI video generation pipeline - text script generation + async video synthesis with polling
---

# 阿里云百炼 AI 视频生成流水线

## 适用场景
通过关键词自动生成短视频完整流程：文本脚本 → 分镜 → 视频生成。

## 推荐模型组合

| 阶段 | 模型 | 接口 | 说明 |
|-------|------|------|------|
| 脚本/分镜 | `qwen-max` | `/compatible-mode/v1/chat/completions` | OpenAI 兼容，返回 JSON 格式化脚本 |
| 图片生成 | `flux-dev` | `/compatible-mode/v1/images/generations` | 文生图，生成分镜预览图 |
| 视频生成 | `wan2.7-t2v-2026-04-25` | `/api/v1/services/aigc/video-generation/video-synthesis` | **最新推荐**：有声视频，多镜头叙事，2-15s，720P/1080P |
| 视频生成(旧版) | `wanx2.1-t2v-plus` | `/api/v1/services/aigc/video-generation/video-synthesis` | 无声视频，5s，720P |
| 任务查询 | - | `/api/v1/tasks/{task_id}` | GET 轮询状态 |

### wan2.7 系列 vs 旧版本关键变化

| 参数 | wan2.7 (`wan2.7-t2v-2026-04-25`) | wanx2.1/wan2.2 系列 |
|------|-----------------------------------|----------------------|
| 分辨率 | `resolution`: `720P` / `1080P` + `ratio`: `16:9` / `9:16` | `size`: `1280*720` |
| 时长 | 文档写 2~15s，实际 **强制输出约 5s** | 固定 5s |
| 多镜头 | prompt 中自然语言描述（如"第1个镜头[0-2秒]..."） | `shot_type: "multi"` + `prompt_extend: true` |
| 声音 | 自动配音（背景音/人声），或传 `audio_url` 对口型 | 无声视频 |
| 水印 | `watermark`: true/false | 支持 |
| 智能改写 | `prompt_extend`: true/false | 支持 |

Base URL: `https://dashscope.aliyuncs.com`

## Headers

```
Authorization: Bearer {api_key}
Content-Type: application/json
X-DashScope-Async: enable   # 视频任务必须加，表示异步调用
```

## 脚本生成 Prompt 设计

系统提示词要求模型返回严格 JSON：
```json
{
  "title": "...",
  "script": "带时间轴口播脚本...",
  "storyboard": [
    {
      "scene": 1,
      "description": "中文画面描述",
      "videoPrompt": "英文AI视频提示词，包含主体/环境/光影/镜头/风格",
      "duration": "0:00-0:05"
    }
  ]
}
```

## 图片生成（分镜预览图）

分镜可以配合 AI 图片生成，让用户在提交视频任务前预览每个镜头的画面效果。推荐使用 `flux-dev` 通过 OpenAI 兼容图片接口：

```json
POST /compatible-mode/v1/images/generations
{
  "model": "flux-dev",
  "prompt": "英文图像描述，包含主体/环境/光影/风格",
  "size": "1024*1024",
  "n": 1
}
```

**Response:**
```json
{
  "data": [
    { "url": "https://dashscope-result-bj.oss-cn-beijing.aliyuncs.com/.../xxx.png?Expires=..." }
  ]
}
```

**注意事项**：
- `flux-dev` 同样需要百炼控制台开通，否则返回 `Model.AccessDenied`
- 返回的 URL 有过期时间（通常几小时），如需长期保存应及时下载到本地
- 建议分镜 `videoPrompt` 和 `imagePrompt` 分开：`videoPrompt` 用于万相视频模型（偏重运动/运镜），`imagePrompt` 用于 `flux-dev`（偏重静态画面/细节）

## 视频生成任务体

### wan2.7 系列（推荐）

```json
{
  "model": "wan2.7-t2v-2026-04-25",
  "input": {
    "prompt": "第1个镜头[0-3秒] 全景：一个年轻人坐在电脑前...第2个镜头[3-6秒] 特写：电脑屏幕上显示收入数据..."
  },
  "parameters": {
    "resolution": "1080P",
    "ratio": "16:9",
    "duration": 15,
    "prompt_extend": true,
    "watermark": false
  }
}
```

**关键参数：**
- `input.prompt`: 视频提示词（多镜头描述文本）
- `parameters.resolution`: `720P` 或 `1080P` (建议默认 1080P)
- `parameters.ratio`: `16:9` (横屏) 或 `9:16` (竖屏/短视频)
- `parameters.duration`: 2~15 秒整数
- `parameters.prompt_extend`: 开启智能改写（推荐）
- `parameters.audio_url`: 可选，传入音频 URL 实现声画同步/对口型
- `parameters.watermark`: 是否添加阿里云百炼水印

**⚠️ 极其重要：** `resolution`/`ratio`/`duration`/`prompt_extend`/`watermark` 必须放在 **独立的 `parameters` 对象** 中，而不是嵌在 `input` 内部。如果放在 `input` 里，参数会被完全忽略（例如 `duration: 15` 不生效，视频默认只有 5 秒）。

### 旧版模型（wanx2.1/wan2.2）

```json
{
  "model": "wanx2.1-t2v-plus",
  "input": { "prompt": "英文提示词" },
  "parameters": {
    "size": "1280*720",
    "duration": 5
  }
}
```

## 异步任务轮询

1. 提交返回 `output.task_id`
2. 每 3-5 秒 GET `/api/v1/tasks/{id}`
3. 状态：`PENDING` → `RUNNING` → `SUCCEEDED`/`FAILED`
4. 成功后 `output.video_url` 获取视频链接

## 纯前端无法实现本地保存

浏览器沙箱限制，React/Vue 前端无法直接写入本地 `output/` 文件夹。如需自动保存视频到本地目录，必须增加 **Node.js 后端代理**。

### 后端代理架构（Express）

```js
// server.js — 代理百炼 API + 自动下载视频
import express from "express";
import fs from "fs";
import path from "path";
import https from "https";

const OUTPUT_DIR = path.join(process.cwd(), "output");
if (!fs.existsSync(OUTPUT_DIR)) fs.mkdirSync(OUTPUT_DIR, { recursive: true });

// 代理路由：/api/chat、/api/video/submit、/api/video/:taskId
// 新增 /api/video/download — 接收 videoUrl，stream 写入 output/
app.post("/api/video/download", async (req, res) => {
  const { videoUrl, filename } = req.body;
  const filePath = path.join(OUTPUT_DIR, filename || `video_${Date.now()}.mp4`);
  const client = videoUrl.startsWith("https:") ? https : http;
  const file = fs.createWriteStream(filePath);
  client.get(videoUrl, (response) => {
    response.pipe(file);
    file.on("finish", () => { file.close(); res.json({ success: true, filePath }); });
  }).on("error", (err) => { fs.unlink(filePath, () => {}); res.status(500).json({ error: err.message }); });
});
app.use("/videos", express.static(OUTPUT_DIR));
```

前端 `api.ts` 中 `BASE_URL` 改为 `http://localhost:3001/api`，所有请求走本地后端。

### 同时启动前后端

```json
{
  "scripts": {
    "server": "node server.js",
    "dev": "concurrently \"npm run server\" \"vite\""
  }
}
```

### 文件流下载注意事项

- 视频 URL 可能是 HTTPS，用 Node.js `https` 模块
- 下载失败要清理半成品文件（`fs.unlink`）
- 后端需处理 CORS，前端 dev server 与后端端口不同

## 模型权限问题（高频）

百炼所有模型都需要在控制台手动「开通」，新账号常遇到 `Model.AccessDenied`。

**推荐默认模型（最大概率已开通）：**
- 脚本：`qwen-plus`（`qwen-max` 通常未开通，需手动点）
- 视频：`wan2.7-t2v-2026-04-25`（视频模型普遍需要单独开通）

**诊断端点模式（推荐实现）**

后端增加 `/api/diagnose`，一键测试所有模型权限：

```js
app.post("/api/diagnose", async (req, res) => {
  const { apiKey } = req.body;
  const results = [];
  for (const model of ["qwen-plus", "qwen-max", "qwen-turbo"]) {
    try {
      await proxyToDashScope("/compatible-mode/v1/chat/completions", {
        method: "POST",
        body: JSON.stringify({ model, messages: [{ role: "user", content: "Hi" }], max_tokens: 5 }),
      }, apiKey);
      results.push({ model, status: "ok" });
    } catch (err) {
      const denied = err.message.includes("AccessDenied");
      results.push({ model, status: denied ? "denied" : "error" });
    }
  }
  // 同理测试视频模型，提交后立即 cancel 避免浪费
  res.json({ results });
});
```

前端展示红绿灯状态，用户一眼知道哪个模型要去控制台开通。

**开通链接**
- 模型广场：`https://bailian.console.aliyun.com/#/model-market`
- 找到对应模型 → 点击「开通」

## 音视频合成

**关键变化（wan2.7 系列）：** `wan2.7-t2v-2026-04-25` 及 `wan2.7-t2v` / `wan2.6-t2v` **自带声音**（背景音乐/人声），无需额外 TTS 配音。只有 `wan2.2` 及更早版本是无声视频。

**旧版模型（wanx2.1/wan2.2 及更早）确实无声，需要补齐：**

| 缺失项 | 补齐方式 | 百炼模型/接口 |
|--------|---------|--------------|
| 配音 | TTS 语音合成 | `cosyvoice-v1` via `/compatible-mode/v1/audio/speech` **或** `MiniMax/speech-2.8-hd` via `/api/v1/services/aigc/multimodal-generation/generation` |
| 字幕 | 生成 SRT 文件 | 后端按分镜时间轴拼接 |
| 合并 | 用户用剪映导入 | 视频 + MP3 + SRT 一键对齐 |

### 方案 A：CosyVoice TTS（OpenAI 兼容接口）

```js
app.post("/api/tts", async (req, res) => {
  try {
    const { apiKey, text, voice = "longxiaochun", folder } = req.body;
    const ttsRes = await fetch(`${DASHSCOPE_BASE}/compatible-mode/v1/audio/speech`, {
      method: "POST",
      headers: { Authorization: `Bearer ${apiKey}`, "Content-Type": "application/json" },
      body: JSON.stringify({ model: "cosyvoice-v1", input: { text }, voice }),
    });

    if (!ttsRes.ok) {
      const errText = await ttsRes.text();
      let parsedErr = errText;
      try { parsedErr = JSON.parse(errText).message || errText; } catch {}
      throw new Error(parsedErr);
    }

    const buffer = Buffer.from(await ttsRes.arrayBuffer());
    if (buffer.length === 0) throw new Error("空音频");

    // 支持按标题分文件夹
    const dir = folder ? path.join(OUTPUT_DIR, sanitizeFolder(folder)) : OUTPUT_DIR;
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
    const filename = `tts_${Date.now()}.mp3`;
    const filePath = path.join(dir, filename);
    fs.writeFileSync(filePath, buffer);

    const relPath = folder ? `${sanitizeFolder(folder)}/${filename}` : filename;
    res.json({ success: true, filePath, filename, url: `/videos/${relPath}` });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});
```

### CosyVoice 完整音色列表

| voice_id | 描述 |
|----------|------|
| `longxiaochun` | 知性女声（默认） |
| `longxiaoxia` | 活泼女声 |
| `longxiaocheng` | 沉稳男声 |
| `longxiaobai` | 温柔女声 |
| `longxiaojing` | 甜美女声 |
| `longxiaomei` | 成熟女声 |
| `longxiaofang` | 亲切女声 |
| `longxiaoshu` | 磁性男声 |
| `longxiaoming` | 阳光男声 |
| `longxiaotong` | 童声 |

### 方案 B：MiniMax TTS（多模态生成接口）

有些用户明确要求走 **阿里云百炼代理的 MiniMax 模型**，而不是原生 CosyVoice。这时走的是多模态生成接口，与 OpenAI 兼容接口完全不同：

**Endpoint**: `POST /api/v1/services/aigc/multimodal-generation/generation`

```json
{
  "model": "MiniMax/speech-2.8-hd",
  "input": {
    "action": "tts",
    "text": "今天是不是很开心呀，当然了！",
    "stream": false,
    "voice_setting": {
      "voice_id": "male-qn-qingse",
      "speed": 1,
      "vol": 1,
      "pitch": 0
    },
    "audio_setting": {
      "sample_rate": 16000,
      "format": "mp3",
      "channel": 1
    }
  }
}
```

**关键区别：**
- 接口路径是 `multimodal-generation/generation`，不是 `audio/speech`
- 参数结构是 `{ model, input: { action, text, voice_setting, audio_setting } }`，不是 `{ model, input: { text }, voice }`
- 音色 ID 命名规范与 CosyVoice 完全不同（`male-qn-qingse` vs `longxiaochun`）

**MiniMax 常见音色 ID**（基于命名规范推测，需要测试确认）：
- `male-qn-qingse` / `female-qn-qingse` — 青涩
- `male-qn-jingying` / `female-qn-jingying` — 精英
- `male-qn-badao` / `female-qn-badao` — 霸道
- `male-qn-daxuesheng` / `female-qn-daxuesheng` — 大学生

建议前端音色选择器同时提供「自定义 voice_id」输入框，防止某些 ID 不存在。

### MiniMax TTS 返回格式（已验证）

通过实际调用测试，阿里云百炼代理的 Minimax TTS 返回格式如下：

```json
{
  "output": {
    "base_resp": {
      "status_code": 0,
      "status_msg": "success"
    },
    "data": {
      "audio": "4944330400000000086a545858580000083d00000341494743..."
    }
  }
}
```

**解析要点：**
- 成功标志：`output.base_resp.status_code === 0`（注意不是 HTTP 200 判断，而是 JSON 内部状态码）
- 音频数据：`output.data.audio` 是 **base64 编码的 MP3**
- base64 内容以 `494433...` 开头（MP3 ID3 标签的 hex），可直接 `Buffer.from(audio, "base64")` 解码
- **不是** `output.choices[0].message.content` 格式，也不是直接返回音频二进制

后端解析代码：

```js
const data = await res.json();

// 先检查内部状态码
if (data.output?.base_resp?.status_code !== 0) {
  throw new Error(data.output?.base_resp?.status_msg || "TTS failed");
}

// 提取 base64 音频
const audioBase64 = data.output?.data?.audio;
if (!audioBase64) {
  throw new Error("Missing audio data in response");
}

const buffer = Buffer.from(audioBase64, "base64");
fs.writeFileSync("voiceover.mp3", buffer);
```

### 权限注意

`cosyvoice-v1` 和 `MiniMax/speech-2.8-hd` 均需要百炼控制台手动开通，否则返回 `Model.AccessDenied`。

## 试听模式
```

### SRT 字幕生成

按分镜 `duration` 字段解析时间轴，每段分镜生成一条字幕。后端接口同样支持 `folder` 参数：

```
1
00:00:00,000 --> 00:00:05,000
第一句口播

2
00:00:05,000 --> 00:00:10,000
第二句口播
```

前端通过 Blob + `<a download>` 触发浏览器自动下载 `.srt` 文件。

### 按标题分文件夹输出

用户常要求「每个视频放一个文件夹，文件夹名是视频标题」：

```
output/
├── 怎样扩展自己的额外收入/
│   ├── video_abc123.mp4
│   ├── tts_123456.mp3
│   └── subtitle_789.srt
```

实现：
1. `sanitizeFolder()` 替换非法字符 `\ / : * ? " < > |` 和空格为下划线
2. 视频下载、TTS、字幕三个接口都接受 `folder` 参数
3. `/api/videos` 递归扫描子目录，返回每个文件的 `folder` 路径

```js
function sanitizeFolder(name) {
  return name.replace(/[\\/:*?"<>|]/g, "_").replace(/\s+/g, "_").replace(/_+/g, "_").trim();
}
```

**为什么不用 FFmpeg 自动合成？** 用户环境通常没有 FFmpeg，且剪映导入视频+音频+SRT 的对齐体验比命令行更可控。如果用户明确要求全自动合并，再引入 `fluent-ffmpeg` 或 `ffmpeg-static`。

### 权限注意

`cosyvoice-v1` 同样需要百炼控制台手动开通，否则返回 `Model.AccessDenied`。

## 常见坑

- 文本模型用 `compatible-mode/v1` 路径，视频模型用 `api/v1` 路径，不要混
- 视频提交必须带 `X-DashScope-Async: enable`
- 视频生成约 1-3 分钟，前端需要轮询等待 UI
- qwen 返回的内容可能包含 markdown 代码块，需要提取 JSON
- JSON.parse 失败时要有 fallback，避免整个流程崩溃
- 如果用户说"服务我来启动"，不要帮他长期占着端口，改完代码就停掉服务

### 改了 server.js 必须重启后端（高频踩坑）

**问题现象**：前端选15秒，生成的视频还是5秒；或新加的接口404；或新功能不生效。

**根本原因**：Node.js 进程一旦启动就常驻内存，修改 `server.js` 后旧进程仍在运行旧代码。

**正确做法**：
```bash
# 1. 先杀掉所有旧进程
pkill -f "node server.js"

# 2. 确认端口已释放
lsof -i :3001

# 3. 重新启动
node server.js
```

**用 `npm run dev` / `concurrently` 启动时**：

`npm run dev` 会同时启动后端 + 前端。按 `Ctrl+C` 停止时 `concurrently` 有时候杀不干净子进程，导致新代码不生效。稳妥做法：

```bash
# 先全部杀掉
pkill -f "node server.js"
pkill -f "vite"

# 重新启动
npm run dev
```

**终端工具注意事项**：此环境的 terminal 工具对长驻进程（vite dev、node server）有拦截行为。
- 前台启动超时会被强制终止
- `background=true` 启动的进程可能异常退出
- 建议用户自己在本地终端用 `node server.js` 长期运行

### 时长不对（选了15秒出来5秒）排查指南

从前端到阿里云 API 逐层确认：

1. **请求体结构是否正确**（最常见）：确认 `resolution`/`ratio`/`duration`/`prompt_extend`/`watermark` 等参数在 **独立的 `parameters` 对象** 中，而不是嵌在 `input` 里面。这是最容易被忽视的原因——它们放在 `input` 内时会被服务端完全忽略，导致 `duration: 15` 不生效（默认只有5秒）。
2. **前端选择器**：`duration` 是 Number 类型，确认传给 `submitVideoTask` 的是数字15
3. **API 层 (`api.ts`)**：`submitVideoTask()` 的 `duration` 参数正确拼到 POST body
4. **后端 (`server.js`)**：确认进程已重启，在 `/api/video/submit` 中加日志打印最终请求体
5. **模型版本**：确认是 `wan2.7-t2v-2026-04-25` 或 `wan2.7-t2v`，而不是 `wan2.5-t2v-preview`（只支持5s/10s）或 `wan2.2-t2v-plus`（只支持5s）
6. **多镜头提示词冲突**：如果 `multiScenePrompt` 里写的镜头总时长只有8秒，模型可能按提示词生成而非 API 参数
7. **以上全部确认无误后，还是5秒**：如果请求体结构正确、模型版本对、参数全部在 `parameters` 中，仍然只有5秒，可能是 **该模型实例本身的限制**，需联系阿里云确认。

## 多镜头叙事生成（Multi-Scene Prompt）

`wan2.7` 系列模型支持通过自然语言描述多镜头切换，而非传统单镜头提示词。这是**推荐做法**，画面连贯性和叙事感远优于单镜头拼接。

### 官方示例格式

```
展现未来科技与自然和谐共存的美好愿景。 第1个镜头[0-2秒] 未来城市的空中花园全景，悬浮植物在微风中摇曳。 第2个镜头[2-4秒] 机器人园丁正在精心修剪植物，动作精准而优雅。 第3个镜头[4-7秒] 阳光透过透明穹顶洒下，照亮整个花园，展现科技与自然的完美融合。 第4个镜头[7-10秒] 镜头拉远，展现整个未来城市的壮观景象，空中花园只是其中的一部分。
```

### 前端数据模型改造

```ts
export interface ScriptResult {
  title: string;
  script: string;
  storyboard: Array<{
    scene: number;
    description: string;
    videoPrompt: string;
    duration: string;
  }>;
  multiScenePrompt: string;  // 新增：直接传给视频模型的多镜头描述
}
```

### System Prompt 设计

要求大模型同时输出分镜数组和多镜头描述文本：

```
请严格按照以下JSON格式返回：
{
  "title": "...",
  "script": "...",
  "storyboard": [...],
  "multiScenePrompt": "主题句。 第1个镜头[0-2秒] 画面描述。 第2个镜头[2-4秒] 画面描述。..."
}

关于 multiScenePrompt 的要求：
1. 格式：先写一句总体主题，然后用「第N个镜头[开始-结束秒] 画面描述」列出每个镜头
2. 每个镜头的描述必须包含：画面主体、环境、光影、镜头运动、氛围
3. 镜头数量为${sceneCount}个，总时长不超过15秒
4. 语言风格要具有电影感、绘画感，适合短视频平台
5. 这段文本将直接传给 wan2.7 模型生成多镜头视频
```

### UI 交互设计

1. **配置栏新增镜头数量选择器**（1~6个镜头下拉框），随其他模型参数一起配置
2. **脚本展示区分两块**：
   - **多镜头视频提示词**（蓝色高亮主区域）：展示 AI 生成的 `multiScenePrompt`，用户可直观看到最终传给视频模型的内容
   - **分镜参考**（灰色弱化次区域）：保留 `storyboard` 数组展示，仅作阅读参考，不再支持点击选择单镜头
3. **视频生成按钮**：直接使用 `multiScenePrompt` 提交，无需用户选择单个分镜

### 代码实现要点

```ts
// api.ts — 生成脚本时传入 sceneCount
export async function generateScript(
  apiKey: string,
  keyword: string,
  model = "qwen-plus",
  sceneCount = 4           // 新增参数
): Promise<ScriptResult> { ... }

// App.tsx — 视频生成逻辑
const prompt = script.multiScenePrompt || script.storyboard.map((s) => s.videoPrompt).join("; ");
const taskId = await submitVideoTask(apiKey, prompt, videoModel, ...);

// 移除旧的 selectedScene 单分镜选择逻辑
// const [selectedScene, setSelectedScene] = useState<number | null>(null);  // 删除
```

### 为什么不再让用户选单镜头？

- `wan2.7` 原生支持多镜头叙事，单镜头提示词反而浪费了模型能力
- 多镜头描述的连贯性由模型内部处理，比前端拼接多个独立提示词更自然
- 用户只需要控制「镜头数量」这个创作参数，其余交给 AI

## 多任务队列 + 刷新不丢失

前端同时提交多个视频任务，刷新页面后未完成任务不丢失。实现要点：

1. **localStorage 存未完成任务**：只存 `PENDING`/`RUNNING` 状态的任务，完成后立即移除，避免无限墨水
2. **finishedTasks React state**：任务完成后从 localStorage 删除，但保留在内存中的「已完成」列表，页面关闭后丢失（视频文件已持久化在 output/）
3. **每个任务独立轮询**：`Promise.all(tasks.map(...))` 每 4 秒同时查询所有未完成任务
4. **视频完成后自动下载**：后端代理自动下载视频到 output/

## 每个任务的独立 TTS 进度

> **注意：** `wan2.7` 及 `wan2.6` 系列视频模型**自带声音**（背景音、人声、音效），**无需 TTS 配音**。只有 `wanx2.1` / `wan2.2` 等旧版无声模型才需要以下配音流程。

对于旧版无声模型，配音不是全局的，而是关联到每个视频任务卡片：

```ts
interface TaskItem extends VideoTask {
  prompt: string;
  title: string;
  script: string;        // 口播脚本，用于 TTS
  createdAt: number;
  localFile?: string;
  // TTS 状态（仅旧版无声模型需要）
  ttsStatus?: "idle" | "running" | "succeeded" | "failed";
  ttsUrl?: string;
  ttsError?: string;
  ttsVoice?: string;     // 每个任务可独立选音色
  subtitleUrl?: string;
}
```

**前端流程（旧版无声模型）：**
1. 脚本区域：选择全局默认音色 → 点击「试听」预览
2. 每个任务卡片：视频完成后显示 TTS 区域
3. 可单独修改该任务的音色 → 「试听」 → 「生成配音」
4. TTS 进度状态（running / succeeded / failed）实时显示在卡片上

## 环境限制

- Node 18 无法运行 `create-vite@latest`（需要 Node 20+），应使用 `npm create vite@4`
- 此环境中的 terminal 工具会拦截长期运行进程（vite dev/build），需用 `background=true`

# Skill Café

星巴克风格的 Agent Skills 目录站，支持浏览、下载，以及「AI 点单」自然语言找 skill。

## 推荐启动方式（含 AI）

需要 Node 18+，以及阿里云百炼 API Key（仅放服务端）：

```bash
cd ~/Desktop/skills/server
cp .env.example .env   # 编辑填入 DASHSCOPE_API_KEY
npm install
npm start
```

打开：http://localhost:3000/site/

- 健康检查：`/api/health`
- AI 点单：首页输入框，或 `⌘/Ctrl+J`

> 纯静态预览（无 AI）仍可用：`cd ~/Desktop/skills && python3 -m http.server 8765` → http://localhost:8765/site/

## 功能

- 搜索（名称 / 描述 / 分类）
- 分类筛选与排序、热门 / 最近更新
- 预览 `SKILL.md`、下载 Zip / MD
- **AI 点单**：口语需求 → 站内优先检索 → 过宽则澄清 → 无命中再联网（百炼 `qwen-plus`）

## Render 部署

仓库已含 [`render.yaml`](../render.yaml)。在 [Render Dashboard](https://dashboard.render.com/)：

1. **New → Blueprint**，连接本仓库并应用；或 **Web Service**（Root Directory 留空 / 仓库根，**不要**填 `server`）
2. Build Command: `cd server && npm install`；Start: `cd server && npm start`
3. Environment 添加密钥（Secret）：

   - `DASHSCOPE_API_KEY` = 你的百炼 Key

4. 部署完成后访问 `https://<你的服务>.onrender.com/site/`

免费档 Web Service 有冷启动，首次请求可能稍慢。

从旧的 **Static Site** 迁过来时：停用旧静态站，改用上述 Web Service（预览/下载与 API 需同一进程）。

## UI 栈

- 设计：Starbucks 色板（`星巴克.md`）
- 组件：[Shoelace](https://shoelace.style/)
- 图标：[Lucide](https://lucide.dev/)
- 后端：Express（见 [`../server`](../server)）

## 结构

```
skills/
  server/           # Express：静态托管 + /api/ask
  site/             # 前端
    index.html
    css/styles.css
    js/app.js
    data/skills.json
  01-…/99-misc/     # skill 源文件
  render.yaml
```

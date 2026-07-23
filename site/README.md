# Skill Café

星巴克风格的 Agent Skills 目录站，支持浏览、下载，以及「AI 点单」自然语言找 skill。

## 本地启动（前后端分离）

需要 Node 18+（后端），以及阿里云百炼 API Key（仅放服务端）。

**终端 1 — 后端 API**（`~/Desktop/skillsServer`）

```bash
cd ~/Desktop/skillsServer
cp .env.example .env   # 编辑填入 DASHSCOPE_API_KEY
npm install
npm start
```

**终端 2 — 前端静态站**

```bash
cd ~/Desktop/skills
python3 -m http.server 8765
```

打开：http://localhost:8765/site/

- 顶栏：**探索**（AI 点单）· **全部**（浏览 / 热门 / 最近）
- 健康检查：http://localhost:3000/api/health
- AI 点单：首页「想点什么」，或 `⌘/Ctrl+J`
- 探索页：按分类逛 / 热门精选 / 最近更新
- 后端切换：改 `site/js/app.js` 里的 `API_TARGET`（`"local"` / `"remote"`）；也可用 `window.SKILL_CAFE_API = "..."` 临时覆盖

> 不启后端也能浏览 / 下载，只是 AI 点单不可用。

## 功能

- 搜索（名称 / 描述 / 分类）
- 分类筛选与排序、热门 / 最近更新
- 预览 `SKILL.md`、下载 Zip / MD
- **AI 点单**：口语需求 → 站内优先检索 → 过宽则澄清 → 无命中再联网（百炼 `qwen-plus`）

## Render 部署

后端在并列目录 [`skillsServer`](../../skillsServer)（本地 `~/Desktop/skillsServer`）。静态站与 API 可分开部署；API 需设置：

- `DASHSCOPE_API_KEY`
- `SKILLS_ROOT`（指向本仓库检出根目录）
- `CORS_ORIGIN`（前端站点 Origin）

详见 `skillsServer/README.md`。

## UI 栈

- 设计：Starbucks 色板（`星巴克.md`）
- 组件：[Shoelace](https://shoelace.style/)
- 图标：[Lucide](https://lucide.dev/)
- 后端：Express API（见 `~/Desktop/skillsServer`）

## 结构

```
Desktop/
  skills/           # 本仓库：前端 + skill 源文件
    site/
    01-…/99-misc/
    render.yaml
  skillsServer/     # Express：仅 /api/*
```

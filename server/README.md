# Skill Café server

Express 服务：托管 `site/` 静态页 + `/api/ask` AI 点单。

## 本地启动

```bash
cd server
cp .env.example .env   # 填入 DASHSCOPE_API_KEY
npm install
npm start
```

浏览器打开：http://localhost:3000/site/

健康检查：http://localhost:3000/api/health

## 环境变量

| 变量 | 必填 | 说明 |
|------|------|------|
| `DASHSCOPE_API_KEY` | 是（AI 功能） | 阿里云百炼 API Key |
| `BAILIAN_MODEL` | 否 | 默认 `qwen-plus` |
| `PORT` | 否 | 默认 `3000`（Render 会自动注入） |

也可不建 `.env`，直接：

```bash
DASHSCOPE_API_KEY=sk-xxx npm start
```

## API

`POST /api/ask`

```json
{ "query": "做视频", "clarify": null }
```

返回 `mode`: `local` | `clarify` | `web`。

流水线：改写关键词 → 站内检索 → 命中则推荐/澄清；0 命中再联网（`enable_search`）。

## Render 部署

见仓库根 [README](../site/README.md) 或根目录 `render.yaml` Blueprint。

Dashboard：https://dashboard.render.com/

1. New → Blueprint 选本仓库，或 New Web Service（**不要**把 Root Directory 设为 `server`，否则读不到技能文件）
2. Build: `cd server && npm install` / Start: `cd server && npm start`
3. Environment 添加 `DASHSCOPE_API_KEY`

# Hermes 记忆核心导出模板

使用说明：将此模板作为 `hermes-memory-core.md` 的基础，填充 `MEMORY.md` 与 `USER.md` 的原文，并记录导出时间即可。

```markdown
# <用户名> - Hermes 记忆核心导出

导出时间: YYYY-MM-DD HH:MM:SS
来源机器: <hostname>
Hermes Home: ~/.hermes

---

## 一、个人记忆 (MEMORY.md)

<粘贴 ~/.hermes/memories/MEMORY.md 全文>

---

## 二、用户画像 (USER.md)

<粘贴 ~/.hermes/memories/USER.md 全文>

---

## 三、迁移说明

1. 在新电脑安装 Hermes Agent 后，把当前 `.hermes/memories/` 目录下的 `MEMORY.md` 和 `USER.md` 复制过去。
2. 如果新账号/新机器的人格文件 (`SOUL.md`) 为空，可把旧机器上的 `~/.hermes/SOUL.md` 一并复制。
3. 以下路径还包含自定义技能、cron 任务、频道状态，换机器时建议整体备份 `.hermes` 目录：
   - `~/.hermes/skills/` — 自定义技能
   - `~/.hermes/cron/` — 定时任务
   - `~/.hermes/config.yaml` — 模型/工具配置
   - `~/.hermes/memories/` — 核心记忆
4. 敏感凭证（API Key、token）通常存放在 `~/.config/` 或 `.env` 中，请另行手动迁移，不要随普通备份扩散。

---
EOF
```

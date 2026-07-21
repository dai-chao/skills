# 43漫画 — 安装与激活指南

> **版本：** 0.3.0

## 概览

**推荐用法**：把 **SKILL.md 的 HTTPS 地址** 发给 Agent，它会自动拉取本目录全部文件并完成安装。

```
https://comic.43music.vip/agentApi/skills/SKILL.md
```

安装后 Agent 会提示绑定；用户在小程序「我的 → Agent 接入」复制 **激活码** 发给 Agent 即可。

完整对话式流程见 `SKILL.md` 开头「对话式使用」章节。

---

## 从 URL 自动安装（Agent 执行）

用户发来 `.../skills/SKILL.md` 时，从 URL 推导 `SKILLS_BASE`（即 `.../skills`），然后：

```bash
SKILL_DIR="${SKILL_DIR:-$HOME/.hermes/skills/43comic}"
SKILLS_BASE="https://comic.43music.vip/agentApi/skills"

mkdir -p "$SKILL_DIR"
curl -sL "$SKILLS_BASE/skill.json"     -o "$SKILL_DIR/skill.json"
curl -sL "$SKILLS_BASE/SKILL.md"       -o "$SKILL_DIR/SKILL.md"
curl -sL "$SKILLS_BASE/INSTALL.md"     -o "$SKILL_DIR/INSTALL.md"
curl -sL "$SKILLS_BASE/GENERATION.md"  -o "$SKILL_DIR/GENERATION.md"
```

### 安装自检

```bash
for f in skill.json SKILL.md INSTALL.md GENERATION.md; do
  [ -f "$SKILL_DIR/$f" ] || { echo "MISSING_$f"; exit 1; }
done
echo "OK"
```

---

## 绑定账号（对话式）

1. Agent 检测 `~/.config/43comic/credentials.json` 是否存在且有效
2. 若未绑定，提示用户打开 **微信小程序「43漫画」→ 我的 → Agent 接入**，复制激活码
3. 用户把 8 位激活码发给 Agent → Agent 调用 `comic.activate` 并保存凭证

```bash
API_BASE="https://comic.43music.vip/agentApi"
ACTIVATION_CODE="用户提供的8位码"

RESP=$(curl -sS -X POST "$API_BASE/comic.activate" \
  -H "X-Activation-Code: $ACTIVATION_CODE")

mkdir -p "$HOME/.config/43comic"
echo "$RESP" | jq '{
  comicToken: .comicToken,
  apiBase: .apiBase,
  userId: .userId,
  nickName: .nickName,
  activatedAt: (now | floor)
}' > "$HOME/.config/43comic/credentials.json"
```

凭证文件示例：

```json
{
  "comicToken": "eyJ...",
  "apiBase": "https://comic.43music.vip/agentApi",
  "userId": "oXXXX",
  "nickName": "漫画玩家",
  "activatedAt": 1745000000
}
```

### 激活自检

```bash
CRED="$HOME/.config/43comic/credentials.json"
COMIC_TOKEN=$(jq -r .comicToken "$CRED")
API_BASE=$(jq -r .apiBase "$CRED")
curl -sS -H "X-Comic-Token: $COMIC_TOKEN" "$API_BASE/comic.status" | grep -q '"quotaRemaining"' \
  && echo "OK" || echo "AUTH_FAIL"
```

---

## 日常自愈

业务接口返回 HTTP 401 或 `Comic Token 无效`：

```bash
CRED="$HOME/.config/43comic/credentials.json"
COMIC_TOKEN=$(jq -r .comicToken "$CRED")
API_BASE=$(jq -r .apiBase "$CRED")

NEW=$(curl -sS -X POST "$API_BASE/auth.refreshToken" \
  -H "X-Comic-Token: $COMIC_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}')
# 用 jq 更新 comicToken 后重试
```

若 `auth.refreshToken` 也返回 401 → 请用户在小程序确认激活码未重置，重新 `comic.activate`。

---

## 环境变量（可选）

| 变量 | 默认 |
|------|------|
| `COMIC_CREDENTIALS` | `~/.config/43comic/credentials.json` |
| `COMIC_API_BASE` | credentials 内 `apiBase` |

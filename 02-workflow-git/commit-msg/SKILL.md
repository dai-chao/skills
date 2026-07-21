---
name: commit-msg
description: Handles Git commits for any repository. Generates messages from status/diff/log (Chinese-first, matches repo style). On 提交代码/提交并推送, runs full workflow—message, commit, push. On 生成提交信息/写 commit, message only unless user also asks to commit. Use for 提交代码, 提交并推送, 帮我提交, 生成提交信息, commit, push.
---

# Git 提交与推送

## 两种模式

| 用户说法 | 动作 |
|----------|------|
| **提交代码**、提交并推送、帮我提交推送 | **完整流程**：分析 → 写 message → `add` → `commit` → `push` |
| **生成提交信息**、写 commit、commit message | **仅生成**说明（不 `add`/`commit`/`push`，除非用户紧接着要求提交） |

## 完整流程（「提交代码」）

按顺序执行，每步失败则停止并说明原因。

### 1. 分析（并行）

```bash
git status
git diff
git diff --staged
git log --oneline -15
```

- **无变更**：告知 working tree clean，不 commit、不 push
- **有未跟踪/未 stage 文件**：`git add` 仅与本次改动相关的文件；**禁止**提交 `.env`、密钥、`credentials.json` 等

### 2. 生成提交说明

对齐当前仓库 `git log` 风格（见下方「仓库风格」），取一条 **推荐** subject；完整流程中可直接用于 commit，并在回复中简要展示：

```markdown
## 提交说明
<subject>

## 变更摘要
- ...
```

### 3. 提交

```bash
git add <相关文件>   # 若已全部 staged 可跳过
git commit -m "$(cat <<'EOF'
<subject>

<optional body>

EOF
)"
git status
```

hook 失败：修复后 **新建 commit**，不要 `amend`（除非用户明确要求 amend 且满足安全条件）。

### 4. 推送远端

```bash
git push
```

- 当前分支**无 upstream**：`git push -u origin $(git branch --show-current)`
- push 失败：报告错误（权限、冲突、需 pull 等），**不要** `push --force`，除非用户明确要求
- push 到 `main`/`master` 前可简短确认变更摘要（用户已说「提交代码」视为同意推送当前分支）

### 5. 回复用户

汇总：**提交说明**、**commit hash**（`git log -1 --oneline`）、**推送结果**（分支与 remote）。

---

## 仅生成说明（不自动提交）

不执行 `git add` / `git commit` / `git push`。输出：

```markdown
## 推荐
<subject>

## 备选
1. ...
2. ...

## 变更摘要
- ...
```

用户只要一句话时，只给 **推荐** subject。

---

## 仓库风格（以当前仓库 `git log` 为准）

**先读最近 15 条 commit**，对齐语言与长度。

默认（无明确惯例时）：

- **简短中文**：做了什么、为什么，一行为主
- 业务向 → 中文；API/重构且 log 多为英文 → `Refactor` / `Enhance` / `Fix` + 英文祈使句
- 不写 `Merge #xxx`；不罗列文件名；聚焦 **why**
- 单行通常 ≤ 72 字

---

## 安全（必须遵守）

- 不修改 `git config`
- 不用 `--no-verify`、不用 `push --force`（除非用户明确要求）
- 不用 `git commit --amend`，除非：用户明确要求 **且** 上一 commit 是你本会话创建的 **且** 未 push
- 无变更：不空提交、不 push
- 不提交敏感文件

---

## 示例

| 场景 | Subject |
|------|---------|
| 优化逻辑 | `优化教练 TTS 请求超时与重试逻辑，降低流式中断概率` |
| 重构 API | `Refactor Coach Whitelist API to remove 'IsAll' field` |
| 避免 | `update files`、`修改 xxx.go` |

更多见 [examples.md](examples.md).

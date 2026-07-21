# HANDOFF — 2026-07-20

blindspot-finder 仓库当前进度交接。分支 `main`，工作区干净，已全部推送到
`origin`（https://github.com/HeathTeng/blindspot-finder）。

## 已完成

- **v1.2 已发布并推送** —— tag `v1.2`，指向 commit `0e8e17f`
  (`docs: v1.2 roadmap, changelog, sync discipline`)。功能本体在其父 commit
  `30878a6`（HANDOFF.md 生成后追加一行不提问的反馈邀请，指向 GitHub Issues，
  每会话最多一次，不计入问题预算）。
  - 审 diff 时发现英文示范句原以问号结尾，与"这是陈述不是提问"的规则自相
    矛盾（模型跟示范走不跟规则走），已改为陈述句后放行。
  - ROADMAP 候选功能第 7 条已标记「已完成，v1.2」；决策记录已补 2026-07-20 条目。
  - README.md / README.zh-CN.md 的 Changelog 各加一条 v1.2。
  - 新建仓库根目录 `CLAUDE.md`，写入 SKILL.md 三副本同步纪律。
- **test-prompts.json 已进版本库**（3 条用例）—— commit `e0e5088`
  (`test: add eval baseline (3 cases, to expand in v2 prep)`)。
- **design-demos/ 已加入 .gitignore** —— commit `dc8f62c`
  (`chore: ignore design-demos (logo drafts; finals in docs/assets)`)。
  文件仍在本地磁盘，只是不再进版本库。

### SKILL.md 三副本同步纪律（改动时必守）

三份必须完全一致，**以根目录为准**：`SKILL.md`、
`.claude/skills/blindspot-finder/SKILL.md`、`.agents/skills/blindspot-finder/SKILL.md`。
只改根目录那份，复制覆盖另外两份，然后跑：

```bash
diff <(cat SKILL.md) <(cat .claude/skills/blindspot-finder/SKILL.md)
diff <(cat SKILL.md) <(cat .agents/skills/blindspot-finder/SKILL.md)
```

两条都无输出（退出码 0）才算改完。后两份被 gitignore，`git diff` 不会暴露
不一致——漏同步不报错，只会让实际加载的技能与仓库版本悄悄分叉。详见 `CLAUDE.md`。

## 进行中：把 design-demos/ 里的成品文件挪进 docs/

`design-demos/` 完整清单共 16 个文件（比早前一次查看多出 10 个，即带 `10:25`
时间戳的那批，应为之后新导出）。design-demos/ 本身保持忽略状态不变。

### 已点名要挪的 5 个

| 文件 | 去向 |
|---|---|
| `logo-blindspot-finder.png` (116 KB) | docs/assets/ |
| `icon.html` (3.4 KB) | docs/assets/ |
| `banner-zh.html` (3.1 KB) | docs/assets/ |
| `logo-spec.md` (2.6 KB) | docs/design/（目录不存在，需新建） |
| `direction-approved.md` (1.1 KB) | docs/design/（目录不存在，需新建） |

### 剩下 11 个的 A/B/C 三类判断（原样保留）

**A. 看着是成品导出件，但未点名（建议一并挪）：**

- `icon-16.png` / `icon-32.png` / `icon-64.png` / `icon-128.png` /
  `icon-256.png` —— icon.html 的五档尺寸导出。挪了源文件不挪成品有点怪。

**B. 有冲突，需要裁决：**

- `banner-zh.png` (108,944 字节) —— **`docs/assets/banner-zh.png` 已存在且
  不同**（130,703 字节，7 月 17 日）。design-demos 这份更新。是新版要覆盖
  旧版，还是旧版才是定稿？
- `logo-blindspot-finder.html` (9.3 KB) —— 已点名挪 icon.html 和
  banner-zh.html 两个源文件，却没挪 logo 的源文件，而 logo 的 png 要挪。
  看着是漏了。

**C. 确属草稿，留在忽略目录合理：**

- `banner-en-a-demand-lens.png` / `banner-en-b-scope-first.png` —— 英文
  banner 的 A/B 两稿（定稿 `docs/assets/banner-en.png` 已在库里）
- `banner-en-candidates.html` —— 上面两稿的源文件
- `_preview-en-candidates.png` —— 比稿预览图

## 待裁决（阻塞项，需用户拍板）

1. **A 类**：五个 icon 尺寸导出（16/32/64/128/256）是否一并挪进 docs/assets/。
2. **B 类之一**：`banner-zh.png` 新旧两版谁是定稿——design-demos 版
   (108,944 字节，07-20) 覆盖 docs/assets 版 (130,703 字节，07-17)，还是保留旧版。
3. **B 类之二**：`logo-blindspot-finder.html` 源文件是否漏挪、应否一并进
   docs/assets/。

## 下一步

1. 裁决 A / B 后**一次性**完成：挪文件 → 逐个跑 `git check-ignore -v` 确认
   docs/ 下的新文件没被 .gitignore 规则误伤（无输出=未被忽略=正常）→
   commit `chore: promote final logo, banner sources and design records out of design-demos`
   → 推送 main。
2. 之后另起新对话做 **ROADMAP 候选功能第 8 条：评测集扩建** —— 把
   `test-prompts.json` 从 3 条扩到 20–30 条带标准答案的需求发现用例，作为
   后续版本的回归测试基线（ROADMAP 标注其为 v2.0 开工前置任务，可随时启动）。

## 给下一个读到这份文档的 AI

- 本仓库是一个 Claude Code skill（blindspot-finder，需求透镜类 meta-skill），
  主交付物就是 `SKILL.md` 本身，不是应用代码。版本主线：v1 纯指令 →
  v2 结构化配置 → v3 可执行脚本，详见 `ROADMAP.md`。
- **动 SKILL.md 前先读本文档「三副本同步纪律」一节和 `CLAUDE.md`。**
- 上面「待裁决」三项在用户明确答复前不要自行决定，尤其 B 类第一项涉及
  覆盖已在版本库中的 `docs/assets/banner-zh.png`——那是有损操作。
- 用户的工作习惯：改动先看 diff 再决定是否 commit；不要未经要求就 commit
  或 push。

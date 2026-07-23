---
name: skill-visualizer
description: "分析任意Skill 文件夹，生成一份面向初学者的中文「Skill 学习导览」单页 HTML。报告帮助非工程背景的用户快速看懂：这个 Skill 是做什么的、文件夹怎么读、运行时的工作顺序，以及想学习或改造时应该先看哪里。"
---

## 触发关键词

- "visualize this skill"
- "analyze this skill"
- "可视化这个Skill"
- "分析这个Skill"
- "Skill可视化"
- "展示Skill流程"
- "看懂这个Skill"
- "Skill 学习导览"

## 报告定位（最重要，先读这里）

这份报告面向 **Skill 初学者和非工程背景用户**。

报告目标 **不是** 展示复杂技术分析或代码审计，而是帮助用户快速看懂一个 Skill 的：
1. **用途** — 这个 Skill 是干什么的？
2. **结构** — 文件夹里这些文件分别负责什么？
3. **运行流程** — 它运行时按什么顺序工作？
4. **质量与原理** — 它做得好不好？设计原理是什么？（大师视角点评）
5. **改造入口** — 我想学习或改造，应该先看哪里？

### 总体原则（贯穿全程）

1. **全中文**：所有用户可见的标题、按钮、标签、说明文字必须使用中文。
2. **禁止抽象英文术语**：不要出现 Dashboard、Constellation Map、Deep Dive、Interaction Matrix、SLRC、"电梯陈述"、"多模型分析" 等说法。模块标题一律用中文。
3. **不堆信息**：不要为了"展示完整"而堆砌。优先展示对理解 Skill 有帮助的信息，低价值内容折叠或省略。
4. **每个模块都要有明确结论**：先给结论，再给细节。
5. **少图谱，多解释**：少用复杂关系图谱，多用分组、步骤、主链路和直白的中文解释。
6. **直白短句**：语言像一份"学习导览"，不像审计报告。
7. **克制使用表情符号**：整份报告尽量少用 emoji。能用文字徽标、强调短线、颜色区分的地方，就不要用表情符号。确需图标时，每个模块最多点缀 1-2 个，避免满屏花哨。
8. **追求精致美观**：版面要干净、有呼吸感、配色统一协调，像一份精心排版的学习手册。
9. **技术术语必须小白化**：面向非工程背景用户，凡是出现技术词汇都要顺手解释。两种方式：
   - **括号补一句大白话**，例如："元数据（也就是这个 Skill 的'身份信息'，比如名字和描述）"、"依赖（指它运行时要用到的其他文件）"。
   - **用术语提示**：`<span class="term" data-definition="用一句大白话解释这个词">JSON</span>`，鼠标悬停就能看到解释。
   - 常见需要解释的词：JSON、HTML、CSS、脚本、依赖、元数据、骨架、渲染、解析、触发词、参数、字段等。
   - 解释要短、要像跟朋友聊天，不要再用新的术语去解释术语。

## 第一阶段：分析 Skill

读取 Skill 文件夹里的每一个文件。带着"小白会问的 4 个问题"去读，而不是做技术分类穷举。

### 1.1 提炼用途
- 这个 Skill 一句话能说清是干什么的吗？
- 用户在什么场景下会用到它？
- 它最终会产出什么（文件、内容、结果）？

### 1.2 理解文件结构
- 按目录把文件分组：入口文件、references、assets、scripts、config、docs。
- 每个文件属于哪一组？这一组负责什么？
- 哪些是**关键文件**（必看）、**辅助文件**（按需）、**可忽略文件**（基本不用管）？
- 找出最重要的几条引用关系，组成一条**主链路**，例如：
  `SKILL.md → references/*.md → 模板/脚本 → 最终产出`
- 不要追求把所有文件关系都画出来。

### 1.3 梳理运行顺序
把 Skill 的执行过程拆成清晰的几步。每一步都要能回答：
- 这一步**读取**什么？
- 这一步**判断**什么？
- 这一步**产出**什么？
- 涉及**哪些文件**？

### 1.4 定位改造入口
- 想改触发词，应该改哪个文件的哪一部分？
- 想改输出样式，看哪里？
- 想改流程逻辑，看哪里？
- 想加脚本工具，放哪里？
- 哪些改动风险较高（容易改坏）？

## 第二阶段：模块设计

报告由 **6 个中文模块** 组成。每个模块回答一个小白问题，模块标题必须是中文。

---

### 模块 01：这个 Skill 是做什么的（type: `purpose`）

回答"这个 Skill 是干什么的"。内容包括：

- **一句话结论**：直接说明这个 Skill 的用途。放在最显眼的位置（用 `.callout.callout-accent`）。
- **适合场景**：列出用户什么时候应该用它（卡片或清单）。
- **最终产出**：说明它会生成什么文件、内容或结果。
- **学习建议**：告诉新手应该先看哪些部分、按什么顺序。

可以用少量 `.stats-grid` 展示基础信息（文件数、总行数、产出类型），但不要堆砌复杂指标。

> 禁止出现"电梯陈述""SLRC""多模型分析"等抽象说法。

---

### 模块 02：文件结构怎么读（type: `file_structure`）

回答"文件夹里这些文件分别负责什么"。

**不要使用大规模节点星座图作为主展示**（文件多时会乱）。改用 **「文件夹分组 + 主链路」**：

1. **文件夹分组**：用 `.file-tree` 按目录聚合文件（入口、references、assets、scripts、config、docs）。
   - 每组用一句话说明职责。
   - 每个文件标注价值等级：`.value-tag.value-key`（关键）、`.value-tag.value-aux`（辅助）、`.value-tag.value-skip`（可忽略）。
   - 支持点击分组/文件展开查看说明，但不要一次性铺满所有文件关系。
2. **主链路**：用 `.main-chain` 展示最重要的一条引用关系，配明显的大箭头，例如：
   `SKILL.md → references/*.md → 模板/脚本 → 最终产出`

---

### 模块 03：Skill 是怎么运行的（type: `execution_flow`）

回答"它运行时按什么顺序工作"。保留执行流程，但要中文化、教学化。

用 `.flow-timeline` **静态全展示**所有步骤（**不要自动播放、不要播放控件**），每一步写清楚 4 件事：
- **读取**：这一步读取什么
- **判断**：这一步判断什么
- **产出**：这一步产出什么
- **相关文件**：涉及哪些文件（用 `.flow-file-tag`）

**箭头/编号要清晰明显**，避免细小、不明显的连接线。所有步骤一进来就全部可见，用户上下扫一眼即可看懂顺序。

> 不要再生成"上一步/下一步/播放全部/重置"按钮，也不要 `flow-controls`、`flow-progress`、`id="exec-flow"` 这些播放相关结构 —— 这个模块现在是纯静态展示。

---

### 模块 04：核心文件解读（type: `core_file`）

回答"想学习应该先看哪里"。重点解读入口文件（通常是 `SKILL.md`）。

1. **入口文件英雄卡**（`.skill-hero`）：图标 + 文件名 + 一段话说明它**为什么重要**。
2. **文档结构地图**（`.struct-map`）：解析入口文件的 markdown 标题，逐节展示：
   - 每节：中文标题 + 行号范围 + 这一节负责什么。
   - 标注 **必看 / 按需看 / 可跳过**（可用 `.value-tag`）。
   - **结构地图必须中文化**。如果原文 heading 是英文，必须给出中文解释，不能只显示英文 heading。
   - 点击展开查看该节要点。
3. **其他文件概览**：**不要平铺罗列**，必须按价值聚合成分组：
   - 核心入口、规则参考、模板资产、脚本工具、文档与配置。
   - 用 `.file-cards` 展示，每张卡片可展开看摘要。
   - 对用户理解 Skill 没有明显帮助的文件，折叠到 **"辅助文件"** 分组里，**默认不展开**。

> 不需要内容构成饼图、设计原则卡片网格等。保持聚焦。

---

### 模块 05：大师视角分析（type: `master_insights`）

回答"这个 Skill 做得好不好、它的设计原理是什么"。

**结合 Skill 的特点，从下面的大师池里挑选最相关的 3 位**，让他们各自给出直击本质的点评。

| 大师 | 视角 | 适合的 Skill 类型 |
|------|------|------------------|
| 乔布斯 | 产品品味、极致简化、用户体验 | 产品/设计/界面生成类 |
| 马斯克 | 第一性原理、10 倍思考、去除瓶颈 | 工程/自动化/流水线类 |
| 查理·芒格 | 多元思维、逆向思考、护城河 | 复杂多文件/框架类 |
| 费曼 | 化繁为简、教学相长、分层讲解 | 教学/文档类 |
| 保罗·格雷厄姆 | 做不可规模化的事、先简单、写作即思考 | 内容生成/创意类 |
| 纳瓦尔 | 杠杆、专属知识、长期复利 | 自动化/知识沉淀类 |
| 塔勒布 | 反脆弱、凸性、林迪效应、尾部风险 | 基础设施/长生命周期工具 |
| 张一鸣 | 数据驱动迭代、推荐、理解用户 | 数据分析/个性化类 |

**挑选规则（结合 Skill 特点自动判断，带一点随机性）**：
- 生成视觉/HTML/图表 → 乔布斯 + 费曼
- 多阶段复杂流水线 → 马斯克 + 芒格
- 单文件/极简 → 格雷厄姆 + 乔布斯
- 数据/分析 → 芒格 + 塔勒布
- 教学/文档 → 费曼 + 格雷厄姆
- 至少保留 1 位"唱反调"的（塔勒布或芒格的逆向视角），避免一味夸奖。
- 在符合上面规则的前提下，可在候选大师中随机替换 1 位，让每次报告视角略有不同。

**每位大师的卡片必须包含**：
1. **一句话定论**（`.perspective-verdict`）：用该大师的口吻，直击本质地总结对这个 Skill 的看法。
2. **2-4 条要点**（`.perspective-points`）：每条用 **文字徽标**（不要用表情符号）标明类型：
   - `<span class="point-label point-good">亮点</span>` — 做得好的地方
   - `<span class="point-label point-warn">警示</span>` — 需要注意/做得不好的地方
   - `<span class="point-label point-core">本质</span>` — 设计原理 / 它为什么这样设计
   - `<span class="point-label point-idea">建议</span>` — 改进方向

**如果这个 Skill 设计质量较高**：要直白地讲清它的**设计原理**——它好在哪、为什么这么设计、用了什么巧思（多用「本质」徽标）。不要为了平衡而硬找缺点。

**交互**：每位大师是一张可折叠卡片（`.perspective-card`，点击 `.perspective-header` 展开/折叠，调用 `togglePerspective(this)`），第一张默认展开。头像（`.perspective-avatar`）用大师姓氏首字（如"乔""马""芒"）而非表情符号。

结尾用一个 `.callout.callout-accent.consensus` 写一句**共识结语**：几位大师都认同的、关于这个 Skill 最重要的一点。

> 这是用户主动要求保留的模块。点评要言之有物、直击本质，避免空泛套话。

---

### 模块 06：学习路线与改造建议（type: `learning_path`）

回答"我想改造应该从哪下手"。**替代原来的交互矩阵和过度复杂的分析模块。**

必须告诉用户：
- **新手阅读顺序**：建议按什么顺序读文件（用 `.roadmap` 带编号步骤）。
- **改造入口对照表**（用 `.principle-grid` 卡片，每张回答"想做 X → 看哪里"）：
  - 想改触发词 → 看哪里
  - 想改输出样式 → 看哪里
  - 想改流程逻辑 → 看哪里
  - 想添加脚本工具 → 看哪里
- **高风险改动提醒**：哪些改动风险较高，用 `.callout.callout-warning` 标出。

> 不要生成文件交互热力图。

---

### 已删除 / 弱化的内容（不要再生成）

- ❌ 交互矩阵（Interaction Matrix）/ 文件交互热力图 — 删除。
- ❌ 大规模文件节点星座图 — 弱化，改用分组 + 主链路。
- ❌ 内容构成饼图、设计原则网格 — 删除。
- ❌ 所有英文模块标题 — 改为中文。
- ❌ 低价值配置文件的详细展示 — 折叠到辅助文件。

## 第三阶段：构建 HTML

### 输出文件命名

```
skill-viz-output/{skill-name}-学习导览.html
```
使用 Skill 元数据里的 `name` 字段；若没有则用文件夹名。

### ⭐ 构建方式：JSON 数据 + 构建脚本（必须用这个）

HTML 文件通常 60KB+，**一次性写完会失败**。你只需生成一个 5-15KB 的 `skill-data.json`，构建脚本会自动把固定的 CSS/JS 骨架 + 你的数据拼成完整 HTML。

**第一步**：生成 `skill-data.json`（schema 见 `scripts/build-report.py` 文件末尾注释）：
```json
{
  "name": "Skill 名称",
  "total_files": 4,
  "total_lines": 1500,
  "file_data": { "SKILL.md": { "role": "entry", "lines": 200, "color": "#D94F30", "summary": "...", "value": "key" } },
  "flow_steps": [ { "title": "第 1 步：触发识别", "read": "...", "judge": "...", "output": "...", "files": [["#D94F30","SKILL.md"]] } ],
  "sections": [ { "type": "purpose", "nav_title": "用途", "title": "...", "subtitle": "...", "html": "..." } ]
}
```

`sections` 数组按顺序包含 6 个模块，`type` 字段必须是：
`purpose` → `file_structure` → `execution_flow` → `core_file` → `master_insights` → `learning_path`

**第二步**：运行构建脚本：
```bash
cd {skill-viz-output-dir}
python3 {skill-dir}/scripts/build-report.py \
  --data skill-data.json \
  --output {skill-name}-学习导览.html
```

### 构建铁律

1. **单文件自包含**：CSS 内联、JS 内联，全部在一个 HTML 文件里。
2. **零框架**：纯 HTML + CSS + 原生 JavaScript。
3. **唯一外部资源**：Google Fonts。
4. **响应式**：桌面和手机都要正常。
5. **全中文 UI**：标题、标签、按钮、提示全部中文。
6. **真实内容**：展示 Skill 文件里真实的代码和文字，不要编造。

### ⭐ 复用固定骨架（不要重新发明 CSS）

构建脚本会自动加载 `references/template-head.html`（CSS）和 `references/template-scripts.html`（JS）。**你只负责写各模块的 HTML 内容**，必须复用骨架里已有的 CSS 类名，不要自己造类名。

**可用的 CSS 类名**（节选，完整见 `references/template-head.html`）：
| 用途 | CSS 类名 |
|------|---------|
| 结论/提示框 | `.callout`、`.callout-accent`、`.callout-info`、`.callout-warning`、`.callout-icon`、`.callout-title` |
| 统计卡 | `.stats-grid`、`.stat-card`、`.stat-icon`、`.stat-value`、`.stat-label` |
| 文件分组树 | `.file-tree`、`.ft-folder`、`.ft-file`、`.ft-children`、`.ft-toggle`、`.ft-name`、`.ft-desc`、`.ft-size`、`.ft-icon` |
| 价值标签 | `.value-tag`、`.value-key`（关键）、`.value-aux`（辅助）、`.value-skip`（可忽略） |
| 主链路 | `.main-chain`、`.chain-step`、`.chain-arrow` |
| 运行流程 | `.flow-timeline`、`.flow-track`、`.flow-phase`、`.flow-phase-dot`、`.flow-phase-title`、`.flow-phase-desc`、`.flow-phase-files`、`.flow-file-tag`（静态展示，无播放控件） |
| 核心文件 | `.skill-hero`、`.skill-hero-icon`、`.skill-hero-info`、`.skill-hero-meta` |
| 文档结构地图 | `.struct-map`、`.struct-section`、`.struct-section-head`、`.struct-section-marker`、`.struct-section-title`、`.struct-section-desc`、`.struct-section-detail` |
| 文件卡片 | `.file-cards`、`.file-card`、`.file-card-header`、`.file-card-body`、`.file-card-left`、`.file-card-right`、`.file-card-name`、`.file-card-stat`、`.file-card-chevron` |
| 改造对照卡 | `.principle-grid`、`.principle-card`、`.principle-num` |
| 学习路线 | `.roadmap`、`.roadmap-step`、`.roadmap-num`、`.roadmap-body` |
| 大师视角 | `.perspective-card`、`.perspective-header`、`.perspective-avatar`、`.perspective-meta`、`.perspective-name`、`.perspective-tag`、`.perspective-chevron`、`.perspective-body`、`.perspective-verdict`、`.perspective-points`、`.perspective-intro` |
| 大师要点徽标 | `.point-label`、`.point-good`（亮点）、`.point-warn`（警示）、`.point-core`（本质）、`.point-idea`（建议）、`.point-text` |
| 子标题 | `.sub-header`、`.sub-header-icon` |
| 代码片段 | `.snippet-code`、`.snippet-explanation`、`.snippet-label`、`.code-keyword`、`.code-string`、`.code-comment`、`.code-property`、`.code-function` |
| 术语提示 | `.term`、`.tooltip` |

**可用的 JS 函数**（已在骨架里定义，直接用 `onclick` 调用）：
```
toggleFolder(toggle)        — 展开/折叠文件夹分组
toggleStruct(el)            — 展开/折叠文档结构地图某节
toggleFileCard(header)      — 展开/折叠文件卡片
togglePerspective(card)     — 展开/折叠大师视角卡片
showTooltip(term) / hideTooltip()  — 术语提示（用 .term + data-definition 即可自动绑定）
```
> 运行流程（模块 03）为静态展示，没有播放函数。

**分段背景**：奇数模块（1、3、5）用 `var(--color-bg)`，偶数模块（2、4、6）用 `var(--color-bg-warm)`。构建脚本会自动处理，你不用管。

### 设计系统与配色

沿用 `references/design-system.md` 的暖色调设计：米色背景、Bricolage Grotesque 标题字体、DM Sans 正文、JetBrains Mono 代码、Catppuccin 代码高亮。配色变量见 `references/template-head.html` 顶部。

## 第四阶段：检查与交付

构建后在浏览器打开，逐项确认：
- [ ] 6 个模块标题全部为中文，无英文模块名、无抽象术语
- [ ] 模块 01 有醒目的"一句话结论"
- [ ] 模块 02 用分组 + 主链路，没有大规模星座图；价值标签清晰
- [ ] 模块 03 运行流程为静态全展示，所有步骤直接可见，无播放控件；每步写清读取/判断/产出/相关文件，箭头/编号明显
- [ ] 模块 04 文档结构地图全中文，其他文件按价值分组，辅助文件默认折叠
- [ ] 模块 05 大师视角：3 位大师、点评直击本质、有亮点/警示/本质徽标、有共识结语；第一张默认展开
- [ ] 模块 06 有阅读顺序、改造对照、高风险提醒；没有热力图
- [ ] 技术术语都有小白化解释（括号大白话或 .term 悬停提示），不留生硬术语
- [ ] 文件卡片、结构地图、大师卡片交互正常
- [ ] 表情符号克制使用，版面干净精致、配色统一
- [ ] 导航圆点、进度条同步；窄屏正常
- [ ] 语言直白、短句、每个模块都有明确结论

## 参考文件（按需读取）

| 文件 | 用途 | 何时读 |
|------|------|--------|
| `references/template-head.html` | 固定 CSS 骨架（构建脚本自动加载） | 需要查 CSS 类名时 |
| `references/template-scripts.html` | 固定 JS 骨架（构建脚本自动加载） | 需要查 JS 函数时 |
| `references/design-system.md` | 配色、字体、间距、动画规范 | 需要微调样式时 |
| `references/interactive-elements.md` | 交互组件实现模式 | 需要查交互细节时 |
| `references/template-report.html` | 完整示例报告 | 想看整体结构示例时 |

## 核心原则

> **这是一份「Skill 学习导览」，不是代码审计报告。**
> 语言要直白、短句、中文优先。少用图谱，多用分组、步骤、主链路和中文解释。
> 每个模块先给结论，再给细节。能折叠的低价值信息就折叠，不要堆砌。

### 要避免的做法
- ❌ 英文模块标题、抽象术语（Dashboard / Deep Dive / Matrix / 电梯陈述 / SLRC）
- ❌ 大规模节点星座图、文件交互热力图
- ❌ 为了"完整"而平铺罗列所有文件
- ❌ 编造代码片段 — 永远用 Skill 里的真实内容
- ❌ 冷淡的企业风、紫色渐变
- ❌ 引入 CDN 外部库

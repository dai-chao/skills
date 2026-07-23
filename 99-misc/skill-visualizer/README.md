# Skill 学习导览 · Skill Visualizer

![License](https://img.shields.io/github/license/Gtato-ai/skill-visualizer?style=flat-square)
![Skill](https://img.shields.io/badge/Skill-Agent-111111?style=flat-square)
![Output](https://img.shields.io/badge/输出-单页HTML-2A7B9B?style=flat-square)
![Lang](https://img.shields.io/badge/界面-中文优先-D94F30?style=flat-square)

> 把任意 Skill 文件夹，变成一份面向初学者的中文「Skill 学习导览」单页 HTML。
> 帮你快速看懂：这个 Skill 是做什么的、文件怎么读、运行时按什么顺序工作、它做得好不好、想改造该从哪下手。

## 它会生成什么

一份单页 HTML，包含 6 个中文模块：

| 模块 | 回答的问题 |
|------|-----------|
| 01 **这个 Skill 是做什么的** | 它是干什么的？适合什么场景？最终产出什么？ |
| 02 **文件结构怎么读** | 文件夹里这些文件分别负责什么？（分组 + 主链路，不堆星座图） |
| 03 **Skill 是怎么运行的** | 运行时按什么顺序工作？每步读取/判断/产出什么？（静态展示） |
| 04 **核心文件解读** | 想学习应该先看哪里？入口文件每节负责什么？ |
| 05 **大师视角分析** | 它做得好不好？设计原理是什么？（结合特点随机请 3 位大师直击本质点评） |
| 06 **学习路线与改造建议** | 新手怎么读？想改触发词 / 样式 / 流程 / 脚本看哪里？哪些改动风险高？ |

**输出为单个 HTML 文件** —— 无依赖、无需安装、可离线查看和分享。

## 报告定位

这是一份**学习导览**，不是代码审计报告：

- 全中文标题、标签、说明，不用抽象英文术语
- 语言直白、短句、先给结论
- 少用复杂图谱，多用分组、步骤、主链路和中文解释
- 技术术语带小白化解释（悬停提示），低价值文件自动折叠
- 克制使用表情符号，版面干净精致

## 安装

把本仓库克隆到你的 Skill 目录（如 Claude Code 的 `~/.claude/skills/`）：

```bash
git clone https://github.com/Gtato-ai/skill-visualizer.git ~/.claude/skills/skill-visualizer
```

也可以直接把这段话发给有 shell 权限的 AI Agent：

```text
帮我安装 skill-visualizer。请把 https://github.com/Gtato-ai/skill-visualizer 克隆到 ~/.claude/skills/skill-visualizer，安装完成后检查 SKILL.md、scripts/、references/ 是否存在。
```

## 使用方法

1. 打开任意包含 Skill 的项目
2. 输入触发语：
   - *"分析这个Skill"*
   - *"Skill可视化"*
   - *"看懂这个Skill"*
   - *"展示Skill流程"*
3. 稍等片刻，得到一份 `{skill-name}-学习导览.html`，浏览器打开即可。

## 工作原理

1. AI 读取 `SKILL.md`，分析目标 Skill 文件夹
2. AI 生成一个 5-15KB 的 `skill-data.json`（含 6 个模块的 HTML 内容）
3. 运行 `scripts/build-report.py`，自动把固定的 CSS/JS 骨架 + 数据拼成完整 HTML

```bash
python3 scripts/build-report.py --data skill-data.json --output {skill-name}-学习导览.html
```

这样 AI 只需写约 10KB 的数据，剩下的精致样式与交互由固定骨架保证，稳定又高效。

## 项目结构

```
skill-visualizer/
├── SKILL.md                      # 核心指令文件（生成导览的全部规则）
├── README.md                     # 说明文档（你正在读的）
├── LICENSE                       # MIT 许可证
├── scripts/
│   └── build-report.py           # 报告构建器：JSON 数据 + 固定骨架 → HTML
└── references/
    ├── template-head.html        # 固定 CSS 骨架
    ├── template-scripts.html     # 固定 JS 骨架（交互函数）
    ├── template-report.html      # 完整示例报告
    ├── design-system.md          # 配色 / 字体 / 间距规范
    └── interactive-elements.md   # 交互组件实现模式
```

## 设计理念

> 这是一份「Skill 学习导览」，不是文件清单。
> 用分组、步骤、主链路和直白的中文，把复杂的 Skill 讲成新手能看懂的样子。

## 致谢

受 [codebase-to-course](https://github.com/zarazhangrui/codebase-to-course) 启发，针对 Skill 学习场景重新设计。

## License

[MIT](./LICENSE)

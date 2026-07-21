---
name: github-repo-analysis
description: >
  Analyze a GitHub repository when the user drops a bare URL or terse command like
  "分析这个仓库". Produces structured architecture summary, code metrics, dependency
  overview, test quality assessment, and actionable conclusions.
triggers:
  - Bare GitHub repo URLs (https://github.com/<owner>/<repo>)
  - Commands like "分析这个仓库", "review this repo", "分析一下"
  - Requests to compare or survey AI agent / open-source tools
category: software-development
---

# GitHub 仓库分析工作流

## 目标
收到 GitHub 仓库链接或类似 terse 命令时，不需要确认意图，直接产出一份结构化、可执行的仓库分析报告。

## 默认动作
1. 克隆仓库（浅克隆）到本地临时目录。
2. 读取 README、pyproject.toml / package.json / Cargo.toml 等元数据。
3. 统计代码规模（按目录/语言的文件数与行数）。
4. 识别核心模块、架构分层、入口点。
5. 检查测试、CI、文档、依赖。
6. 给出亮点、风险、改进建议与结论。

## 分析维度

### 1. 基础信息
- 仓库名、版本、License、主要语言
- 最近提交活跃度、open issues/PRs（如 gh auth 可用，否则跳过）
- README 长度与完整度

### 2. 项目结构
- 顶层目录树
- 源码目录结构
- 配置文件、脚本、文档、测试目录位置

### 3. 代码规模
- 各目录 .py / .ts / .js / .rs 等文件数与行数
- 核心文件行数
- 如果仓库较小，可列出所有模块

### 4. 架构与核心设计
- 入口 CLI / 服务入口
- 抽象层与插件/渠道/后端机制
- 配置管理方式
- 与外部工具/平台/API 的集成方式

### 5. 依赖与生态
- 依赖列表与关键库
- optional dependencies / extras 含义
- 版本锁定策略（constraints.txt / poetry.lock / pnpm-lock）

### 6. 测试与质量
- 测试框架
- CI 配置（矩阵、覆盖率等）
- 测试覆盖的主要功能
- mock 与真实集成比例

### 7. 亮点与风险
- 产品设计/定位亮点
- 架构可维护性
- 对上游工具的依赖风险
- 安全/隐私相关设计

### 8. 结论
- 一句话定位
- 适用场景
- 是否值得跟进/使用/学习

## 输出风格
- 简洁、结构化，避免大段无编号文字
- 使用小标题、列表、表格
- 中文为主，保留英文技术术语
- 不加入未经验证的推测
- 如需进一步分析，在结尾用一句询问

## 常见陷阱
- 不要假设用户要 PR / 贡献 / fork；先给出分析
- 当 web_extract 被 block 或 gh 未登录时，直接 git clone 替代
- 文件读取优先用 execute_code / read_file，不要 cat/grep
- 测试不要真的运行 unless explicitly asked

## 相关参考
- references/repo-analysis-checklist.md — 可打印的逐项检查清单

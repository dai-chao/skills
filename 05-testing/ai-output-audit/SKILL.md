---
name: ai-output-audit
description: Audit and improve AI-generated outputs for fluency, persona consistency, safety, factual accuracy, and user-instruction compliance.
version: 1.0.0
author: Hermes Agent
metadata:
  hermes:
    tags: [ai audit, llm evaluation, output quality, safety, persona, prompt qa]
    category: qa
---

# AI 输出审计

用于批量审计和评估 AI 生成的文本输出，发现病句、人设不一致、安全违规、数据编造、指令不遵循等问题。

## 何时使用

- 需要对 LLM 输出做批量质量检查。
- 要生成带评估结果的 HTML 报告。
- 要维护一套规则化的审计 check list。
- 迭代 prompt 后验证输出是否改善。

## 通用审计维度

1. **口语化 / 病句**
   - 单句超过 9 个逗号 → 长句堆砌
   - 书面/AI 腔词（综上所述、值得注意的是、因此、基于此、首先/其次/最后）
   - 4 字及以上连续重复（排除范围表达如 `X分到X分半`）
   - 句尾单独 “别。” 等语病
   - 回复过短（<15 字）且不是开场/心跳/补水 → 缺少指导

2. **数据一致性**
   - 弱数据（如 `heartRateAvailable=false`）场景下引用具体数值 → 编造
   - 无配速数据却引用 `X:XX` 配速 → 编造

3. **安全规则**
   - 根据业务阈值检查是否出现明确的安全提示
   - 例如心率 ≥ 175 应出现降速建议；≥ 180/190 需要更强提示

4. **用户指令尊重**
   - 用户明确禁止的内容（如 “别报配速/心率”）是否仍出现
   - 用户报告身体不适（如膝盖不适）必须给出安全建议

5. **场景/业务逻辑**
   - 慢配速场景下是否错误催促加速
   - 范围表达、session_end 总结等是否被误判

6. **人设一致性**
   - 称谓与设定性别/角色是否冲突
   - 古今/意象是否混用
   - 人格标记词是否缺失导致褪色

## 工作流

1. 读取输出源（HTML 报告、JSONL、CSV）。
2. 解析输入字段（metrics、triggerType、userMessage、personaId 等）和输出文本。
3. 按审计维度逐条运行规则。
4. 为每个输出生成 `result`（合理 / 需优化）和具体 `suggest`。
5. 输出到原文件或生成新的 HTML 报告。
6. 在 summary 中统计合理/需优化数量。

## jymo Coach Chat 输出审计

一个具体应用案例：审计 `jymo /api/ai/coach/chat` 的跑步教练回复。规则详见 `references/jymo-persona-fluency-patterns.md`，包括：

- 口语化 / 病句规则
- 弱数据场景下不编造心率/配速
- 高心率安全提示阈值（HR ≥ 175/180/190）
- 用户指令尊重（如 “别报配速/心率”）
- 慢配速场景不催促加速
- 教练人设一致性（pro_female / 江湖武侠等）

## 输出规范

- HTML 报告新增「结果和建议」列。
- 合理用绿色，需优化用橙色并给行加 `row-failed` 背景。
- summary 卡片统计「合理」和「需优化」数量。
- 输出文件命名：`{original}_with_evaluation.html`。

## 常见陷阱

- 不要把 `session_end` 总结里引用当前输入数据（durationS、distanceM）当成编造历史。
- 不要把 “X分到X分半” 范围表达误判为重复短语。
- 慢配速场景中的 “冲到/顶到/被拉高” 是描述心率/强度，不是催促加速。
- 不要过度严格：教练口语允许无主语句、短句、连接词省略。
- 人设包装下，安全提醒必须优先。

## References

- `references/jymo-persona-fluency-patterns.md` — 人格一致性与口语流利度问题模式库（来自已合并的 `jymo-coach-chat-audit`）

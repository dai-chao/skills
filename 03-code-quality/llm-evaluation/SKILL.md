---
name: llm-evaluation
description: "Evaluate LLMs: academic benchmarks (MMLU, GSM8K), output quality auditing, and systematic prompt optimization with DSPy."
version: 1.0.0
author: Hermes Agent
license: MIT
dependencies: [lm-eval, dspy, transformers]
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [LLM Evaluation, Benchmarking, MMLU, GSM8K, Prompt Audit, DSPy, Prompt Optimization, Quality Assurance]
    related_skills: [llm-fine-tuning, llm-inference-serving]
---

# LLM Evaluation & Quality Assurance

## When to Use This Skill

Trigger when the user wants to:
- Benchmark model performance on academic tasks (MMLU, GSM8K, HumanEval)
- Audit LLM outputs for quality, safety, and consistency
- Optimize prompts systematically with data-driven methods
- Compare models before/after fine-tuning or abliteration
- Evaluate structured output quality

## Section 1: Academic Benchmarking with lm-eval-harness

Industry-standard evaluation across 60+ benchmarks.

### Installation
```bash
pip install lm-eval
```

### Core Benchmarks
| Benchmark | Measures | Task Type |
|:----------|:---------|:----------|
| **MMLU** | 57-subject knowledge | Multiple choice |
| **GSM8K** | Grade school math | Word problems |
| **HumanEval** | Code generation | Python functions |
| **HellaSwag** | Common sense | Sentence completion |
| **TruthfulQA** | Factuality | QA |
| **ARC** | Science reasoning | Multiple choice |

### Quick Evaluation
```bash
# Standard suite for model releases
lm_eval --model hf \
  --model_args pretrained=meta-llama/Llama-2-7b-hf \
  --tasks mmlu,gsm8k,hellaswag,truthfulqa,arc_challenge \
  --device cuda:0 \
  --batch_size 8

# With vLLM backend (5-10× faster)
lm_eval --model vllm \
  --model_args pretrained=meta-llama/Llama-2-7b-hf \
  --tasks mmlu,gsm8k \
  --batch_size auto

# View all available tasks
lm_eval --tasks list
```

### Key Flags
| Flag | Description | Default |
|:-----|:------------|:--------|
| `--num_fewshot` | Few-shot examples | 5 (varies by task) |
| `--batch_size` | Batch size | auto |
| `--device` | GPU device | cuda:0 |
| `--output_path` | Results directory | None |
| `--allow_code_execution` | For HumanEval | false |

### Troubleshooting
- **OOM**: Reduce batch size or use quantization
- **Slow**: Switch to vLLM backend or evaluate subsets (`mmlu_stem`)
- **Result mismatch**: Verify fewshot count and exact task names

## Section 2: Output Quality Auditing

Systematic quality auditing of LLM-generated text against persona, tone, safety, and accuracy rules.

### Audit Dimensions
1. **Tone & Persona** — Consistency with defined character/voice
2. **Safety** — Dangerous content detection (strict rules for health/safety)
3. **Scene-Trigger Matching** — Content matches expected trigger type
4. **Terminology** — Colloquial vs technical language consistency
5. **Data Accuracy** — Factual correctness

### Safety Override Rule
When safety and tone conflict, **safety always wins**. Example: Heart rate ≥ 190 → must use urgent language ("立刻", "别硬撑") regardless of casual persona.

### Audit Report Format
```
🟢 OK — Meets all criteria
🟠 Suggestion — Minor improvement possible
🔴 Critical — Must fix before deployment
```

### Batch-Level Persona Consistency
Cross-output checks for:
- Repetitive phrases across responses
- Theatricality/emotional range consistency
- Robotic pattern detection
- Safety persona-breaks
- Response length patterns

See [references/llm-prompt-audit-persona-patterns.md](references/llm-prompt-audit-persona-patterns.md) for full cross-output audit framework.

## Section 3: DSPy — Systematic Prompt Optimization

Stanford NLP's framework for building complex AI systems with declarative programming.

### Installation
```bash
pip install dspy
```

### Core Concepts
1. **Signatures** — Define input/output structure of LM tasks
2. **Modules** — Reusable components: `Predict`, `ChainOfThought`, `ReAct`, `ProgramOfThought`
3. **Optimizers** — Data-driven prompt optimization: `BootstrapFewShot`, `MIPRO`, `BootstrapFinetune`

### Quick Start
```python
import dspy

lm = dspy.Claude(model="claude-sonnet-4-5-20250929")
dspy.settings.configure(lm=lm)

class QA(dspy.Signature):
    """Answer questions with short factual answers."""
    question = dspy.InputField()
    answer = dspy.OutputField(desc="often between 1 and 5 words")

qa = dspy.Predict(QA)
response = qa(question="What is the capital of France?")
print(response.answer)  # "Paris"
```

### Chain of Thought
```python
class MathProblem(dspy.Signature):
    """Solve math word problems."""
    problem = dspy.InputField()
    answer = dspy.OutputField(desc="numerical answer")

cot = dspy.ChainOfThought(MathProblem)
result = cot(problem="If a train travels 60 mph for 2.5 hours, how far does it go?")
```

### RAG Pipeline
```python
class RAG(dspy.Module):
    def __init__(self, num_passages=3):
        self.retrieve = dspy.Retrieve(k=num_passages)
        self.generate = dspy.ChainOfThought("context, question -> answer")

    def forward(self, question):
        context = self.retrieve(question).passages
        return self.generate(context=context, question=question)
```

### Prompt Optimization
```python
from dspy.teleprompt import BootstrapFewShot

optimizer = BootstrapFewShot(metric=accuracy_metric)
optimized_rag = optimizer.compile(RAG(), trainset=train_data)
```

## Hardware Requirements

| Benchmark | Model Size | VRAM | Time |
|:----------|:-----------|:-----|:-----|
| MMLU full | 7B | ~16GB | ~2 hrs (A100) |
| GSM8K | 7B | ~16GB | ~30 min |
| HumanEval | 7B | ~16GB | ~15 min |

**Speed tips:**
- Use vLLM backend for 5-10× speedup
- Evaluate subsets (`mmlu_stem`) for quick checks
- Use `--batch_size auto` for optimal throughput

## Common Pitfalls

1. **Wrong fewshot count**: Default varies by task; check task docs
2. **Task name typos**: Use `lm_eval --tasks list` to verify exact names
3. **Audit subjectivity**: Define clear rubrics before auditing
4. **DSPy over-optimization**: Monitor for overfitting to training set
5. **Missing code execution**: HumanEval requires `--allow_code_execution`

## Complementary Skills

- **llm-fine-tuning** — Evaluate before/after fine-tuning
- **llm-inference-serving** — Benchmark served models
- **huggingface-hub** — Download models for evaluation

---
name: llm-inference-serving
description: "Serve and run LLMs locally: vLLM for high-throughput APIs, llama.cpp for GGUF/CPU inference, Outlines for structured generation, and OBLITERATUS for refusal removal."
version: 1.0.0
author: Hermes Agent
license: MIT
dependencies: [vllm, llama-cpp-python, outlines, obliteratus, torch, transformers]
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [LLM Inference, vLLM, llama.cpp, Outlines, Structured Generation, OBLITERATUS, GGUF, Quantization, PagedAttention, Model Serving]
    related_skills: [llm-fine-tuning, llm-evaluation, huggingface-hub]
---

# LLM Inference & Serving

## When to Use This Skill

Trigger when the user wants to:
- Deploy a production LLM API with high throughput
- Run models locally on CPU or limited GPU
- Generate structured outputs (JSON, XML, Pydantic models)
- Remove refusal behaviors from models (abliteration)
- Convert between model formats (GGUF, HF, quantized)
- Optimize inference latency and throughput

## Tool Selection Guide

| Tool | Best For | Throughput | Quantization | Structured Output |
|:-----|:---------|:-----------|:-------------|:------------------|
| **vLLM** | Production APIs | 24× higher | AWQ/GPTQ/FP8 | Via Outlines |
| **llama.cpp** | Local/CPU/GGUF | Standard | GGUF (Q4-Q8) | JSON via grammar |
| **Outlines** | Structured generation | N/A (add-on) | N/A | FSM-constrained |
| **OBLITERATUS** | Refusal removal | N/A | N/A | N/A |

## Section 1: vLLM — High-Throughput Serving

vLLM achieves ~24× higher throughput than standard transformers via PagedAttention and continuous batching.

### Installation
```bash
pip install vllm
```

### OpenAI-Compatible Server
```bash
# Single GPU (7B-13B)
vllm serve meta-llama/Llama-3-8B-Instruct \
  --gpu-memory-utilization 0.9 \
  --max-model-len 8192 \
  --port 8000

# Multi-GPU with tensor parallelism (30B-70B)
vllm serve meta-llama/Llama-2-70b-hf \
  --tensor-parallel-size 4 \
  --quantization awq \
  --port 8000

# With prefix caching and metrics
vllm serve meta-llama/Llama-3-8B-Instruct \
  --enable-prefix-caching \
  --enable-metrics \
  --metrics-port 9090
```

### Client Usage
```python
from openai import OpenAI
client = OpenAI(base_url='http://localhost:8000/v1', api_key='EMPTY')
response = client.chat.completions.create(
    model='meta-llama/Llama-3-8B-Instruct',
    messages=[{'role': 'user', 'content': 'Hello!'}]
)
print(response.choices[0].message.content)
```

### Offline Batch Inference
```python
from vllm import LLM, SamplingParams
llm = LLM(model="meta-llama/Llama-3-8B-Instruct")
sampling = SamplingParams(temperature=0.7, max_tokens=256)
outputs = llm.generate(["Explain quantum computing"], sampling)
```

### Hardware Guide
| Model Size | GPU Setup | Quantization |
|:-----------|:----------|:-------------|
| 7B-13B | 1× A10 / RTX 4090 | None or 8-bit |
| 30B-40B | 2× A100 | None or 8-bit |
| 70B | 4× A100 or AWQ | AWQ/GPTQ |
| 405B | 8× A100 / Multi-node | FP8 |

### Ollama Quick Reference (Windows / macOS / Linux)
Ollama wraps llama.cpp and is the easiest way to run GGUF models locally.

```bash
# Install
brew install ollama          # macOS
winget install Ollama.Ollama # Windows

# Pull and run (automatically downloads quantized model)
ollama run glm4:9b
ollama run llama3.1:8b

# List local models
ollama list

# Serve API (OpenAI-compatible)
ollama serve
# Then: curl http://localhost:11434/api/generate -d '{"model":"glm4:9b","prompt":"hi"}'
```

**VRAM rule of thumb for Ollama (GGUF / Q4_K_M):**
- 7B-9B  → ~5-6 GB  (RTX 3060 12GB, RTX 4060, laptop 3060)
- 14B    → ~9-10 GB (RTX 3080 10GB, RTX 4070 Ti)
- 32B    → ~20 GB   (RTX 3090/4090 24GB)
- 70B    → ~40 GB+  (dual GPU or A100 40/80GB)
- 100B+  → ~60 GB+  (multi-node or H100)

If the user names a model you don't know (e.g. "GLM-5.2"), ask for its parameter count or suggest they run `ollama run <model>` — Ollama will error with a clear message if VRAM is insufficient.

## Section 2: llama.cpp — Local GGUF Inference

Run quantized models locally on CPU or GPU with minimal dependencies.

### Installation
```bash
pip install llama-cpp-python
```

### Basic Usage
```python
from llama_cpp import Llama

llm = Llama(model_path="models/llama-3-8b-q4.gguf", n_ctx=4096, n_threads=8)
output = llm("Q: What is the capital of France?\nA:", max_tokens=64, stop=["Q:", "\n"])
print(output["choices"][0]["text"])
```

### GGUF Conversion
```bash
# From HuggingFace model
python -m llama_cpp.convert \
  --model-id meta-llama/Llama-3-8B-Instruct \
  --outfile models/llama-3-8b-q4.gguf \
  --outtype q4_k_m
```

### Quantization Types
| Type | Size | Quality | Use Case |
|:-----|:-----|:--------|:---------|
| Q4_K_M | ~4.5GB (8B) | Good | Balanced |
| Q5_K_M | ~5.5GB (8B) | Better | Quality优先 |
| Q8_0 | ~8GB (8B) | Best | Maximum quality |
| IQ4_XS | ~4GB (8B) | Good | Smallest |

## Section 3: Outlines — Structured Generation

Guarantee valid JSON/XML/code outputs using FSM-constrained token generation.

### Installation
```bash
pip install outlines
```

### JSON with Pydantic
```python
from pydantic import BaseModel
import outlines

class User(BaseModel):
    name: str
    age: int
    email: str

model = outlines.models.transformers("microsoft/Phi-3-mini-4k-instruct")
generator = outlines.generate.json(model, User)
user = generator("Extract: John Doe, 30, john@example.com")
print(user.name)  # "John Doe"
```

### Regex-Constrained Generation
```python
import outlines
model = outlines.models.transformers("microsoft/Phi-3-mini-4k-instruct")
generator = outlines.generate.regex(model, r"\d{3}-\d{2}-\d{4}")
ssn = generator("Generate a US Social Security number: ")
```

### With vLLM Backend
```python
import outlines
from vllm import LLM

llm = LLM(model="meta-llama/Llama-3-8B-Instruct")
model = outlines.models.vllm(llm)
generator = outlines.generate.json(model, User)
```

## Section 4: OBLITERATUS — Refusal Removal

Surgically remove refusal behaviors from open-weight LLMs without retraining.

### ⚠️ License Warning
OBLITERATUS is AGPL-3.0. **NEVER** import it as a library in MIT/Apache projects. Always invoke via CLI or subprocess.

### Installation
```bash
git clone https://github.com/elder-plinius/OBLITERATUS.git
cd OBLITERATUS
pip install -e .
```

### Quick Abliteration
```bash
# Default method (recommended)
obliteratus obliterate meta-llama/Llama-3-8B-Instruct \
  --method advanced \
  --quantization 4bit \
  --output-dir ./abliterated-models

# Get telemetry-driven recommendation
obliteratus recommend meta-llama/Llama-3-8B-Instruct
```

### Method Selection
| Method | Best For | Speed | Risk |
|:-------|:---------|:------|:-----|
| basic | Quick test | ~5-10 min | Low |
| advanced (DEFAULT) | Most models | ~10-20 min | Low |
| aggressive | Stubborn refusals | Medium | Higher coherence damage |
| surgical | Reasoning models | ~1-2 hrs | Lowest |
| nuclear | MoE models (DeepSeek) | Medium | Medium |

### Verification
After abliteration, check:
- Refusal rate < 5% (ideally ~0%)
- Perplexity change < 10% increase
- KL divergence < 0.1

## Common Pitfalls

1. **vLLM OOM**: Reduce `--gpu-memory-utilization` or use quantization
2. **llama.cpp slow on CPU**: Use `n_threads=os.cpu_count()` and Q4 quant
3. **Outlines invalid JSON**: Ensure Pydantic model has no `Optional` without defaults
4. **OBLITERATUS AGPL**: Never `import obliteratus` — CLI only
5. **Quantized models can't be re-quantized**: Abliterate full-precision, then quantize output
6. **vLLM model not found**: Use exact HuggingFace model ID or local path
7. **llama.cpp context too small**: Increase `n_ctx` for long conversations

## Complementary Skills

- **llm-fine-tuning** — Fine-tune models before serving
- **llm-evaluation** — Benchmark served models
- **huggingface-hub** — Download and upload models

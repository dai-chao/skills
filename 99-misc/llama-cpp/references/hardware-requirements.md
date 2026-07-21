# Local LLM Hardware Requirements Guide

Quick-reference for answering "what hardware do I need to run model X locally?"

## Core Principle

VRAM (or unified memory on Apple Silicon) is the bottleneck. Use this formula:

```
VRAM needed ≈ model_params × bytes_per_param × 1.2 overhead
```

| Precision | Bytes/Param | Quality |
|-----------|-------------|---------|
| FP16/BF16 | 2 | Baseline (best) |
| Q8_0 | 1 | Nearly lossless |
| Q6_K | ~0.75 | Excellent |
| Q5_K_M | ~0.65 | Very good |
| Q4_K_M | ~0.55 | Good (recommended) |
| Q3_K_M | ~0.45 | Acceptable |
| Q2_K | ~0.35 | Poor (emergency only) |

## Rule-of-Thumb VRAM Table

Assume ~70B-100B parameter models (e.g., GLM-5.2, Llama-3-70B, Qwen-72B):

| Quant | VRAM Needed | Fit On |
|-------|-------------|--------|
| Q4_K_M | ~40-50 GB | 2× RTX 4090 (24GB), 1× A100 (40/80GB) |
| Q8_0 | ~70-80 GB | 1× A100 80GB, 2× A6000 (48GB) |
| FP16 | ~140-200 GB | 2× A100 80GB, 1× H100 80GB (tight) |

For 7B-13B models, divide by ~6-10.

## Platform-Specific Guidance

### NVIDIA (Windows/Linux) — Recommended

| GPU | VRAM | Can Run |
|-----|------|---------|
| RTX 3060 / 4060 | 12 GB | 7B Q4, 13B Q3 |
| RTX 3090 / 4090 | 24 GB | 7B-13B Q4-Q8, 70B Q4 (tight) |
| RTX 4090 ×2 | 48 GB | 70B Q4-Q5, 13B FP16 |
| A6000 | 48 GB | 70B Q4-Q5 comfortably |
| A100 | 40/80 GB | 70B Q4-Q8, 100B+ Q4 |

- CUDA is the gold standard for local LLM inference
- Use `nvidia-smi` to check actual VRAM availability
- Leave 1-2 GB headroom for OS / desktop

### Apple Silicon (macOS)

| Chip | Unified Memory | Can Run | Reality Check |
|------|---------------|---------|---------------|
| M1/M2 base | 8-16 GB | 3B-7B Q4 | Forget 70B+ models |
| M3 Pro / M3 Max | 36-48 GB | 7B-13B Q4, 70B Q4 (barely) | Very slow for 70B |
| M4 Max / M3 Ultra | 128 GB+ | 70B Q4-Q5, 13B Q8 | Metal backend 2-5× slower than CUDA equivalent |

**Apple Silicon caveats:**
- No CUDA; Ollama/llama.cpp uses Metal backend
- Unified memory bandwidth is high (~400-500 GB/s) but not GPU-dedicated HBM
- Quantized models sometimes have compatibility issues on Metal
- For large models (70B+), Apple Silicon is a "can run" not "should run" platform
- Be honest with users: Macs are great for 7B-13B, marginal for 70B, impractical for 100B+ at full precision

### CPU-Only

- Possible but painful for models > 7B
- Requires massive RAM (128 GB+ for 70B Q4)
- Speed: 1-5 tok/s vs 50-100+ tok/s on GPU
- Only recommend for tiny models or batch offline jobs

## Ollama-Specific Notes

Ollama abstracts quantization but the hardware math is the same:

```bash
# Check what Ollama thinks it can load
ollama ps
# Shows loaded models and their memory footprint
```

Ollama will automatically quantize to fit available memory, but quality degrades. Tell users the truth: if their hardware only supports Q3, the model will be noticeably dumber.

## Cloud Fallback

When user's hardware is insufficient, suggest cloud GPU rental:

| Provider | GPU | Price | Good For |
|----------|-----|-------|----------|
| RunPod | RTX 4090 | ~$0.50-1/hr | Quick experiments |
| Vast.ai | RTX 4090 / A6000 | ~$0.40-0.80/hr | Best price |
| Lambda Labs | A100 / H100 | ~$1-3/hr | Production workloads |
| 阿里云 / 腾讯云 | A100 | 按量付费 | 国内用户 |

## How to Answer Users

1. **Ask their current hardware first** — don't dump a full table if they already have a 4090
2. **Be direct about Apple Silicon limits** — "能跑但很慢" is more useful than "理论上可以"
3. **Give quant-specific numbers** — "70B Q4 needs ~40GB" is actionable
4. **Suggest cloud when local is impractical** — don't let them waste money on hardware that won't satisfy them
5. **Mention context length** — longer context = more KV cache = more VRAM

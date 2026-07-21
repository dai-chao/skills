---
name: heartmula
description: Set up and run HeartMuLa, the open-source music generation model family (Suno-like). Generates full songs from lyrics + tags with multilingual support.
version: 1.1.0
metadata:
  hermes:
    tags: [music, audio, generation, ai, heartmula, heartcodec, lyrics, songs]
    related_skills: [audiocraft]
---

# HeartMuLa - Open-Source Music Generation

## Overview
HeartMuLa is a family of open-source music foundation models (Apache-2.0) that generates music conditioned on lyrics and tags. Comparable to Suno for open-source. Includes:
- **HeartMuLa** - Music language model (3B/7B) for generation from lyrics + tags
- **HeartCodec** - 12.5Hz music codec for high-fidelity audio reconstruction
- **HeartTranscriptor** - Whisper-based lyrics transcription
- **HeartCLAP** - Audio-text alignment model

## When to Use
- User wants to generate music/songs from text descriptions
- User wants an open-source Suno alternative
- User wants local/offline music generation
- User asks about HeartMuLa, heartlib, or AI music generation

## Hardware Requirements
- **Minimum (GPU)**: 8GB VRAM with `--lazy_load true` (loads/unloads models sequentially)
- **Recommended (GPU)**: 16GB+ VRAM for comfortable single-GPU usage
- **Multi-GPU**: Use `--mula_device cuda:0 --codec_device cuda:1` to split across GPUs
- 3B model with lazy_load peaks at ~6.2GB VRAM
- **CPU**: Not recommended. Requires **~20GB+ free RAM**, and 30 seconds of audio takes ~3 hours on a modern Mac CPU.

## Installation Steps

### 1. Clone Repository
```bash
cd ~/  # or desired directory
git clone https://github.com/HeartMuLa/heartlib.git
cd heartlib
```

### 2. Create Virtual Environment (Python 3.10+ required)

**IMPORTANT**: Python 3.9 (macOS default) is too old — modern PyTorch requires 3.10+. Install 3.10 first:
```bash
uv python install 3.10
```

Then create the venv and install. **This step downloads torch (~75MB), transformers, pyarrow, etc. and can take several minutes.**
```bash
uv venv --python 3.10 .venv
. .venv/bin/activate
uv pip install -e .
```

> **Tip**: If the command times out (common on slower connections), run it in background:
> ```bash
> uv pip install -e . > /tmp/heartlib_install.log 2>&1 &
> ```

### 3. Fix Dependency Compatibility Issues

**IMPORTANT**: As of Feb 2026, the pinned dependencies have conflicts with newer packages. Apply these fixes:

```bash
# Upgrade datasets (old version incompatible with current pyarrow)
uv pip install --upgrade datasets

# Upgrade transformers (needed for huggingface-hub 1.x compatibility)
uv pip install --upgrade transformers
```

### 4. Patch Source Code (Required for transformers 5.x)

**Patch 1 - RoPE cache fix** in `src/heartlib/heartmula/modeling_heartmula.py`:

In the `setup_caches` method of the `HeartMuLa` class, add RoPE reinitialization after the `reset_caches` try/except block and before the `with device:` block:

```python
# Re-initialize RoPE caches that were skipped during meta-device loading
from torchtune.models.llama3_1._position_embeddings import Llama3ScaledRoPE
for module in self.modules():
    if isinstance(module, Llama3ScaledRoPE) and not module.is_cache_built:
        module.rope_init()
        module.to(device)
```

**Why**: `from_pretrained` creates model on meta device first; `Llama3ScaledRoPE.rope_init()` skips cache building on meta tensors, then never rebuilds after weights are loaded to real device.

**Patch 2 - HeartCodec loading fix** in `src/heartlib/pipelines/music_generation.py`:

Add `ignore_mismatched_sizes=True` to ALL `HeartCodec.from_pretrained()` calls (there are 2: the eager load in `__init__` and the lazy load in the `codec` property).

**Why**: VQ codebook `initted` buffers have shape `[1]` in checkpoint vs `[]` in model. Same data, just scalar vs 0-d tensor. Safe to ignore.

### 5. Download Model Checkpoints

Total download size is **~20 GB** (3B model ≈13.7GB + HeartCodec ≈6.6GB + config files).

**Option A — HuggingFace (fastest with token)**
```bash
cd heartlib  # project root
export HF_TOKEN='your_hf_token_here'  # strongly recommended; unauthenticated downloads are heavily rate-limited and may stall
hf download --local-dir './ckpt/HeartMuLa-oss-3B' 'HeartMuLa/HeartMuLa-oss-3B-happy-new-year'
hf download --local-dir './ckpt/HeartCodec-oss' 'HeartMuLa/HeartCodec-oss-20260123'
```

Both can be downloaded in parallel.

**Option B — ModelScope mirror (China-friendly, and often faster globally)**
If HuggingFace is unreachable or slow, ModelScope hosts the same checkpoints:

```python
# ModelScope sequential download script (RECOMMENDED over snapshot_download)
# snapshot_download triggers rate limiting; single-file downloads are much faster
from modelscope.hub.file_download import model_file_download
import os

repos = [
    ("HeartMuLa/HeartMuLa-oss-3B-happy-new-year", "./ckpt/HeartMuLa-oss-3B"),
    ("HeartMuLa/HeartCodec-oss-20260123", "./ckpt/HeartCodec-oss"),
]

for repo_id, local_dir in repos:
    os.makedirs(local_dir, exist_ok=True)
    # Download index first to discover shards
    idx = model_file_download(repo_id, "model.safetensors.index.json", local_dir=local_dir)
    import json
    with open(idx) as f:
        data = json.load(f)
    shards = set(data["weight_map"].values())
    for shard in sorted(shards):
        model_file_download(repo_id, shard, local_dir=local_dir)
    # Download small config files
    for small in ["config.json", "README.md"]:
        try:
            model_file_download(repo_id, small, local_dir=local_dir)
        except Exception:
            pass
```

> **Key finding**: ModelScope `snapshot_download` (which downloads all files concurrently) often triggers rate limiting and drops to ~100KB/s. **Sequential single-file downloads via `model_file_download` achieve 20MB/s+** and complete in minutes instead of hours. Always prefer sequential single-file downloads.

> **Codec model file naming**: HeartCodec uses `model-00001-of-00002.safetensors` and `model-00002-of-00002.safetensors`, NOT a single `model.safetensors`. The index file maps weights across these two shards.

**Option C — Let the pipeline auto-download on first run**
If checkpoints are missing from `./ckpt`, the generation script will attempt to download them automatically from HuggingFace. This is convenient but gives you no progress visibility and is subject to the same rate limits.

## GPU / CUDA

HeartMuLa uses CUDA by default (`--mula_device cuda --codec_device cuda`). No extra setup needed if the user has an NVIDIA GPU with PyTorch CUDA support installed.

- The installed `torch==2.4.1` includes CUDA 12.1 support out of the box
- `torchtune` may report version `0.4.0+cpu` — this is just package metadata, it still uses CUDA via PyTorch
- To verify GPU is being used, look for "CUDA memory" lines in the output (e.g. "CUDA memory before unloading: 6.20 GB")

### No GPU / macOS / CPU-only

**macOS**: Triton is not available on macOS, so GPU acceleration is impossible. You can only run on CPU:
```bash
--mula_device cpu --codec_device cpu
```

**CPU mode realities**:
- **Speed**: Generating 30 seconds of audio with the 3B model takes **~3 hours** on a modern Mac CPU (M1/M2/M3). Each generation step takes ~30 seconds.
- **RAM**: Requires **~20GB+ free system memory** (3B model + codec + activations)
- **Heat/Fan**: MacBooks will thermal-throttle under sustained CPU load; expect fans at max
- **Recommendation**: For Mac or CPU-only users, **do NOT attempt local generation** with the 3B model. Use the **online demo** at https://heartmula.github.io/ or a cloud GPU (Google Colab T4, Lambda Labs, etc.) instead.

If the user still insists on local CPU generation, reduce `--max_audio_length_ms 10000` (10 seconds) to cut generation time to ~1 hour, or use a much smaller model if one becomes available.

**Required CPU-specific code patches** (in addition to the RoPE and HeartCodec patches above):

**Patch 3 — Remove CUDA-only guards** in `src/heartlib/encoding_decoding.py`:
Replace:
```python
if torch.cuda.is_available():
    torch.cuda.synchronize()
```
With:
```python
if torch.cuda.is_available():
    torch.cuda.synchronize()
# CPU: no sync needed
```
Do this for ALL occurrences in that file.

**Patch 4 — Fix parametrize import** in `src/heartlib/encoding_decoding.py`:
Add after the `torch` import:
```python
import torch.nn.utils.parametrize as parametrize
```

**Patch 5 — Fix `torch.set_default_device` missing attribute** in `src/heartlib/encoding_decoding.py`:

Some PyTorch builds (especially older CPU-only wheels) do not have `torch.set_default_device`. If you hit:
```
AttributeError: module 'torch' has no attribute 'set_default_device'
```

Wrap the call at approximately line 75:
```python
# OLD:
torch.set_default_device(device)

# NEW:
try:
    torch.set_default_device(device)
except AttributeError:
    pass
```

**Patch 5 — Fix autocast for CPU** in `src/heartlib/pipelines/music_generation.py`:
The script uses `torch.autocast(device_type=self.mula_device.type, ...)` with `bfloat16`/`float16`, but CPU autocast only supports `bfloat16` and `float16` (it actually does support them). The real issue is that when `self.mula_dtype == torch.float32`, autocast emits warnings. The warnings are harmless but noisy. If you want to silence them, patch the two `with torch.autocast(...)` blocks to skip autocast when on CPU and dtype is float32:
```python
if self.mula_device.type == "cpu" and self.mula_dtype == torch.float32:
    # No autocast on CPU with float32 — avoids warnings
    pass
else:
    with torch.autocast(...):
        ...
```

**Note**: When running on CPU, use `--mula_dtype float32 --codec_dtype float32`. BFloat16 on CPU may not be supported depending on PyTorch build.

## Usage

### Basic Generation (GPU)
```bash
cd heartlib
. .venv/bin/activate

LYRICS=$(cat ./assets/lyrics.txt)
TAGS=$(cat ./assets/tags.txt)

python ./examples/run_music_generation.py \
  --model_path=./ckpt \
  --version="3B" \
  --lyrics="$LYRICS" \
  --tags="$TAGS" \
  --save_path="./output.mp3" \
  --lazy_load true
```

> **Note**: `--lyrics` and `--tags` accept **literal strings**, not file paths. Use `$(cat file.txt)` or write the text directly in quotes.

### CPU Generation (NOT recommended — see CPU section above)
```bash
python ./examples/run_music_generation.py \
  --model_path=./ckpt \
  --version="3B" \
  --lyrics="$LYRICS" \
  --tags="$TAGS" \
  --save_path="./output.mp3" \
  --mula_device cpu \
  --codec_device cpu \
  --mula_dtype float32 \
  --codec_dtype float32 \
  --max_audio_length_ms 30000 \
  --lazy_load true
```

### Input Formatting

**Tags** (comma-separated, no spaces):
```
piano,happy,wedding,synthesizer,romantic
```
or
```
rock,energetic,guitar,drums,male-vocal
```

**Lyrics** (use bracketed structural tags):
```
[Intro]

[Verse]
Your lyrics here...

[Chorus]
Chorus lyrics...

[Bridge]
Bridge lyrics...

[Outro]
```

### Key Parameters
| Parameter | Default | Description |
|-----------|---------|-------------|
| `--max_audio_length_ms` | 240000 | Max length in ms (240s = 4 min) |
| `--topk` | 50 | Top-k sampling |
| `--temperature` | 1.0 | Sampling temperature |
| `--cfg_scale` | 1.5 | Classifier-free guidance scale |
| `--lazy_load` | false | Load/unload models on demand (saves VRAM) |
| `--mula_dtype` | bfloat16 | Dtype for HeartMuLa (bf16 recommended) |
| `--codec_dtype` | float32 | Dtype for HeartCodec (fp32 recommended for quality) |

### Performance
- RTF (Real-Time Factor) ≈ 1.0 — a 4-minute song takes ~4 minutes to generate
- Output: MP3, 48kHz stereo, 128kbps

## Pitfalls
1. **Do NOT use bf16 for HeartCodec** — degrades audio quality. Use fp32 (default).
2. **Tags may be ignored** — known issue (#90). Lyrics tend to dominate; experiment with tag ordering.
3. **Triton not available on macOS** — Linux/CUDA only for GPU acceleration.
4. **RTX 5080 incompatibility** reported in upstream issues.
5. **Dependency install can timeout** — `uv pip install -e .` downloads torch, transformers, pyarrow, etc. On slower connections use background mode or increase timeout.
6. **Model downloads are large and easily throttled** — ~20GB total (3B ~14GB + Codec ~6.6GB). Without `HF_TOKEN`, HuggingFace downloads may stall at ~0% for hours. ModelScope helps in China but `snapshot_download` can trigger rate limiting. **Use sequential single-file `model_file_download` for fastest speeds (20MB/s+).**
7. The dependency pin conflicts require the manual upgrades and patches described above.
8. **CPU generation is impractical**: 3B model on CPU takes ~30s per step. A 30-second song (~375 steps) takes ~3 hours. Only use CPU for testing the pipeline, not for actual production.
9. **Codec model has sharded weights**: HeartCodec uses `model-00001-of-00002.safetensors` + `model-00002-of-00002.safetensors`, not a single file. Make sure both shards are present.

## Links
- Repo: https://github.com/HeartMuLa/heartlib
- Models: https://huggingface.co/HeartMuLa
- Paper: https://arxiv.org/abs/2601.10547
- License: Apache-2.0

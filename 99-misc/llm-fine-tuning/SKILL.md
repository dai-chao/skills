---
name: llm-fine-tuning
description: "Fine-tune LLMs: framework selection (Unsloth, Axolotl, TRL), training methods (SFT, DPO, PPO, GRPO, LoRA/QLoRA), and experiment tracking with W&B."
version: 1.0.0
author: Hermes Agent
license: MIT
dependencies: [torch, transformers, datasets, peft, accelerate, wandb]
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Fine-Tuning, LLM, LoRA, QLoRA, SFT, DPO, PPO, GRPO, Unsloth, Axolotl, TRL, W&B, Experiment Tracking]
    related_skills: [llm-inference-serving, llm-evaluation, huggingface-hub]
---

# LLM Fine-Tuning

## When to Use This Skill

Trigger when the user wants to:
- Fine-tune a language model (Llama, Mistral, Qwen, Gemma, etc.)
- Choose between fine-tuning frameworks (Unsloth, Axolotl, TRL)
- Apply LoRA/QLoRA for memory-efficient training
- Align models with human preferences (DPO, PPO, GRPO)
- Track experiments with Weights & Biases
- Compare training methods and hardware requirements

## Framework Selection Guide

| Framework | Best For | Config Style | Speed | Memory |
|:----------|:---------|:-------------|:------|:-------|
| **Unsloth** | Speed & memory optimization | Python API | 2-5× faster | 50-80% less |
| **Axolotl** | YAML-driven, 100+ models | YAML config | Standard | Standard |
| **TRL** | RLHF, preference alignment | Python API | Standard | Standard |

## Section 1: Unsloth — Fast Fine-Tuning

Unsloth delivers 2-5× faster training and 50-80% less memory via optimized kernels.

### Installation
```bash
pip install unsloth
# Also installs: torch, transformers, trl, datasets, peft
```

### Quick Start (LoRA)
```python
from unsloth import FastLanguageModel
import torch

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/Llama-3.2-1B",
    max_seq_length=2048,
    dtype=torch.float16,
    load_in_4bit=True,
)

model = FastLanguageModel.get_peft_model(
    model,
    r=16,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
    lora_alpha=16,
    lora_dropout=0,
    bias="none",
    use_gradient_checkpointing="unsloth",
    random_state=3407,
)
```

### Supported Models
- Llama 3.1/3.2, Mistral, Gemma 2, Qwen 2.5, Phi-4, Mistral Small
- See [references/unsloth-llms-txt.md](references/unsloth-llms-txt.md) for full model list and advanced patterns.

## Section 2: Axolotl — YAML-Config Training

Axolotl provides YAML-driven training for 100+ models with no code required.

### Installation
```bash
pip install axolotl
```

### Quick Start
```yaml
# config.yaml
base_model: Qwen/Qwen2.5-0.5B
model_type: AutoModelForCausalLM
load_in_4bit: true
adapter: lora
lora_r: 16
lora_alpha: 32
lora_dropout: 0.05
lora_target_linear: true

 datasets:
  - path: teknium/OpenHermes-2.5
    type: sharegpt
    conversation: chatml

num_epochs: 3
micro_batch_size: 2
gradient_accumulation_steps: 4
learning_rate: 2e-4
optimizer: adamw_bnb_8bit
```

```bash
axolotl train config.yaml
```

### Training Methods Supported
- SFT, DPO, KTO, ORPO, GRPO
- Multimodal (vision-language)
- FSDP, DeepSpeed, sequence packing, context parallelism

### Key Features
- `save_compressed: true` reduces disk usage ~40%
- `context_parallel_size` must divide total GPU count
- See [references/axolotl-dataset-formats.md](references/axolotl-dataset-formats.md) for dataset format reference.

## Section 3: TRL — Reinforcement Learning & Preference Alignment

TRL (Transformer Reinforcement Learning) provides post-training methods for aligning models with human preferences.

### Installation
```bash
pip install trl transformers datasets peft accelerate
```

### Method Selection

| Method | Data Needed | Use Case | VRAM (7B) |
|:-------|:------------|:---------|:----------|
| **SFT** | Prompt-completion pairs | Instruction following | 16GB (LoRA) |
| **DPO** | Chosen/rejected pairs | Preference alignment (no reward model) | 24GB |
| **PPO** | Reward model + prompts | Full RLHF | 40GB |
| **GRPO** | Prompts + reward function | Memory-efficient online RL | 24GB |

### SFT Quick Start
```python
from trl import SFTTrainer, SFTConfig
from datasets import load_dataset

model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-0.5B")
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-0.5B")
dataset = load_dataset("trl-lib/Capybara", split="train")

training_args = SFTConfig(
    output_dir="Qwen2.5-0.5B-SFT",
    per_device_train_batch_size=4,
    num_train_epochs=1,
    learning_rate=2e-5,
)

trainer = SFTTrainer(model=model, args=training_args, train_dataset=dataset, tokenizer=tokenizer)
trainer.train()
```

### DPO Quick Start
```python
from trl import DPOTrainer, DPOConfig

config = DPOConfig(output_dir="model-dpo", beta=0.1, per_device_train_batch_size=4)
trainer = DPOTrainer(model=model, args=config, train_dataset=preference_dataset, processing_class=tokenizer)
trainer.train()
```

### GRPO Quick Start
```python
from trl import GRPOConfig, GRPOTrainer

def reward_function(completions, **kwargs):
    return [len(c.split()) + len(set(c.lower().split())) for c in completions]

config = GRPOConfig(output_dir="Qwen2-GRPO", num_generations=4, max_new_tokens=128)
trainer = GRPOTrainer(model="Qwen/Qwen2-0.5B-Instruct", reward_funcs=reward_function, args=config, train_dataset=dataset)
trainer.train()
```

### Full RLHF Pipeline
```
RLHF Training:
- [ ] Step 1: SFT (supervised fine-tuning)
- [ ] Step 2: Train reward model
- [ ] Step 3: PPO reinforcement learning
- [ ] Step 4: Evaluate aligned model
```

See [references/trl-grpo-training.md](references/trl-grpo-training.md) for in-depth GRPO guidance, reward function design, and production-ready templates.

## Section 4: Weights & Biases — Experiment Tracking

Track and visualize all training runs with W&B.

### Installation
```bash
pip install wandb
wandb login
```

### Basic Integration
```python
import wandb

wandb.init(project="llm-finetuning", config={"lr": 2e-4, "epochs": 3, "batch_size": 4})

for epoch in range(wandb.config.epochs):
    train_loss = train_epoch()
    val_loss = validate()
    wandb.log({"epoch": epoch, "train/loss": train_loss, "val/loss": val_loss})

wandb.finish()
```

### Hyperparameter Sweeps
```python
sweep_config = {
    'method': 'bayes',
    'metric': {'name': 'val/loss', 'goal': 'minimize'},
    'parameters': {
        'learning_rate': {'distribution': 'log_uniform', 'min': 1e-5, 'max': 1e-3},
        'lora_r': {'values': [8, 16, 32, 64]},
        'batch_size': {'values': [2, 4, 8]}
    }
}
sweep_id = wandb.sweep(sweep_config, project="llm-finetuning")
wandb.agent(sweep_id, function=train, count=20)
```

### Model Registry
```python
artifact = wandb.Artifact('lora-adapter', type='model')
artifact.add_dir('./lora-output')
wandb.log_artifact(artifact, aliases=['best', 'production'])
```

## Hardware Requirements

| Model Size | SFT (LoRA) | DPO | PPO | GRPO |
|:-----------|:-----------|:----|:----|:-----|
| 7B | 16GB | 24GB | 40GB | 24GB |
| 13B | 24GB | 40GB | 80GB | 40GB |
| 70B | 80GB (QLoRA) | Multi-GPU | Multi-GPU | Multi-GPU |

**Memory optimization tips:**
- Use LoRA/QLoRA for all methods
- Enable gradient checkpointing: `model.gradient_checkpointing_enable()`
- Use smaller batch sizes with gradient accumulation
- Use `bf16` on A100/H100

## Common Pitfalls

1. **OOM during DPO**: DPO stores a reference model — reduce batch size or use QLoRA
2. **Poor DPO alignment**: Tune `beta` (higher = more conservative, default 0.1)
3. **PPO instability**: Increase `kl_coef`, reduce `cliprange`
4. **Unsloth not installed**: Requires specific PyTorch version; use `pip install unsloth` in fresh env
5. **Axolotl config errors**: YAML indentation is critical; validate with `axolotl validate config.yaml`
6. **W&B not logging**: Ensure `report_to="wandb"` in TrainingArguments or call `wandb.init()` before training

## Complementary Skills

- **llm-inference-serving** — Serve fine-tuned models with vLLM or llama.cpp
- **llm-evaluation** — Benchmark fine-tuned models with lm-eval-harness
- **huggingface-hub** — Upload and share fine-tuned models

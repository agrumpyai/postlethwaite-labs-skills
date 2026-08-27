---
name: llm-gpu-fit
description: Check if an LLM fits your GPU VRAM and agent context minimums — architecture-aware VRAM math, KV cache estimation, and the 3-way fit check (VRAM + context + agent compatibility) so you stop downloading models that can't run.
version: 1.0.0
author: Postlethwaite Labs
license: MIT
domain: mlops
subdomain: inference
tags:
  - llm
  - gpu
  - vram
  - context-length
  - model-fit
  - kv-cache
  - agent
  - ollama
  - local-llm
---

# LLM GPU Fit

Quick, honest answer to "can I actually run this model?" — the 3-way
intersection of VRAM, context length, and agent compatibility. Built from
real testing on an 11GB GPU, not marketing math.

## When to Use

- "Can I run model X on my GPU?" — you want the answer BEFORE downloading 5GB.
- You're choosing a local model for an AI agent and need a minimum context
  window (64K+ is common for agent use).
- You're comparing two candidate models of similar size but different
  architecture (e.g. Llama vs Qwen) and want to know which fits.
- Your model "fits" on paper but crashes or responds with empty output at
  load time — you want the reason why.

## The 3-Way Fit Check

A model is actually usable only if ALL THREE hold:

1. **VRAM**: weights + KV cache ≤ your GPU's memory (leave ~500MB-1GB
   headroom for the runtime, CUDA context, tokeniser).
2. **Context**: the model's context window ≥ your requirement (agents
   usually need ≥64,000 tokens; some platforms hard-refuse below that).
3. **Agent-compatible**: output arrives in the normal `content` field (not
   a separate "thinking" field), and tool calls come back as structured
   `tool_calls` — not prose text.

Fail any one and the model is a no-go for that GPU/task combo — regardless
of how new or popular it is.

## The Part Everyone Gets Wrong: KV Cache

KV cache cost = tokens × layers × heads × head_dim × 2. The **attention
architecture** decides the multiplier:

| Architecture | KV cache at 128K (7-8B model) | Notes |
|---|---|---|
| **MHA** (Llama 3.1, older models) | ~16GB | 1x — huge |
| **GQA** (Qwen2.5, Mistral, Gemma 2+) | ~1-4GB | 4-8x smaller |
| **MQA** (some older models) | ~1GB | smallest |

**Concrete result (tested on an 11GB GPU):** Qwen2.5 7B (GQA) fits 128K
context in ~6-7GB total. Llama 3.1 8B (MHA) tops out around 32K on the
same card — same parameter count, 4x less usable context.

**Rule: never assume context costs the same across models. Check the
architecture tag (GQA/MHA) on the model page before doing the math.**

## Procedure

### 1. Define your requirements

- VRAM: `nvidia-smi --query-gpu=memory.total,memory.free --format=csv,noheader`
- Min context: agent requirement (64K for many agents; less for plain chat)
- VRAM budget for weights: free VRAM − ~1GB headroom

### 2. Screen candidates (30 seconds each, no downloads)

For each model page (e.g. Ollama library):
- Weights size for your quant (Q4_K_M is the common default; compare same-quant only)
- Architecture (GQA/MHA) → estimate KV cache at your target context
- "thinking" tag → suspect for agent/OpenAI-compatible routes

### 3. Quick estimate

```
total_estimate = weights + kv_cache_estimate
```

- `total_estimate + 1GB ≤ free VRAM` → worth pulling
- `total_estimate ≈ VRAM` → will offload to CPU/RAM; slow but maybe workable
- `total_estimate > VRAM` → reject for that context; shorten context,
  smaller quant, smaller model, or accept CPU offload

### 4. Pull and test for real

Even after passing steps 1-3, verify with the OpenAI-compatible endpoint
(`/v1/chat/completions`) — the same route agents use:

```bash
curl -s http://<host>:11434/v1/chat/completions \
  -d '{"model":"<name>","messages":[{"role":"user","content":"Say exactly: Hello"}],"max_tokens":20}'
```

- Response content in the `content` field → agent-ready.
- Empty `content` + reasoning elsewhere → thinking-field model, not agent-ready.
- No response/timeout at load → VRAM overshoot, or the server crashed loading it.

### 5. Adjust context with a variant

If the base model's default context is smaller than its true max, create a
context variant:

```bash
curl -s --max-time 120 http://<host>:11434/api/create \
  -d '{"name":"<model>-128k","from":"<base-model>","parameters":{"num_ctx":131072}}'
```

Verify with `/api/show` that `num_ctx` took effect.

## Decision Reference (tested on 11GB GPU, Q4_K_M)

| Model | Arch | Weights | 128K context? | Agent-ready? | Verdict |
|---|---|---|---|---|---|
| Qwen2.5 7B | GQA | 4.7GB | ✅ | ✅ | ✅ Best pick |
| Llama 3.1 8B | MHA | 4.9GB | ❌ (≈32K max) | ✅ | ⚠️ Context-limited |
| Qwen3.x 8B | GQA | ~5GB | ✅ | ❌ thinking field | ❌ |
| Gemma 4 8B | GQA | ~5GB | ✅ | ❌ thinking field | ❌ |
| LFM2.5 8B | MoE | ~5GB | ✅ | ❌ thinking field | ❌ |
| Granite 4.2 8B | GQA | 5.3GB | graph says yes | ⚠️ | ⚠️ crashed at load on 11GB |

**The pattern:** the newest 7-8B releases (Qwen3, Gemma 4, LFM) added
reasoning/thinking fields that route around the OpenAI-compatible content
channel — empty agent responses despite the model working via its native
API. Qwen2.5 7B (older, but GQA + standard chat format) remains the
reliable pick for 8-12GB GPUs at long context.

## Pitfalls

- **Same size ≠ same context cost.** MHA vs GQA changes KV cache 4-8x.
- **"Newest" is not a fit criterion.** Fit = the 3 checks, not release date.
- **Quant mixing.** Q4 vs Q8 sizes aren't comparable. Normalise first.
- **Paper-fit vs real-fit.** A model can pass the math and still crash at
  load (observed: Granite 4.2 8B on 11GB). Leave real headroom.
- **Empty output ≠ broken model.** Usually the thinking-field issue — works
  via raw API, puts reasoning outside `content`.
- **Base-model deletion breaks variants.** Delete context variants before
  the base, or re-pull + recreate.
- **Server-reported context is what matters** — an agent reads `/api/show` /
  the OpenAI metadata, not your desired config. Verify what the server
  reports before wiring anything.

## Verification

- [ ] Every candidate checked for: Q4_K_M size, architecture (GQA/MHA), thinking tag
- [ ] VRAM estimate uses architecture-specific KV cache + 1GB headroom
- [ ] Context minimum decided up front and verified against server-reported context
- [ ] Finalists pass `/v1/chat/completions` with real content in `content`
- [ ] If a model failed, you know exactly which of the 3 checks it failed
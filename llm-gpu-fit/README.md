# LLM GPU Fit

**Check if an LLM actually fits your GPU before you download 5GB you can't run.**

A decision procedure for the three-way intersection everyone gets wrong:
**VRAM, context length, and agent compatibility**. Built from real testing
on an 11GB GPU — including the discovery that two same-size models (Qwen2.5
7B vs Llama 3.1 8B) differ 4x in usable context because of attention
architecture (GQA vs MHA).

## What you get

- The **3-way fit check** — VRAM + context minimum + agent compatibility.
- **Architecture-aware KV cache math** — the part every "just use X" advice
  gets wrong.
- A **tested decision table** for common 8B-class models on an 11GB card:
  which ones fit 128K context AND work with agent tool-calling.
- The **thinking-field trap** explained: why newer reasoning models return
  *empty* output through OpenAI-compatible endpoints even though they work.
- Context-variant creation (`/api/create`) for pushing a model to its real
  context limit.

## Quick example

`nvidia-smi` shows 11GB free. You want a model at 128K context for your
agent.

- **Qwen2.5 7B** (GQA): 4.7GB weights + ~1-2GB KV cache = ✅ fits
- **Llama 3.1 8B** (MHA): 4.9GB weights + ~16GB KV cache = ❌ doesn't
  (maxes out around 32K on the same card)

Same parameter count. 4x difference in usable context. That's the point of
this skill.

## Files

- `SKILL.md` — the full decision procedure (drop into any
  SKILL.md-compatible agent: Claude Code, Codex CLI, Cursor, Hermes,
  OpenCode, Windsurf).

## License

MIT — free forever. If it saved you from downloading another model that
can't run, [buy me a coffee](https://buymeacoffee.com/postlethwaite) ☕
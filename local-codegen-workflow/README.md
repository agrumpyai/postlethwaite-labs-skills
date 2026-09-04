# Local Codegen Workflow

Generate production code with a local LLM on the GPU you already own — and
stop paying per-token API pricing for work a coder-class model can do locally.

## What it does

Turns any OpenAI-compatible local LLM server (LM Studio, Ollama, llama.cpp,
vLLM) into a code-writing workhorse. You write a tight spec, a small script
auto-loads the model at a VRAM-safe context, the model writes the file, and a
review checklist + test gate keep the output trustworthy.

**Model-agnostic:** works with any LLM; coder-class models (Qwen2.5-Coder,
DeepSeek-Coder, CodeLlama, GPT-OSS) give the best results. Reference build:
LM Studio + Qwen2.5-Coder-14B on a 16GB GPU.

## What's inside

- **`tools/genfile.py`** — the spec → model → file bridge (works standalone)
- **`templates/spec-template.md`** — the spec skeleton that makes local models
  produce ~75% usable code
- **`references/lmstudio-v1-api.md`** — the model auto-loading API: how to
  load a model at a VRAM-safe context so it doesn't OOM (the `"terminated"`
  trap), plus a per-VRAM context table
- **SKILL.md** — the full workflow: 5 steps, a 13-item review checklist of
  real bug classes, a worked example, troubleshooting, and a test gate

## Quickstart

```bash
pip install httpx
export LMSTUDIO_BASE_URL=http://localhost:1234/v1   # your server
python tools/genfile.py specs/my-module.md app/my_module.py
```

Then review (checklist in SKILL.md), run the generated tests, commit.

## Why it exists

Local 14B models are good enough to write most boilerplate and CRUD — but
raw output is full of subtle bugs. This skill packages the *loop* that makes
local codegen trustworthy: a spec that models can nail, auto-loading that just
works, a review checklist of the 13 bug classes local models hit, and a
2-strike rule so you never flail. It's the difference between hacking together
a script and having a repeatable pipeline.

## License

MIT — see LICENSE.
## Support

If this skill saves you API tokens, [buy me a coffee](https://buymeacoffee.com/postlethwaite) ☕

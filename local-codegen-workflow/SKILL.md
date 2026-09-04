---
name: local-codegen-workflow
description: Use when generating code with a local LLM (LM Studio/Ollama/vLLM) to save API tokens. Spec-driven codegen on your own GPU, with auto model-swapping, a review checklist, and a test gate. Works with any OpenAI-compatible model; coder-class models give best results.
version: 1.0.0
author: Postlethwaite Labs
license: MIT
platforms: [linux, macos, windows]
domain: mlops
subdomain: inference
tags:
  - codegen
  - local-llm
  - lm-studio
  - ollama
  - gpu
  - token-savings
  - spec-driven
metadata:
  hermes:
    tags: [codegen, local-llm, lm-studio, ollama, gpu, token-savings, spec-driven]
    related_skills: [local-llm-management, gpu-model-fit, model-router]
---

# Local Codegen Workflow

Generate production code with a local LLM on a GPU you already own, instead of
paying per-token APIs. The skill covers the whole loop: writing a spec the
model can actually nail, auto-loading the model at a VRAM-safe context,
generating, reviewing (with a bug checklist), testing, and committing.

**Model-agnostic:** the workflow works with ANY LLM that speaks an
OpenAI-compatible API (`/v1/chat/completions`) — LM Studio, Ollama, llama.cpp,
vLLM, KoboldCpp, local or remote. Coder-class models (Qwen2.5-Coder,
DeepSeek-Coder, CodeLlama, GPT-OSS, etc.) produce the best results and are
recommended, but the method itself does not depend on any specific model.

Reference implementation (what this skill was validated against): LM Studio +
Qwen2.5-Coder-14B on a 16GB GPU.

## Quickstart

1. Install the dependencies: `pip install httpx`
2. Point at your local server (change if not LM Studio on this machine):
   `export LMSTUDIO_BASE_URL=http://localhost:1234/v1`
3. Pick a coder-class model and load it (or let the script auto-load it — see
   Step 3): `qwen2.5-coder-14b-instruct` is the reference.
4. Write a spec (use `templates/spec-template.md`):
   `python tools/genfile.py specs/db.py.md app/db.py`
5. Review the output against the checklist (Step 4), run its tests, commit.

You're now generating code on hardware you already own instead of paying
per-token API pricing.

## Is it worth it? (the cost equation)

A 14B Q4 model on a 16GB GPU writes code at roughly the speed of a small
API model, for **zero marginal cost** — you own the hardware. Typical math:

- A GPT-4o/Claude-class codegen session: 50-200K output tokens × high per-token
  rate = **$1-10 per working session**.
- The same session through a local 14B: **$0**. Electricity is the only cost
  (~50-100W under load).

Payback: one heavy week of codegen pays for the electricity for months. The
tradeoff is quality — local 14B models need the spec + review loop in this
skill to reach ~75% usable output. That's exactly what the next five steps
deliver.

## When to Use

- You want to reduce API token spend by routing code generation to local hardware
- You have a GPU box with LM Studio / Ollama and an 8–14B coder-class model
  (or larger, if you have the VRAM)
- You're building a multi-file project and want ~70-80% of boilerplate
  generated, with a human/agent review pass over the rest
- You have a spec or can write one, and want a repeatable generate → review → test loop

**Don't use for:** one-off small edits to existing code (writing them by hand
is faster than the round-trip), or when model quality would cost more in
review time than it saves.

## Core Principle: Spec → Generate → Review → Test → Commit

The model is the junior developer. The spec is the ticket. YOU are the senior
reviewer. Generated code is never trusted until it passes review and tests.

```
[spec.md] → [genfile.py] → [local model generates] → [review + patch] → [pytest] → [commit]
                                             ↑                                   ↓
                                        (bug checklist)                 (2-strike rule)
```

## Prerequisites

1. A local LLM server with an OpenAI-compatible endpoint (`/v1/chat/completions`)
   — LM Studio, Ollama, llama.cpp, vLLM all work.
2. A coder-class model loaded or downloadable (Qwen2.5-Coder-14B-Instruct
   Q4_K_M ≈ 9GB is the reference; 7B works on 8GB cards).
3. A GPU big enough for model + KV cache at your working context
   (16GB runs 14B at 32K; see `gpu-model-fit` for VRAM math).
4. Python 3.11+ and httpx (`pip install httpx`).

## The 5 Steps

### Step 1 — Write the spec

A good spec is what makes a 14B model produce ~75% usable code instead of 40%.
It is NOT a one-line instruction. It contains:

- **Exact function signatures and return shapes** — the model should never
  invent an API contract.
- **Environment constraints** — Python version, deps, "no third-party deps",
  "standard library only". Be explicit.
- **Behavioural edge cases** — empty input, missing rows, concurrency,
  "return []" vs "raise". List them.
- **Schema / data shapes** — if there's a DB or data structure, give the exact
  columns/keys.
- **"Output ONLY the code"** — models love adding prose, markdown fences and
  commentary. Kill it up front.
- **Tests are generated from the same spec** — spec the behaviour, generate
  module + tests separately.

Spec template (see `templates/spec-template.md`):
```
# Spec: <module>

Write a single Python module `<path>` for <purpose>.

## Environment & constraints
- <python version>, <allowed deps>, <standard library only?>...
- <module-level constants with defaults>

## Function 1: <name>(<params>) -> <return type>
- <behaviour, one line>
- <edge cases: empty input → X, missing → Y>
- <exact algorithm steps when relevant>

## Function 2: ...

## Output format
Output ONLY the module code in one code block. No tests here.
```

### Step 2 — Run genfile.py (auto-loads the model)

`tools/genfile.py` (shipped in this skill) sends the spec to the local endpoint
and writes the response to your target file.

```bash
python tools/genfile.py specs/app-db.py.md app/db.py
# genfile: ensuring qwen2.5-coder-14b-instruct loaded (ctx 32768) …
# genfile: qwen2.5-coder-14b-instruct ready.
# genfile: wrote app/db.py (6746 chars)
```

Environment knobs:
- `LMSTUDIO_BASE_URL` (default `http://localhost:1234/v1`)
- `CODEGEN_CONTEXT` (default `32768`) — see Model Management below
- `--model`, `--max-tokens`, `--stdout` flags

### Step 3 — Model auto-loading (LM Studio v1 API)

**The problem:** LM Studio JIT-loads models with whatever context length the
model is configured to — often the GGUF max (131K for Qwen2.5-Coder-14B). At
that context the KV cache alone can exceed 16GB, so the model loads but OOMs
on the first real generation. Tiny requests (a fib test) succeed; real ones
die with `{"error":"terminated"}`.

**The fix:** load explicitly at a VRAM-safe context via the v1 REST API, which
ships in LM Studio 0.4.0+:

```
POST /api/v1/models/load    {"model": "qwen2.5-coder-14b-instruct", "context_length": 32768, "flash_attention": true}
POST /api/v1/models/unload  {"instance_id": "openai/gpt-oss-20b"}
GET  /api/v1/models         → {"models":[{key, loaded_instances: [...]}]}  # [] = unloaded
```

Key facts learned the hard way:
- **`{"error":"terminated"}` (400) means OOM/wrong-context, NOT "model not
  loaded".** Check `loaded_instances` in `/api/v1/models` before suspecting
  anything else.
- **The v1 API lives at the server root** (`http://host:1234/api/v1/*`),
  separate from OpenAI-compat (`http://host:1234/v1/*`). The older v0 API has
  NO load/unload — don't look there.
- **16GB box, two models:** LM Studio can keep both "loaded" by partially
  CPU-offloading the second — it runs slower but works. Eviction isn't always
  automatic.
- Coder-class context sweet spot: 14B at 32768 ≈ 9.5GB weights + ~5GB KV =
  fits 16GB with headroom (flash attention on). Per-VRAM context table in
  `references/lmstudio-v1-api.md`.

`ensure_loaded(model, context_length, ...)` reference implementation:
loads the model, unloads others only if VRAM is short, polls until it's in
`loaded_instances`, never raises — returns bool so callers degrade gracefully.

### Step 4 — Review + patch (the value-add)

Generated code is NEVER shipped un-reviewed. The 14B model produces solid
structure but fumbles subtle details. Known bug classes (from a real build):

| # | Bug class | Symptom | Fix |
|---|---|---|---|
| 1 | **Connection leak** | sqlite3 `with connect()` commits but never closes | use an explicit session contextmanager that closes |
| 2 | **Stale index** | FTS/derived index rebuilt on a DIFFERENT connection → uncommitted writes invisible | pass the SAME conn into the sync |
| 3 | **Empty-list SQL** | `WHERE id IN ()` crash on empty input | early-return `[]` |
| 4 | **No-op updates** | `UPDATE ... SET WHERE` with no fields | early-return if no fields |
| 5 | **Keyword-kwarg misuse** | `sqlite3.connect(enable_foreign_keys=True)` isn't a kwarg | PRAGMA after connect |
| 6 | **Wrong-API drift** | `db.fts_search()` doesn't return the chunk id the caller needs | include `rowid AS id` |
| 7 | **Module imported, called as fn** | `from x import y` vs `import x; x.y()` mismatch | check import vs call style |
| 8 | **Stream parsing** | SSE lines are `str` not `bytes`; `httpx.loads` doesn't exist | `json.loads`, compare str |
| 9 | **File stream double-read** | size-check loop exhausts upload stream; write loop writes nothing | `seek(0)` before write |
| 10 | **Row vs dict** | `sqlite3.Row` has no `.get()` | use `row["col"]` / `in row.keys()` |
| 11 | **Exception returned, not raised** | test fakes `return RuntimeError()` instead of `raise` | raise in fakes |
| 12 | **Mutation of caller's list** | prompt builder `pop()`s the caller's results | work on a copy |
| 13 | **Filesystem type mismatch** | `Path` bound raw into sqlite → binding error | `str(path)` |

Run order: syntax check → read the file → diff against the spec → run tests →
fix anything that fails the checklist → re-run tests.

### Step 5 — Test gate + commit

- Tests are generated from the same spec and run against the real code.
- **2-strike rule:** if a file comes back wrong twice (fails review or tests
  twice on the same issue), write it by hand. Don't flail — the round-trip
  cost now exceeds the token saving.
- Commit only green code, with a message noting it was AI-generated +
  reviewed (e.g. `feat: db.py schema + FTS5 layer (AI-gen, reviewed)`).

## Worked Example (the whole loop, one file)

**Spec (`specs/fib.md`):** a single function, tightly specified.

```markdown
Write a single Python function `fib(n)` that returns the n-th Fibonacci number
(0-indexed, fib(0)=0, fib(1)=1). Iterative. Docstring + a main block printing
fib(10). Standard library only. Output ONLY the code.
```

**Generate:**
```bash
python tools/genfile.py specs/fib.md fib.py
# genfile: ensuring qwen2.5-coder-14b-instruct loaded (ctx 32768) …
# genfile: qwen2.5-coder-14b-instruct ready.
# genfile: wrote fib.py (387 chars)
```

**Review:** the model returns a correct iterative `fib` with edge-case guard
(`n < 0` raises). Passes the checklist — no bugs in 8 lines.

**Verify:**
```bash
python fib.py   # → 55
```

**Commit:**
```bash
git add fib.py && git commit -m "feat: fib (AI-gen, reviewed)"
```

That's the whole loop on a toy example. On a real module the steps are
identical — only the spec is longer and the review checklist does more work.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `genfile: FAILED — Client error '400'` with `{"error":"terminated"}` | Model loaded at too-big context → OOM on generation | Load at a VRAM-safe context (Step 3); check `CODEGEN_CONTEXT` |
| `genfile: FAILED — ConnectError` | Server not running / wrong port | Start LM Studio (or your server); check `LMSTUDIO_BASE_URL` |
| `genfile: FAILED — Empty completion` | Model returned nothing (thinking-field models) | Use a non-thinking model (Qwen2.5-Coder works; avoid Qwen3-style CoT models for this) |
| `401 Unauthorized` | Server requires an API key | LM Studio: enable + set key in settings; pass via `LMSTUDIO_BASE_URL` config or env |
| Auto-load log says `skipped or unavailable` | Server isn't LM Studio 0.4.0+ (Ollama/vLLM/llama.cpp) | Fine — the server's own JIT loading handles it; verify the model answers manually |
| Output has markdown fences / prose | Model ignored "output ONLY code" | Already handled by `extract_code`; if prose slips through, tighten the spec |

## Pitfalls

- **JIT context trap** — never assume JIT loading "just works". Load at a
  context you've verified fits VRAM.
- **"terminated" ≠ unloaded** — it's OOM or context, almost always.
- **v0 ≠ v1** — model management is v1-only; the OpenAI-compat path has no
  load/unload.
- **Tiny smoke tests lie** — a fib test passing doesn't mean real generation
  works; test with a realistic spec first.
- **Don't use for edits** — surgical changes to existing code beat the
  generate-review round-trip every time.
- **Reviewer skill matters more than model** — the value is the checklist +
  test gate, not the generation. Don't ship raw output.

## Verification

- [ ] Spec written with exact signatures + edge cases + "output ONLY code"
- [ ] `genfile.py` auto-loads the model at a VRAM-safe context (check
      `GET /api/v1/models` shows `loaded_instances` non-empty)
- [ ] Generated file passes syntax check + review checklist
- [ ] Tests (generated from same spec) pass before commit
- [ ] 2-strike rule applied — no flailing on a bad file

## Files

```
tools/genfile.py                # spec → local model → file (standalone)
templates/spec-template.md      # reusable spec skeleton
references/lmstudio-v1-api.md   # load/unload/list endpoints + pitfalls
README.md, LICENSE              # package metadata (MIT)
```

## Related

- `local-llm-management` — testing/wiring local models into agents, aliases
- `gpu-model-fit` — VRAM/context math before you pick a model
- `model-router` — routing tasks across providers with fallback
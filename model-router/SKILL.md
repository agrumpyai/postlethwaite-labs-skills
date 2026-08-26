---
name: model-router
description: Route AI tasks across providers with automatic fallback.
version: 1.0.0
author: Emm & Postlethwaite, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [model-routing, fallback, providers, local-llm, gpu, infrastructure]
    related_skills: []
---

# Model Router Skill

Teaches an AI agent how to intelligently route tasks across multiple model providers (cloud APIs, local Ollama, LM Studio, vLLM, llama.cpp, and any OpenAI-compatible endpoint) with automatic fallback when a provider fails. The skill is a **decision framework** — it doesn't hardcode any specific provider, model, or hardware config. The user supplies their own config; the agent applies the pattern.

## When to Use

- Your primary model provider is rate-limited, down, or returning errors and you want automatic fallback.
- You have multiple local LLM backends (e.g. Ollama, LM Studio, llama.cpp) and want to use the best available one per task.
- You want to save API costs by routing simple tasks to local models and complex tasks to cloud models.
- You're setting up a new machine and want to auto-discover what local providers are available.
- You want to validate that your fallback chain works before relying on it in production.

**Don't use for:** One-shot model switching (use `/model` command instead). Replacing a load balancer for production multi-user inference.

## Prerequisites

- Python 3.8+ with stdlib only (no external dependencies).
- For GPU detection: one of `nvidia-smi` (NVIDIA), `rocm-smi` or `amd-smi` (AMD), `xpu-smi` (Intel), or `sysctl` (Apple Silicon). Detection is optional and graceful — the skill works without any GPU.
- A config file at `~/.model-router/config.json` (JSON format, stdlib) or `~/.model-router/config.yaml` (YAML format, requires PyYAML). Create one from the example file, or run `model-router discover` to auto-generate a starter.

## How It Works (the decision framework)

The agent follows this reasoning process for every routing decision:

```
User requests a task
       ↓
1. CONSULT the user's config
   - Read the ordered provider chain
       ↓
2. ATTEMPT the primary provider
   - If it succeeds → done
   - If it 429s (rate limited) →
       ↓
3. FALL BACK silently
   - Try the next provider in chain
   - If it succeeds → done (inform user of fallback)
   - If it also fails → continue down chain
       ↓
4. If all providers exhausted → report failure with details
```

**Key design principle: don't probe first, just route.** Every health check call burns API quota. On a rate-limited free tier, those probe calls can be the difference between getting a response and hitting your limit. The chain is designed to **try, fail, and fall back** — not to probe, then route.

The agent's own reasoning handles the specifics — the skill provides the structure, not the implementation.

## Quick Reference

| Command | What it does |
|---|---|
| `model-router discover` | Auto-detect local GPU + providers, output starter config |
| `model-router validate` | Test the configured chain end-to-end |
| `model-router status` | Show current config and provider health |
| `model-router route <task>` | Route a specific task through the chain (dry-run) |

## Procedure

### Step 1: Initial Setup

Create a config file at `~/.model-router/config.json` (or `config.yaml` for YAML). Use the provided `config.yaml.example` as a template, or run `model-router discover` to auto-generate one.

The config defines an ordered list of providers. Each entry has:
- `name`: a label for logging
- `provider`: one of `openrouter`, `openai`, `anthropic`, `ollama`, `lmstudio`, `llamacpp`, `vllm`, `custom`
- `model`: the model name to use
- `base_url`: (optional) the API endpoint URL
- `api_key`: (optional) the API key, or reference an env var
- `tier`: `cloud` or `local` — used for task-to-tier routing

**JSON format (stdlib, no dependencies):**

```json
{
  "routers": [
    {
      "name": "primary-cloud",
      "provider": "openrouter",
      "model": "deepseek/deepseek-v4-flash",
      "tier": "cloud"
    },
    {
      "name": "local-ollama",
      "provider": "ollama",
      "model": "llama3:70b",
      "base_url": "http://localhost:11434",
      "tier": "local"
    }
  ]
}
```

**YAML format (more readable, requires PyYAML):**

```yaml
routers:
  - name: primary-cloud
    provider: openrouter
    model: deepseek/deepseek-v4-flash
    tier: cloud

  - name: local-ollama
    provider: ollama
    model: llama3:70b
    base_url: http://localhost:11434
    tier: local
```

### Step 2: Auto-Discovery (optional)

Run the discovery script to detect what's running on your machine:

```
model-router discover
```

This scans for:
- **GPU**: any vendor (NVIDIA, AMD, Intel, Apple)
- **Local providers**: Ollama (11434), LM Studio (1234), llama.cpp (8080), vLLM (8000)
- **Running models**: what's currently loaded on each provider

It outputs a starter config you can save and edit.

### Step 3: Validate the Chain

Run validation to test every provider in your config:

```
model-router validate
```

This probes each endpoint, checks auth, and reports which models are available. If a provider is down, it's logged as a warning — not a failure. The chain is designed to skip unavailable providers gracefully.

### Step 4: Route

Once configured, use the skill's decision framework for any task:

```
# The agent will automatically:
# 1. Classify the task
# 2. Consult the config
# 3. Try providers in order
# 4. Fall back on failure
# 5. Report the routing decision
```

You don't need to specify which provider to use — the agent handles it based on the config and the task type.

### Step 5: Monitor and Adjust

Check provider health at any time:

```
model-router status
```

This shows:
- Current config
- Each provider's health (green/yellow/red)
- Last known good models
- GPU status (if available)

## Provider Reference

| Provider | `provider` value | Default port | Auth method | Probe endpoint |
|---|---|---|---|---|
| OpenRouter | `openrouter` | — | API key (env: `OPENROUTER_API_KEY`) | `GET /v1/models` |
| OpenAI | `openai` | — | API key (env: `OPENAI_API_KEY`) | `GET /v1/models` |
| Anthropic | `anthropic` | — | API key (env: `ANTHROPIC_API_KEY`) | `GET /v1/models` |
| Ollama | `ollama` | 11434 | None by default | `GET /api/tags` |
| LM Studio | `lmstudio` | 1234 | Bearer token | `GET /v1/models` |
| llama.cpp | `llamacpp` | 8080 | None by default | `GET /v1/models` |
| vLLM | `vllm` | 8000 | API key (env var) | `GET /v1/models` |
| Custom | `custom` | any | Configurable | `GET /v1/models` |

## Scripts

The `scripts/` directory contains helper scripts. These are optional — the SKILL.md pattern is the real product. The scripts make common tasks easier:

- **`discover.py`**: Auto-detect GPU + local providers. Vendor-agnostic.
- **`probe.py`**: Check if a provider endpoint is alive and what models it serves.
- **`route.py`**: Validate a full routing chain against a config file.

All scripts use Python stdlib only — no external requirements.

## GPU Detection (Vendor-Agnostic)

The discovery script checks for GPU hardware using these commands, in order:

| Vendor | Command | Info gathered |
|---|---|---|
| NVIDIA | `nvidia-smi --query-gpu=...` | Name, VRAM, driver, temp |
| AMD (ROCm) | `rocm-smi --showhw` | Name, VRAM, driver |
| AMD (new) | `amd-smi static` | Name, VRAM, driver |
| Intel | `xpu-smi discovery` | Name, memory, driver |
| Apple Silicon | `sysctl -n hw.perflevel0.name` | Chip name |

If none of these commands are available, the script reports "no GPU detected" and the skill works in CPU-only / cloud-only mode. This is not an error — the skill is designed to function without a GPU.

## Pitfalls

- **No GPU is not a problem.** The skill works with cloud-only providers. GPU detection is informational.
- **API keys belong in environment variables, not in the config file.** The config supports `api_key_env` to reference env vars. Never commit keys to version control.
- **Local providers may not be running.** The validation step will report them as unavailable. Start them before expecting routing to work.
- **Rate limits (429) are handled by fallback.** The first provider gets a 429 → the agent tries the next provider. This is the core value of the skill.
- **Auth errors (401/403) are NOT the same as rate limits.** A 401 means the API key is wrong or missing. The agent will skip that provider and report the auth issue.
- **Model names are case-sensitive.** The exact model ID from the provider's model listing must be used.
- **The chain is tried in order, not in parallel.** If the first provider is slow to time out, the full chain may take 30+ seconds to exhaust. Set reasonable timeouts.
- **This skill teaches a pattern, not a config.** Every user's setup is different. The skill provides the structure; the user fills in the specifics.

### ⚠️ Hard lessons from production use

- **Probing makes rate limits worse, not better.** Every `/v1/models` health check call eats into your API quota. On free/cheap tiers where every call counts, don't probe before routing — just try the provider and fall back on failure. The discovery and validate scripts are for **initial setup only**, not for live checking.
- **A model that responds with nonsense is WORSE than no fallback at all.** We tested Gemma 4 as a fallback — it responded instantly but produced broken template-leak garbage that looked valid. A wrong answer delivered confidently is more damaging than an error message. Always verify your fallback model can actually handle the agent loop (tool calling, system prompts, structured outputs) before trusting it in production.
- **Free tiers are rate-limited at peak times.** Your cloud provider working at 3am may 429 every call at 3pm. Build your chain assuming the primary WILL fail during peak hours — not as an exception, but as the baseline.
- **A model that's "too big" for your GPU is worse than no local fallback.** If your fallback model spills from VRAM to system RAM, it'll be so slow that you'd have been better off waiting for the cloud provider to recover. Benchmark latency before relying on a fallback.
- **Local models may lack tool-calling capability.** Not every model supports function calling or structured output. If your agent depends on tools, make sure your fallback model supports them too — or the fallback will fail on its first tool call.

## Verification

- [ ] `model-router discover` runs without errors (even if it finds nothing)
- [ ] `model-router validate` probes each configured endpoint and reports results
- [ ] `model-router status` shows provider health without crashing
- [ ] A config with one working provider completes a route successfully
- [ ] A config with a failing provider falls back to the next in chain
- [ ] GPU detection works on any vendor (or gracefully reports none)
- [ ] No hardcoded IPs, tokens, or model names appear in any file
## ☕ Support

If this skill helps you, consider [buying me a coffee](https://buymeacoffee.com/postlethwaitelabs).

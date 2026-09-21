---
name: openrouter-cost-watch
description: Watch OpenRouter model prices and alert when token costs shift — fetch live per-million-token prices, track a baseline, and get pinged only when input or output moves past your threshold. Zero recurring tokens to run.
version: 1.0.0
author: Postlethwaite Labs
license: MIT
domain: mlops
subdomain: inference
tags:
  - openrouter
  - pricing
  - cost
  - monitoring
  - tokens
  - llm
  - alerts
  - cron
external_urls:
  - https://openrouter.ai/api/v1/models
permissions:
  - network
---

# OpenRouter Cost Watch

Track what you're actually being charged for LLM API calls and get alerted
only when it matters. Queries OpenRouter's public model catalog, converts
per-token rates to per-million-token prices, holds a rolling baseline, and
flags any model whose input or output price moves past your threshold.

Deliberately costs **zero tokens** to run: the recurring check is a plain
script scheduled by the agent's cron — no LLM in the loop.

## When to Use

- You build on top of model APIs and want to know when your running cost
  changes (providers reprice without fanfare).
- You're comparing models and want a living record of price drift, not a
  one-off "what does X cost today" lookup.
- You want a standing, hands-off alert: "tell me if any of my tracked
  models moves more than 25% on input or output."

## How It Works

1. **Fetch** live prices from `https://openrouter.ai/api/v1/models`
   (public, no key required for reads).
2. **Normalise** per-token quotes to per-million-token ($/M) — the unit
   everyone actually compares.
3. **Compare** against the last snapshot (a JSON baseline you keep).
4. **Alert** only when a model's input or output price moves past your
   thresholds (a % change, floored by a minimum absolute change so cheap
   models' 0.5¢ wiggles don't spam you).
5. **Update** the baseline so next run compares against *this* run.

## Setup (once)

### 1. Copy the example config

```bash
mkdir -p ~/.openrouter-cost-watch
cp config.example.json ~/.openrouter-cost-watch/config.json
```

Edit `config.json`: choose the models to track and your thresholds.

```json
{
  "models": [
    "deepseek/deepseek-v4-flash-0731",
    "qwen/qwen3.7-flash"
  ],
  "in_pct": 25,
  "out_pct": 25,
  "min_abs_usd": 0.02
}
```

- `models`: exact OpenRouter model IDs (`/api/v1/models` → `id`).
- `in_pct` / `out_pct`: alert when input / output price moves by at least
  this percentage from the last baseline.
- `min_abs_usd`: ignore changes smaller than this absolute amount (US$ per
  million tokens) — filters noise on ultra-cheap models.

### 2. Initialise the baseline

```bash
python3 watch.py init --config ~/.openrouter-cost-watch/config.json
```

`init` fetches current prices and writes `baseline.json` next to the
config. **Do not schedule before this succeeds once** — you want a real
first observation, not a guess.

### 3. Schedule the recurring check

Run it as a plain script on a schedule (agent cron, system cron, or your
orchestrator of choice). It prints a report to stdout; schedule it to
deliver that output when meaningful.

```bash
python3 watch.py --config ~/.openrouter-cost-watch/config.json
```

- **Change detected** → prints a "PRICE CHANGES" report with ▲/▼ arrows,
  old → new values, and percentage.
- **Stable** → prints a short "NO SIGNIFICANT CHANGES" line plus the
  current table, and refreshes the baseline.

The script updates the baseline on every successful run, so the alert
logic stays deterministic against stored state and will not re-alert on
the same price twice.

### Agent cron (zero-token) pattern

If your agent supports a `no_agent` script cron (scheduler runs a script
and delivers its stdout verbatim), wire it like this:

- **Schedule:** whatever cadence suits (e.g. weekly).
- **Script:** `python3 <path>/watch.py --config ~/.openrouter-cost-watch/config.json`
- **No LLM involved** — stdout is delivered as-is.

## Output Example

```
🔔 OPENROUTER PRICE CHANGES (vs last run)

  ▲ deepseek/deepseek-v4-flash-0731 (in): $0.0400 → $0.0620 (+55%)
  ▼ qwen/qwen3.7-flash (out): $0.1300 → $0.1000 (-23%)

(checked 2026-09-21 22:00 UTC; auto-updated baseline)
```

## Pitfalls

- **`openrouter/auto` and router aliases return a sentinel price** (`-1e6`).
  Filter any model whose price is `< 0` before comparing — they're not real
  quotes. (The example script does this; keep it.)
- **Per-token vs per-million confusion.** The API returns per-token
  fractions (e.g. `0.00000004`); multiply by 1,000,000 before displaying
  or comparing. Mixing units is the #1 bug.
- **Never overwrite a good baseline with a failed fetch.** If the API
  errors, report the failure and leave the last baseline intact — an
  unknown state is not a "no change" state.
- **Don't alert on a plain difference — alert on a floored % move.** A raw
  delta flags $0.01 → $0.02 on a $0.02 model as a 100% swing that may be
  noise. Use `% change` *and* a `min_abs_usd` floor.
- **Baseline auto-update is what prevents duplicate alerts.** Without
  refreshing state after a run, the next run re-alerts on the same change.

## Files

- `watch.py` — stdlib-only Python (urllib + json). No third-party deps.
- `config.example.json` — template config (copy, don't edit in place).
- `SKILL.md` / `README.md` — this documentation.

## Verification

- [ ] `watch.py init` succeeded once before scheduling
- [ ] Sentinels (negative prices) filtered, per-token → $/M converted
- [ ] Failed fetches leave the last good baseline untouched
- [ ] Alert condition is deterministic against stored baseline state
- [ ] A repeated unchanged run does not re-alert

# OpenRouter Cost Watch

Watch OpenRouter model prices and get alerted when token costs shift. Fetch live per-million-token prices, track a rolling baseline, and only get pinged when input or output price moves past your threshold.

Runs as a **plain stdlib Python script** — zero third-party dependencies and **zero LLM tokens** to operate (schedule it as a `no_agent` cron and the output is delivered verbatim).

## Why

API providers reprice without fanfare. If you build on model APIs, your running cost can change under you. This gives you a standing, hands-off "tell me when prices move" watch instead of one-off manual lookups.

## Quickstart

```bash
cp config.example.json ~/.openrouter-cost-watch/config.json
# edit config.json: your model IDs + thresholds

python3 watch.py init --config ~/.openrouter-cost-watch/config.json   # snapshot baseline
python3 watch.py      --config ~/.openrouter-cost-watch/config.json   # compare + alert
```

Schedule the `check` command however you like (agent `no_agent` cron, system cron, etc.).

## The alert logic

Alerts only when a tracked model's input **or** output price moves by at least `in_pct`/`out_pct` percent **and** by at least `min_abs_usd` (US$ per million tokens). The percentage + absolute floor filters noise on ultra-cheap models. The baseline auto-updates each run, so a repeated unchanged run never re-alerts.

Output:

```
OPENROUTER PRICE CHANGES (vs last run)

  UP deepseek/deepseek-v4-flash-0731 (in): $0.0400 -> $0.0620 (+55%)

(checked 2026-09-21 22:00 UTC; baseline auto-updated)
```

## Key behaviours

- Per-token API rates are converted to per-million-token US$ before comparing.
- `openrouter/auto` and router aliases that report a sentinel negative price are filtered out.
- A failed catalog fetch reports the error and **leaves the last good baseline untouched** — an unknown state is never treated as "no change".
- MIT licensed, free.

## Files

- `watch.py` — the monitor (stdlib only).
- `config.example.json` — template config (copy, don't edit in place).
- `SKILL.md` — full documentation and agent integration guide.

*Postlethwaite Labs — build free, useful agent tools.*

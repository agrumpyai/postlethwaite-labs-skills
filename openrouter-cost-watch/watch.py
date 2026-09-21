#!/usr/bin/env python3
"""OpenRouter Cost Watch — stdlib-only price monitor.

Fetches live per-million-token prices from OpenRouter's public model
catalog, compares against a stored baseline, and flags any tracked model
whose input or output price moved past the configured thresholds.

Zero third-party dependencies (urllib + json + sys + datetime). The
recurring run is meant to be scheduled as a plain script (agent `no_agent`
cron, system cron, etc.) so it costs no LLM tokens.

Usage:
    python3 watch.py init   --config <path-to-config.json>   # snapshot baseline
    python3 watch.py        --config <path-to-config.json>   # compare + auto-update
"""
import argparse
import datetime
import json
import os
import sys
import urllib.request

CATALOG_URL = "https://openrouter.ai/api/v1/models"
MILLION = 1_000_000
UA = "openrouter-cost-watch/1.0"


def fetch_prices():
    """Return {model_id: {"in": $/M, "out": $/M}} from the public catalog."""
    req = urllib.request.Request(CATALOG_URL, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=40) as r:
        data = json.load(r)
    out = {}
    for model in data.get("data", []):
        mid = model.get("id")
        pricing = model.get("pricing") or {}
        try:
            pin = float(pricing.get("prompt", 0))
            pout = float(pricing.get("completion", 0))
        except (TypeError, ValueError):
            continue
        # Some router/alias entries return a sentinel negative value (-1e6).
        if pin < 0 or pout < 0:
            continue
        out[mid] = {
            "in": round(pin * MILLION, 5),
            "out": round(pout * MILLION, 5),
        }
    return out


def load_config(path):
    with open(path) as f:
        return json.load(f)


def load_baseline(config):
    bl = config.get("baseline_path")
    if bl and os.path.exists(bl):
        with open(bl) as f:
            return json.load(f)
    return {"models": {}}


def save_baseline(config, baseline, now):
    bl = config.get("baseline_path")
    if not bl:
        bl = os.path.join(os.path.dirname(os.path.abspath(config.get("_cfg_path", "."))),
                          "baseline.json")
    os.makedirs(os.path.dirname(os.path.abspath(bl)), exist_ok=True)
    with open(bl, "w") as f:
        json.dump({"captured": now, "models": baseline["models"]}, f, indent=2)
    return bl


def main():
    ap = argparse.ArgumentParser(description="OpenRouter cost watch")
    ap.add_argument("cmd", nargs="?", default="check", choices=["check", "init"],
                    help="init = snapshot baseline; check = compare + auto-update")
    ap.add_argument("--config", required=True, help="path to config.json")
    args = ap.parse_args()

    # Enrich config with its own path so baseline_path can be relative to it.
    cfg = load_config(args.config)
    cfg["_cfg_path"] = args.config

    try:
        live = fetch_prices()
    except Exception as e:  # noqa: BLE001 -- report and exit, never fake state
        print(f"[openrouter-cost-watch] ERROR fetching catalog: {e}")
        sys.exit(1)

    baseline = load_baseline(cfg)
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    if args.cmd == "init":
        baseline = {"models": {}}
        for mid, cur in live.items():
            if mid in cfg.get("models", []):
                baseline["models"][mid] = cur
        save_baseline(cfg, baseline, now)
        print(f"Baseline captured for {len(baseline['models'])} models -> "
              f"{cfg.get('baseline_path', '<relative baseline.json>')}")
        return

    # ---- check mode ----
    in_pct = float(cfg.get("in_pct", 25))
    out_pct = float(cfg.get("out_pct", 25))
    min_abs = float(cfg.get("min_abs_usd", 0.02))
    track = cfg.get("models", [])

    changes = []
    lines = []
    for mid in track:
        cur = live.get(mid)
        if cur is None:
            changes.append((mid, "(disappeared from catalog)", None))
            continue
        old = baseline.get("models", {}).get(mid)
        for label, key in (("in", "in"), ("out", "out")):
            cur_v = cur[key]
            if not old:
                continue  # newly added to config but not in baseline yet
            old_v = old.get(key)
            if old_v == 0:
                continue
            pct = (cur_v - old_v) / old_v * 100.0
            if abs(cur_v - old_v) >= min_abs and abs(pct) >= (in_pct if label == "in" else out_pct):
                changes.append((mid, label, pct, old_v, cur_v))
                break

    if changes:
        lines.append("OPENROUTER PRICE CHANGES (vs last run)")
        lines.append("")
        for c in changes:
            if len(c) == 2:
                lines.append(f"  {c[0]}: {c[1]}")
            else:
                mid, label, pct, old_v, cur_v = c
                arrow = "UP" if pct > 0 else "DOWN"
                lines.append(f"  {arrow} {mid} ({label}): ${old_v:.4f} -> ${cur_v:.4f} ({pct:+.0f}%)")
        lines.append("")
        lines.append("Tracked models with no move are omitted.")
    else:
        lines.append("OPENROUTER PRICES: NO SIGNIFICANT CHANGES")
        lines.append("")
        for mid in track:
            old = baseline.get("models", {}).get(mid)
            if old:
                lines.append(f"  {mid}: in ${old['in']:.4f} / out ${old['out']:.4f}")
    lines.append("")
    lines.append(f"(checked {now}; baseline auto-updated)")

    # Refresh baseline with still-live tracked models.
    new_models = {}
    for mid in track:
        if mid in live:
            new_models[mid] = live[mid]
    baseline["models"] = new_models
    save_baseline(cfg, baseline, now)

    print("\n".join(lines))


if __name__ == "__main__":
    main()

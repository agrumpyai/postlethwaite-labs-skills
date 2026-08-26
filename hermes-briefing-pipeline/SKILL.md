---
name: daily-briefing-pipeline
description: Generate and deliver a branded daily briefing PDF fully via cron — scrape, summarize, build PDF, and email. Works with any AI agent (Claude Code, Codex, Hermes) out of the box.
version: 1.0.0
author: Postlethwaite Labs
license: MIT
domain: productivity
subdomain: automation
tags:
  - briefing
  - pdf
  - cron
  - automation
  - email
  - report
  - newsletter
---

# Daily Briefing Pipeline

Generate a branded daily briefing PDF from configurable sources, then deliver it via email — **fully automated with zero daily effort.**

```
Sources (RSS/API) → JSON config → Python → Branded PDF → Email inbox
                        ↑                            ↑
                     cron job (daily)             SMTP send
```

## What It Does

- Takes a JSON configuration with your sources (RSS feeds, API endpoints, text blocks)
- Generates a beautifully formatted PDF with branded header, section accents, and linked sources
- Delivers via SMTP email or saves to disk
- Runs entirely on cron — set it once, forget it

## Files Included

| File | Purpose |
|---|---|
| `build_briefing.py` | Python script that builds the PDF from JSON config |
| `example_config.json` | Working example with news, weather, and tech sections |
| `cron_setup.sh` | One-line cron installer (daily at 07:00 by default) |
| `README.md` | Full documentation |
| `example_config.json` | Working example showing the JSON input format |

## Quick Start

```bash
# 1. Edit the example config with your sources
cp example_config.json my_briefing.json
nano my_briefing.json

# 2. Generate your first PDF
python3 build_briefing.py my_briefing.json my_briefing.pdf

# 3. Set up daily cron delivery
bash cron_setup.sh
```

## Requirements

- Python 3.8+ with `fpdf2` (`pip install fpdf2`)
- SMTP credentials for email delivery (Gmail App Passwords work great)
- Linux/macOS with cron

## Customisation

Edit `build_briefing.py` to change:
- **Header colours** — banner background and accent colours
- **Fonts** — Helvetica or Courier
- **Layout** — section spacing, source formatting

The script passes all strings through latin-1 sanitisation to prevent emoji/unicode crashes in PDF generation (a common gotcha with fpdf2).

## Use Cases

- **Daily news briefing** — scrape RSS feeds every morning, get a PDF in your inbox
- **Competitor monitoring** — track competitor press mentions weekly
- **Security bulletin** — combine CISA KEV + cyber news into a daily threat brief
- **Internal team updates** — automated status reports for your team

## Privacy

Fully self-hosted. No telemetry, no accounts, no third-party services required (beyond your own SMTP server). Your data never leaves your machine.

## ☕ Support

If this skill helps you, consider [buying me a coffee](https://buymeacoffee.com/postlethwaitelabs).

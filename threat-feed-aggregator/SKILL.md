---
name: threat-feed-aggregator
description: Collect and dedupe cyber threat news from 5 trusted sources (The Hacker News, BleepingComputer, Dark Reading, The Register, threatline.io) into one clean briefing. No API keys, no accounts, no stealth.
version: 1.0.0
author: Postlethwaite Labs
license: MIT
domain: cybersecurity
subdomain: threat-intelligence
tags:
  - threat-intelligence
  - cyber-news
  - feed-aggregator
  - briefing
  - rss
  - monitoring
external_urls:
  - https://ip999--5ce29234a23711f192281607ee4eb77e.web.val.run/feed
  - https://feeds.feedburner.com/TheHackersNews
  - https://www.bleepingcomputer.com/feed
  - https://www.darkreading.com/rss.xml
  - https://www.theregister.com/security/headlines.atom
permissions:
  - network
---

# Threat Feed Aggregator

Collect + dedupe cyber threat news from the industry's most trusted sources
into one clean, timestamped briefing — ready for reports, newsletters, or
daily cyber brief PDFs.

## Sources (all public, zero API keys)

| Source | Method | Coverage |
|---|---|---|
| threatline.io | RSS (official feed) | Anchors links to all 4 major outlets below |
| The Hacker News | RSS | Broad infosec news, exploits, vulnerabilities |
| BleepingComputer | RSS | Tech-level security news, malware, ransomware |
| Dark Reading | RSS | Enterprise security, risk management, cyber strategy |
| The Register Security | Atom | IT + security, UK/global, slightly irreverent |

Multiple sources often link the same story — the dedupe engine merges them
by URL, keeping the most descriptive title.

## Files

| File | Purpose |
|---|---|
| `threat_aggregator.py` | The aggregator — fetch, parse, dedupe, output |
| `README.md` | Full documentation |

## Quick Start

```bash
# Run once with defaults
python3 threat_aggregator.py

# Full text brief
python3 threat_aggregator.py --format text --limit 8

# Machine-readable JSON (pipe into your own tools)
python3 threat_aggregator.py --format json --limit 5

# Skip short/blurry titles
python3 threat_aggregator.py --min-title-len 20
```

## Output Example

The deduped briefing includes 15-25 unique items from 5 sources, sorted
alphabetically by title. Each entry shows the story title + direct URL.

## Cron (daily cyber brief)

```bash
crontab -e
# add:
0 6 * * * cd /opt/feeds && python3 threat_aggregator.py --format text > /tmp/cyber_brief_$(date +%Y%m%d).txt
```

## Privacy

Fully client-side. Only outbound requests are to the five public feed URLs
and threatline.io. No telemetry, no accounts, no data storage on third
parties. The script runs entirely on your machine.

## Pitfalls

- The threatline feed is hosted on a val.run (Val Town) URL — if the host
  changes or disappears, that source returns zero items. Check `threatline`
  count in output headers.
- Feedburner URLs (The Hacker News) require following redirects — handled
  by urllib automatically.
- Multiple sources often link the same story (especially threatline, which
  aggregates the other 4 outlets) — duplicate-detection normalizes URLs
  (drops anchors and trailing slashes) and merges them.

## ☕ Support

If this skill helps you, consider [buying me a coffee](https://buymeacoffee.com/postlethwaite).

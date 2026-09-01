---
name: soc-security-ops
description: SOC-in-a-box for AI agents — monitor the CISA KEV catalog against your stack, aggregate cyber threat news from trusted public sources, and decide which software updates are actually worth installing. Three proven workflows, zero API keys, fully client-side.
version: 1.0.0
author: Postlethwaite Labs
license: MIT
domain: cybersecurity
subdomain: security-operations
tags:
  - cisa-kev
  - threat-intelligence
  - vulnerability-management
  - update-management
  - security-operations
  - soc
external_urls:
  - https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json
  - https://api.first.org/data/v1/epss
  - https://ip999--5ce29234a23711f192281607ee4eb77e.web.val.run/feed
  - https://feeds.feedburner.com/TheHackersNews
  - https://www.bleepingcomputer.com/feed
  - https://www.darkreading.com/rss.xml
  - https://www.theregister.com/security/headlines.atom
permissions:
  - network
metadata:
  openclaw:
    requires:
      bins:
        - python3
      config:
        - watchlist.json
    os:
      - linux
      - macos
---

# SOC Security Ops

A complete small-team security operations toolkit for AI agents. Three
proven workflows that cover the daily "is my stack on fire?" routine:

1. **KEV Monitor** — watch the CISA Known Exploited Vulnerabilities catalog
   against the vendors/products you actually run, enriched with EPSS
   exploit-probability scores and CISA remediation deadlines.
2. **Threat Feed Aggregator** — collect and dedupe cyber threat news from
   5 trusted public sources (The Hacker News, BleepingComputer, Dark Reading,
   The Register, threatline.io) into one clean briefing.
3. **Update Decision Framework** — a repeatable method for deciding whether
   a software update is worth installing, with a clear verdict
   (safe / worth it / urgent).

All three are client-side, use public data only, and require **zero API
keys** to get started.

## When to Use

- **Every morning:** run the KEV monitor to see if anything in your stack
  is now actively exploited (cron-friendly: `0 7 * * *`).
- **Daily briefing:** run the threat aggregator to get your cyber news in
  one deduped pass.
- **Whenever an update notification appears:** apply the update decision
  framework instead of guessing.

## Files

| File | Purpose |
|---|---|
| `kev_monitor.py` | CISA KEV watchlist monitor (Python 3 stdlib only) |
| `threat_aggregator.py` | 5-source threat news aggregator (Python 3 stdlib only) |
| `watchlist.example.json` | Example watchlist — copy to `watchlist.json` and edit |
| `README.md` | Setup, cron, and troubleshooting |

## Quickstart

Both scripts need only Python 3 (no pip installs — stdlib only).

### 1. KEV Monitor

```bash
# One-time setup: create your watchlist
cp watchlist.example.json watchlist.json
# edit watchlist.json with YOUR vendors/products (see format below)

# Run a check now (text report)
python3 kev_monitor.py --watchlist watchlist.json

# Machine-readable (for your own tooling)
python3 kev_monitor.py --watchlist watchlist.json --format json
```

Exit code `0` = nothing in your stack matched; `1` = matches found
(handy for cron). Schedule it daily:

```bash
0 7 * * * cd /path/to/soc-security-ops && python3 kev_monitor.py --watchlist watchlist.json --format text >> /tmp/kev_report.log 2>&1
```

### 2. Threat Feed Aggregator

```bash
# Full text brief (top stories)
python3 threat_aggregator.py --format text --limit 8

# JSON for piping into your own pipeline
python3 threat_aggregator.py --format json --limit 5
```

Schedule every morning alongside (or instead of) the KEV check:

```bash
0 6 * * * cd /path/to/soc-security-ops && python3 threat_aggregator.py --format text > /tmp/cyber_brief_$(date +%Y%m%d).txt
```

### 3. Update Decision Framework (agent-guided)

When the user asks "should I update X?", follow this process:

1. **Current version** — if unknown, check package managers (`pip show`,
   `npm list`, `apt policy`, `docker --version`) or ask.
2. **Latest version** — GitHub releases, official site, package registry,
   or RRS/changelog feed (via web search/browser).
3. **Release notes** between your version and latest, focusing on: security
   fixes/CVEs patched, breaking changes, relevant features, bug fixes.
4. **Verdict** with color coding:
   - 🟢 Safe patch release — no breaking changes → worth installing.
   - 🟡 Minor/major bump with new features → check compatibility first.
   - 🔴 Security patch addressing a CVE / active exploitation → urgent.
5. **Offer** to run the appropriate update command (`pip install -U`,
   `apt upgrade`, `npm update`, etc.) if the verdict is positive.

## Watchlist Format (KEV Monitor)

```json
{
  "vendors": ["microsoft", "adobe", "oracle", "cisco"],
  "products": ["exchange server", "acrobat reader", "webex"],
  "cves": ["CVE-2021-44228"]
}
```

- `vendors`: match any KEV entry whose vendor contains the string
- `products`: match any KEV entry whose product contains the string
- `cves`: explicit CVE IDs to always include

A KEV entry matches if ANY rule matches. Keep vendor/product strings
specific ("apple safari" not "apple") to avoid noise.

## Output Fields Explained (KEV Monitor)

| Field | Meaning |
|---|---|
| EPSS score | 0-1 probability of exploitation in next 30 days (FIRST.org) |
| Ransomware use | "Known" = CISA lists it in ransomware campaigns (act NOW) |
| Required action | CISA's recommended remediation |
| Due date | FCEB remediation deadline (good baseline for any org) |

## Pitfalls

- CISA updates the KEV catalog multiple times a week — run daily, not monthly.
- KEV absence does NOT mean safe — it's a minimum bar.
- The threatline feed is hosted on a val.run (Val Town) URL — if the host
  changes or disappears, that source returns zero items. Check the source
  count in the output header; the other 4 sources (RSS/Atom) are unaffected.
- The Hacker News uses Feedburner — redirects are handled by urllib, but it
  can be slow; give the aggregator a generous timeout.
- Update-check: some projects don't tag releases cleanly — check the commit
  log or package registry for the real latest version. Treat any major
  version bump as a yellow flag by default.

## Privacy

Fully client-side. The only outbound requests are to public APIs/feeds:
CISA KEV JSON, FIRST EPSS API, and the five public news sources. No
telemetry, no accounts, no data leaves your machine except those public
requests. The scripts never collect or transmit any system, network, or
personal information.

## ☕ Support

If this skill helps you, consider [buying me a coffee](https://buymeacoffee.com/postlethwaite).
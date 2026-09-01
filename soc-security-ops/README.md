# SOC Security Ops

A complete small-team security operations toolkit for AI agents, packaged as
a single skill. Three proven workflows, zero API keys, fully client-side.

## What's inside

| Tool | What it does | Runs on |
|---|---|---|
| `kev_monitor.py` | Watches the CISA KEV catalog against your stack, enriches with EPSS + ransomware flags + CISA due dates | Python 3 stdlib only |
| `threat_aggregator.py` | Dedupes cyber news from 5 public sources into one briefing | Python 3 stdlib only |
| Update Decision Framework | Agent-guided method for "should I install this update?" | Any agent with web access |

## Requirements

- Python 3.8+ (stdlib only — no pip installs)
- Network access to the public APIs/feeds listed in SKILL.md

## Setup

```bash
# 1. Create your KEV watchlist
cp watchlist.example.json watchlist.json
# edit watchlist.json with YOUR vendors/products

# 2. Test the KEV monitor
python3 kev_monitor.py --watchlist watchlist.json

# 3. Test the threat aggregator
python3 threat_aggregator.py --format text --limit 8
```

## Cron (recommended daily setup)

```bash
crontab -e
# add:
# 06:00 — cyber threat briefing
0 6 * * * cd /path/to/soc-security-ops && python3 threat_aggregator.py --format text > /tmp/cyber_brief_$(date +%Y%m%d).txt
# 07:00 — KEV stack check
0 7 * * * cd /path/to/soc-security-ops && python3 kev_monitor.py --watchlist watchlist.json --format text >> /tmp/kev_report.log 2>&1
```

## KEV monitor exit codes

- `0` — no matches for your stack (clean)
- `1` — matches found (investigate)

## Update Decision Framework

For any "should I update X?" question: check current version → find latest
(GitHub releases / official site / package registry) → read release notes
between the two (security fixes, breaking changes, features) → give a
color-coded verdict (🟢 safe / 🟡 check compatibility / 🔴 urgent) → offer
to install if positive.

## Privacy

No telemetry, no accounts, no personal data collected or transmitted. The
only outbound requests are to the public CISA KEV feed, FIRST EPSS API, and
five public news sources listed in SKILL.md.

## License

MIT
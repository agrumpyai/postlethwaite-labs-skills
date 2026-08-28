---
name: cisa-kev-monitor
description: Monitor the CISA Known Exploited Vulnerabilities (KEV) catalog against a custom watchlist of vendors/products and get instant alerts when something in your stack becomes actively exploited. Fetches the live CISA feed, filters by your watchlist, enriches with EPSS exploit-probability scores, and outputs a plain-English alert report with remediation deadlines.
version: 1.0.0
author: Postlethwaite Labs
license: MIT
domain: cybersecurity
subdomain: vulnerability-management
tags:
  - cisa-kev
  - cve
  - vulnerability-monitoring
  - epss
  - threat-intelligence
external_urls:
  - https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json
  - https://api.first.org/data/v1/epss
permissions:
  - network

# CISA KEV Vulnerability Monitor

A lightweight watchdog for the CISA Known Exploited Vulnerabilities (KEV)
catalog. It watches the official CISA feed, compares it against the
vendors/products you care about, enriches matches with EPSS scores
(probability of exploitation), and produces an alert report with
remediation deadlines.

Ships with a cron-friendly CLI — run it every morning and get a text or
JSON report of anything in your stack that is now under active attack.

## When to Use

- You want a daily/weekly automated check: "Is anything in my stack in the CISA KEV catalog?"
- You manage a small set of products/services and want exploitation alerts without a full vulnerability scanner.
- You want EPSS context for KEV entries (how likely is exploitation, not just "it's listed").

## Files

| File | Purpose |
|---|---|
| `kev_monitor.py` | The monitor — fetch, filter, enrich, report (Python 3 stdlib + `requests`) |
| `watchlist.example.json` | Example watchlist showing the JSON format |
| `README.md` | Setup + cron instructions |

## Quickstart

```bash
pip install requests

# 1. Create your watchlist
cp watchlist.example.json watchlist.json
# edit watchlist.json with YOUR vendors/products (see format below)

# 2. Run a check now
python3 kev_monitor.py --watchlist watchlist.json

# 3. Daily at 07:00 (cron)
0 7 * * * cd /path/to/monitor && python3 kev_monitor.py --watchlist watchlist.json --format text
```

## Watchlist Format

```json
{
  "vendors": ["microsoft", "adobe", "oracle", "cisco"],
  "products": ["exchange server", "acrobat reader", "webex"],
  "cves": ["CVE-2021-44228"]
}
```

- `vendors`: match any KEV entry whose vendor contains the string (case-insensitive)
- `products`: match any KEV entry whose product contains the string
- `cves`: explicit CVE IDs to always include

A KEV entry matches if ANY rule matches. An empty watchlist returns a
summary of the whole catalog (good for sanity checks).

## Output

- **Default**: pretty text report with: CVEs in your stack, EPSS score,
  whether it is known ransomware abuse, CISA required action, and the
  BOD 22-01 due date.
- `--format json`: machine-readable JSON (`--format text` is default).
- Exit code 0 = no matches, 1 = matches found (handy for cron scripting).
- `--send-to` email address: optional SMTP alert (uses env vars
  `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `EMAIL_FROM`).

## Report Fields Explained

| Field | Meaning |
|---|---|
| EPSS score | 0–1 probability of exploitation in the next 30 days (FIRST.org) |
| Ransomware use | "Known" = CISA lists it in ransomware campaigns (act NOW) |
| Required action | CISA's recommended remediation |
| Due date | FCEB remediation deadline; good baseline for any org |

## Pitfalls

- CISA updates the KEV catalog multiple times per week — run daily, not monthly.
- KEV is a *minimum* bar: absence from KEV does not mean safe.
- If a vendor string is too generic (e.g. "apple"), you'll get noise — be specific ("apple safari").

## Privacy

Fully client-side. The script only calls public APIs: CISA KEV JSON feed
and FIRST EPSS API. No telemetry, no accounts, no data leaves your machine
except the two public API requests.

## ☕ Support

If this skill helps you, consider [buying me a coffee](https://buymeacoffee.com/postlethwaite).
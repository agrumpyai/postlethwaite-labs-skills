# CISA KEV Vulnerability Monitor

Watch the CISA Known Exploited Vulnerabilities catalog against your own
stack. Daily alerts when one of your vendors/products becomes actively
exploited — with EPSS probability scores and remediation deadlines.

Built for Hermes Agent / any AI agent. Works everywhere Python 3 runs.

## Install

```bash
pip install requests   # actually: no deps beyond stdlib + urllib!
```

The script uses only the Python standard library (`urllib`, `json`,
`smtplib`). No `requests` needed.

## Setup

```bash
cp watchlist.example.json watchlist.json
nano watchlist.json   # put YOUR vendors/products/CVEs
```

## Run

```bash
python3 kev_monitor.py --watchlist watchlist.json
```

## Cron (daily alert)

```bash
crontab -e
# add:
0 7 * * * cd /opt/kev-monitor && python3 kev_monitor.py --watchlist watchlist.json --format text
```

Exit code is `1` when matches are found, `0` when clean — easy to chain
into your own notifier.

## Email alerts (optional)

```bash
export SMTP_HOST=smtp.gmail.com SMTP_PORT=587
export SMTP_USER=you@gmail.com SMTP_PASS=app-password EMAIL_FROM=you@gmail.com
python3 kev_monitor.py --watchlist watchlist.json --send-to you@yourdomain.com
```

## Privacy

Only two public API calls (CISA + FIRST), no accounts, no telemetry.
---
☕ If this skill saves you time, [buy me a coffee](https://buymeacoffee.com/postlethwaite)

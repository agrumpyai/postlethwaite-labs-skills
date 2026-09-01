# Threat Feed Aggregator

Collect + dedupe cyber threat news from 5 trusted sources for your daily briefings, reports, or newsletters.

## Sources

- The Hacker News (RSS)
- BleepingComputer (RSS)
- Dark Reading (RSS)
- The Register Security (Atom)
- threatline.io (RSS feed)

## Install

```bash
# No dependencies needed — Python 3 standard library only
python3 --version  # needs 3.8+
```

## Usage

```bash
# Default text output
python3 threat_aggregator.py

# JSON for piping into other tools
python3 threat_aggregator.py --format json

# Control item count per source
python3 threat_aggregator.py --limit 5
```

## Cron (daily brief)

```bash
0 6 * * * cd /opt/threat-feeds && python3 threat_aggregator.py --format text
```

## Output

~15–25 deduped items from 5 sources. Each item shows title + URL.
Dupes across sources are merged (keeps most descriptive title).

---

☕ If this skill saves you time, [buy me a coffee](https://buymeacoffee.com/postlethwaite)

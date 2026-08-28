# Automated Daily Briefing Pipeline for Hermes Agent

Generate, format, and deliver daily briefing PDFs — fully automated via cron.

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Sources   │───▶│ Hermes   │───▶│ PDF      │───▶│ Email    │
│ (RSS, API)│    │ Agent    │    │ (fpdf2)  │    │ (SMTP)   │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
                    │                                  │
                    └──── cron job ─────────────────────┘
```

## What You Get

| File | Purpose |
|---|---|
| `build_briefing.py` | Python script that takes a JSON config and outputs a branded PDF via fpdf2 |
| `example_config.json` | A working example with news, weather, and custom sections |
| `cron_setup.sh` | One‑liner to install the cron job and test it |
| `.env.example` | Template for your SMTP email credentials |
| `hermes_skill.md` | SKILL.md you can drop into your skills folder so Hermes can regenerate on demand |
| `LICENSE` | MIT — use it, modify it, sell it |

## Requirements

- **Hermes Agent** (any version)
- **Python 3.9+** with `fpdf2` and `pypdf` installed
- **An SMTP account** for email delivery (Gmail App Passwords work)
- **Linux / macOS** with cron or systemd timers

## Quick Start

```bash
# 1. Install dependencies
pip install fpdf2 pypdf

# 2. Edit the example config with your sources
cp example_config.json my_briefing.json
nano my_briefing.json

# 3. Run once to test
python3 build_briefing.py my_briefing.json my_first_briefing.pdf

# 4. Set up cron (daily at 07:00)
bash cron_setup.sh

# 5. (Optional) Add email delivery — see .env.example
```

## Customising the Template

### Adding your branding

Edit `build_briefing.py` and change:

- **Header colour** – line `self.set_fill_color(...)` for the banner
- **Fonts** – swap Helvetica for Courier for a different look
- **Footer text** – the `footer()` method

### Input JSON Format

```json
{
  "date": "26 August 2026",
  "title": "Your Custom Briefing Title",
  "sections": [
    ["Headline 1", "Body text here... Supports paragraphs separated by \\n."]
  ],
  "sources": [
    ["Name", "https://example.com"]
  ]
}
```

### Adding delivery via email

Hermes can email the PDF automatically:
```yaml
# In your cron job settings (inside Hermes):
deliver: "origin"          # deliver to the chat channel
# Or use the included email script:
python3 send_email.py recipient@example.com output.pdf
```

## Testing

```bash
# Quick sanity check
python3 -c "
from pypdf import PdfReader
r = PdfReader('test.pdf')
print(f'{len(r.pages)} pages, {sum(1 for p in r.pages for a in (p.get(\"/Annots\") or []))} links')
"
```

## Support

Open an issue on GitHub or ask in the [Hermes Agent Discord](https://discord.gg/nousresearch).

---

☕ If this skill saves you time, [buy me a coffee](https://buymeacoffee.com/postlethwaite)

Built for Hermes Agent by Postlethwaite Labs.

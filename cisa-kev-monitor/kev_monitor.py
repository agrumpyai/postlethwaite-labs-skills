#!/usr/bin/env python3
"""
CISA KEV Vulnerability Monitor

Fetches the CISA Known Exploited Vulnerabilities catalog, filters it
against a local watchlist (vendors/products/CVEs), enriches matches with
EPSS scores, and prints a plain-English alert report.

Usage:
    python3 kev_monitor.py --watchlist watchlist.json [--format text|json] [--send-to email]

Public APIs used (no keys required):
    - CISA KEV: https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json
    - FIRST EPSS: https://api.first.org/data/v1/epss?cve=...
"""

import argparse
import json
import os
import smtplib
import sys
from email.mime.text import MIMEText
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
EPSS_API = "https://api.first.org/data/v1/epss"

USER_AGENT = "cisa-kev-monitor/1.0 (vulnerability watchlist monitor)"


def http_get_json(url, params=None):
    """Fetch JSON from a URL with a browser-ish user agent."""
    full = url
    if params:
        qs = "&".join(f"{k}={v}" for k, v in params.items())
        full = url + ("&" if "?" in url else "?") + qs
    req = Request(full, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        print(f"[!] HTTP {e.code} for {full}", file=sys.stderr)
        raise
    except URLError as e:
        print(f"[!] Network error: {e.reason}", file=sys.stderr)
        raise


def load_watchlist(path):
    """Load watchlist JSON: {vendors: [], products: [], cves: []}."""
    if not os.path.exists(path):
        print(f"[!] Watchlist not found: {path}", file=sys.stderr)
        return {"vendors": [], "products": [], "cves": []}
    with open(path) as f:
        data = json.load(f)
    return {
        "vendors": [v.lower() for v in data.get("vendors", [])],
        "products": [p.lower() for p in data.get("products", [])],
        "cves": [c.upper() for c in data.get("cves", [])],
    }


def entry_matches(entry, wl):
    """True if a KEV entry matches any watchlist rule."""
    if not (wl["vendors"] or wl["products"] or wl["cves"]):
        return True  # empty watchlist -> match everything (summary mode)
    cve = entry.get("cveID", "").upper()
    vendor = entry.get("vendorProject", "").lower()
    product = entry.get("product", "").lower()
    if cve in wl["cves"]:
        return True
    for v in wl["vendors"]:
        if v in vendor:
            return True
    for p in wl["products"]:
        if p in product:
            return True
    return False


def fetch_kev():
    """Return (catalog_meta, entries list) from CISA."""
    data = http_get_json(KEV_URL)
    meta = {
        "catalog_version": data.get("catalogVersion", "N/A"),
        "released": data.get("dateReleased", "N/A"),
    }
    return meta, data.get("vulnerabilities", [])


def fetch_epss(cve_ids):
    """Fetch EPSS scores for a list of CVEs, in batches of 100."""
    scores = {}
    ids = list(cve_ids)
    for i in range(0, len(ids), 100):
        batch = ids[i : i + 100]
        try:
            data = http_get_json(EPSS_API, params={"cve": ",".join(batch)})
            for entry in data.get("data", []):
                scores[entry["cve"]] = {
                    "epss": float(entry.get("epss", 0.0)),
                    "percentile": float(entry.get("percentile", 0.0)),
                }
        except Exception:
            continue  # EPSS is enrichment; never fail the run on it
    return scores


def build_report(entries, epss):
    """Return list of match dicts sorted by EPSS desc."""
    matches = []
    for e in entries:
        cve = e.get("cveID", "")
        s = epss.get(cve, {"epss": 0.0, "percentile": 0.0})
        matches.append(
            {
                "cve": cve,
                "vendor": e.get("vendorProject", ""),
                "product": e.get("product", ""),
                "name": e.get("vulnerabilityName", ""),
                "epss": round(s["epss"], 4),
                "epss_percentile": round(s["percentile"], 4),
                "ransomware": e.get("knownRansomwareCampaignUse", "Unknown"),
                "required_action": e.get("requiredAction", ""),
                "due_date": e.get("dueDate", ""),
                "date_added": e.get("dateAdded", ""),
            }
        )
    matches.sort(key=lambda m: (-m["epss"], m["cve"]))
    return matches


def format_text(meta, matches):
    lines = []
    lines.append("=" * 68)
    lines.append("CISA KEV VULNERABILITY MONITOR — ALERT REPORT")
    lines.append("=" * 68)
    lines.append(f"Catalog version : {meta['catalog_version']}")
    lines.append(f"CISA released   : {meta['released']}")
    lines.append("-" * 68)
    if not matches:
        lines.append("No watchlist items found in the KEV catalog. Good news.")
    for m in matches:
        lines.append("")
        lines.append(f"  {m['cve']}  [{m['vendor']} / {m['product']}]")
        lines.append(f"    {m['name']}")
        lines.append(f"    EPSS: {m['epss']:.4f} (p{int(m['epss_percentile']*100)}th pct)  "
                     f"Ransomware: {m['ransomware']}")
        if m["required_action"]:
            lines.append(f"    Action required: {m['required_action']}")
        if m["due_date"]:
            lines.append(f"    Remediation due: {m['due_date']}")
    lines.append("")
    lines.append("=" * 68)
    lines.append(f"{len(matches)} matching KEV entr{'y' if len(matches)==1 else 'ies'}. "
                 "KEV absence does NOT mean safe.")
    return "\n".join(lines)


def send_email(to, subject, body):
    """Optional SMTP alert. Reads creds from env."""
    host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER", "")
    pwd = os.getenv("SMTP_PASS", "")
    frm = os.getenv("EMAIL_FROM", user)
    if not user or not pwd:
        print("[!] SMTP_USER/SMTP_PASS not set — skipping email.", file=sys.stderr)
        return False
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = frm
    msg["To"] = to
    try:
        with smtplib.SMTP(host, port, timeout=30) as s:
            s.starttls()
            s.login(user, pwd)
            s.send_message(msg)
        print(f"[+] Email alert sent to {to}")
        return True
    except Exception as e:
        print(f"[!] Email failed: {e}", file=sys.stderr)
        return False


def main():
    ap = argparse.ArgumentParser(description="CISA KEV vulnerability monitor")
    ap.add_argument("--watchlist", default="watchlist.json",
                    help="path to watchlist JSON (default: watchlist.json)")
    ap.add_argument("--format", choices=["text", "json"], default="text")
    ap.add_argument("--send-to", default="",
                    help="email address to alert on matches")
    args = ap.parse_args()

    wl = load_watchlist(args.watchlist)
    print(f"[*] Watchlist: {len(wl['vendors'])} vendors, "
          f"{len(wl['products'])} products, {len(wl['cves'])} CVEs", file=sys.stderr)

    meta, entries = fetch_kev()
    print(f"[*] KEV catalog: {len(entries)} entries "
          f"(v{meta['catalog_version']}, {meta['released']})", file=sys.stderr)

    matched = [e for e in entries if entry_matches(e, wl)]
    print(f"[*] {len(matched)} entries match your watchlist", file=sys.stderr)

    epss = fetch_epss([e["cveID"] for e in matched])
    report = build_report(matched, epss)

    if args.format == "json":
        print(json.dumps({"meta": meta, "matches": report}, indent=2))
    else:
        print(format_text(meta, report))

    # Exit code: 0 = clean, 1 = matches (for cron scripting)
    if report and args.send_to:
        send_email(args.send_to, f"KEV alert: {len(report)} item(s) in your stack",
                   format_text(meta, report))
    sys.exit(1 if report else 0)


if __name__ == "__main__":
    main()
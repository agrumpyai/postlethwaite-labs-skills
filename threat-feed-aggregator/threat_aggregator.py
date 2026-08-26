#!/usr/bin/env python3
"""
Threat Feed Aggregator — collect + dedupe cyber threat items from trusted
feeds into one clean list for briefings, reports, or newsletters.

Sources (all public, no API keys):
  - threatline.io (scrape, JS site, regex extraction)
  - The Hacker News (RSS via Feedburner)
  - BleepingComputer (RSS)
  - Dark Reading (RSS)
  - The Register Security (RSS)

Usage:
    python3 threat_aggregator.py [--format text|json] [--limit N] [--min-title-len N]

Output: deduped list of (title, url) sorted newest-first per feed.
"""

import argparse
import html
import json
import re
import sys
import xml.etree.ElementTree as ET
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

USER_AGENT = "threat-feed-aggregator/1.0 (cyber briefing monitor)"

THREATLINE_URL = "https://threatline.io/"
FEEDS = {
    "the_hacker_news": "https://feeds.feedburner.com/TheHackersNews",
    "bleepingcomputer": "https://www.bleepingcomputer.com/feed/",
    "dark_reading": "https://www.darkreading.com/rss.xml",
    "theregister": "https://www.theregister.com/security/headlines.atom",
}

# Allowed domains for the threatline scrape (anchors on these)
THREATLINE_DOMAINS = (
    "https://thehackernews.com",
    "https://www.bleepingcomputer.com",
    "https://www.darkreading.com",
    "https://www.theregister.com",
)


def http_get(url, headers=None):
    """GET a URL and return raw bytes."""
    req = Request(url, headers={"User-Agent": USER_AGENT, **(headers or {})})
    try:
        with urlopen(req, timeout=30) as resp:
            return resp.read()
    except HTTPError as e:
        print(f"[!] HTTP {e.code} for {url}", file=sys.stderr)
        return b""
    except URLError as e:
        print(f"[!] Network error for {url}: {e.reason}", file=sys.stderr)
        return b""


def threatline_items(html_text):
    """threatline.io homepage -> [(title, url)].
    threatline.io is a JS-rendered site with NO RSS; regex is the only way.
    It anchors links to the 4 major security outlets."""
    items = re.findall(
        r'<a[^>]+href="('
        r'https://(?:thehackernews|www\.bleepingcomputer|'
        r'www\.darkreading|www\.theregister)\.com[^"]+)'
        r'"[^>]*>([^<]{10,200})</a>',
        html_text,
    )
    seen, out = set(), []
    for url, title in items:
        title = html.unescape(title).strip()
        if url not in seen and len(title) > 15:
            seen.add(url)
            out.append((title, url))
    return out  # typically ~10 items


def rss_items(xml_bytes, limit=6):
    """Parse an RSS/Atom feed -> [(title, desc, url)]."""
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as e:
        print(f"[!] XML parse error: {e}", file=sys.stderr)
        return []

    out = []
    # Try RSS (<item>) first, then Atom (<entry>)
    items = root.findall(".//item") or root.findall(".//entry")
    for it in items[:limit]:
        title = it.findtext("title")
        link = it.findtext("link")
        # Atom <link href="...">
        if not link:
            link_el = it.find("link")
            if link_el is not None:
                link = link_el.get("href")
        desc = it.findtext("description") or it.findtext("summary") or ""
        desc = re.sub(r"<[^>]+>", "", html.unescape(desc)).strip()[:250]
        if title:
            out.append((html.unescape(title).strip(), desc, link))
    return out


def fetch_all(limit_per_feed):
    """Fetch all sources, returning dict {source: [(title, url)]}."""
    results = {}

    # threatline scrape
    raw = http_get(THREATLINE_URL)
    if raw:
        items = threatline_items(raw.decode("utf-8", "replace"))
        results["threatline"] = [(t, u) for t, u in items[:limit_per_feed * 3]]
        print(f"[*] threatline.io: {len(items)} items", file=sys.stderr)

    # RSS feeds
    for name, url in FEEDS.items():
        raw = http_get(url)
        if raw:
            items = rss_items(raw, limit=limit_per_feed)
            results[name] = [(t, u) for t, _, u in items]
            print(f"[*] {name}: {len(items)} items", file=sys.stderr)

    return results


def dedupe(results):
    """Merge all sources, dedupe by URL, prefer most descriptive title."""
    by_url = {}
    for source, items in results.items():
        for title, url in items:
            if not url:
                continue
            norm = url.split("#")[0].rstrip("/")  # strip anchors/trailing slash
            existing = by_url.get(norm)
            if existing is None:
                by_url[norm] = (title, url)
            elif len(title) > len(existing[0]):
                by_url[norm] = (title, url)

    out = [{"title": t, "url": u} for t, u in by_url.values()]
    out.sort(key=lambda x: x["title"].lower())
    return out


def format_text(items, source_counts):
    lines = []
    lines.append("=" * 68)
    lines.append("THREAT FEED AGGREGATOR — CYBER BRIEF")
    lines.append("=" * 68)
    for source, count in source_counts.items():
        lines.append(f"  {source}: {count} items")
    lines.append("-" * 68)
    if not items:
        lines.append("No items collected. Check network/source availability.")
    for i, item in enumerate(items, 1):
        lines.append(f"{i:>2}. {item['title']}")
        lines.append(f"     {item['url']}")
    lines.append("")
    lines.append(f"Total: {len(items)} deduped items across {len(source_counts)} sources")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Threat feed aggregator")
    ap.add_argument("--format", choices=["text", "json"], default="text")
    ap.add_argument("--limit", type=int, default=6,
                    help="max items per source (default 6)")
    ap.add_argument("--min-title-len", type=int, default=15,
                    help="skip titles shorter than this (default 15)")
    args = ap.parse_args()

    # Patch threatline_items to respect min-title-len
    global threatline_items
    if args.min_title_len != 15:
        def threatline_items(html_text, _orig=threatline_items, _min=args.min_title_len):
            out = []
            for t, u in _orig(html_text):
                if len(t) >= _min:
                    out.append((t, u))
            return out

    results = fetch_all(args.limit)
    items = dedupe(results)
    source_counts = {k: len(v) for k, v in results.items()}

    if args.format == "json":
        print(json.dumps({
            "source_counts": source_counts,
            "items": items,
            "total": len(items),
        }, indent=2))
    else:
        print(format_text(items, source_counts))

    sys.exit(0 if items else 1)


if __name__ == "__main__":
    main()
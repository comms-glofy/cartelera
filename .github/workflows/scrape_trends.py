#!/usr/bin/env python3
"""
Scraper del RSS oficial de Google Trends Argentina
https://trends.google.com/trending/rss?geo=AR
Genera trends.json — se ejecuta via GitHub Actions cada 30 minutos.
"""

import json
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

import requests

RSS_URL = "https://trends.google.com/trending/rss?geo=AR"
NS = {"ht": "https://trends.google.com/trending/rss"}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
    "Accept-Language": "es-AR,es;q=0.9",
}

def scrape():
    try:
        r = requests.get(RSS_URL, headers=HEADERS, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print(f"ERROR al obtener Google Trends RSS: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        root = ET.fromstring(r.content)
    except ET.ParseError as e:
        print(f"ERROR al parsear XML: {e}", file=sys.stderr)
        sys.exit(1)

    trends = []
    for item in root.findall(".//item"):
        title_el = item.find("title")
        if title_el is None or not title_el.text:
            continue

        title = title_el.text.strip()

        traffic_el = item.find("ht:approx_traffic", NS)
        traffic = traffic_el.text.strip() if traffic_el is not None else ""

        pic_el = item.find("ht:picture", NS)
        pic_url = pic_el.text.strip() if pic_el is not None and pic_el.text else ""

        pic_src_el = item.find("ht:picture_source", NS)
        pic_src = pic_src_el.text.strip() if pic_src_el is not None and pic_src_el.text else ""

        # First news item title as context
        news_title_el = item.find("ht:news_item/ht:news_item_title", NS)
        news_title = news_title_el.text.strip() if news_title_el is not None and news_title_el.text else ""

        trends.append({
            "name": title,
            "traffic": traffic,
            "picture": pic_url,
            "picture_source": pic_src,
            "news_title": news_title,
        })

        if len(trends) >= 10:
            break

    if not trends:
        print("ERROR: no se encontraron tendencias en el RSS", file=sys.stderr)
        sys.exit(1)

    output = {
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "Google Trends Argentina",
        "geo": "AR",
        "trends": trends,
    }

    with open("trends.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"OK — {len(trends)} tendencias de Google Trends AR")
    for t in trends:
        print(f"  {t['traffic']:>6}  {t['name']}")

if __name__ == "__main__":
    scrape()

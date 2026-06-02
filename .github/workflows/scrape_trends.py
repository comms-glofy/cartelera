#!/usr/bin/env python3
"""
Scraper Google Trends Argentina — RSS oficial
Sin pytrends, sin dependencias externas más que requests.
"""

import json, sys, time, random
from datetime import datetime, timezone
import xml.etree.ElementTree as ET
import requests

RSS_URL = "https://trends.google.com/trending/rss?geo=AR"
NS = {"ht": "https://trends.google.com/trending/rss"}

# User agents reales de navegadores
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]

def fetch_rss(attempt=0):
    ua = USER_AGENTS[attempt % len(USER_AGENTS)]
    session = requests.Session()
    
    # Primero hacer una visita a la página principal para obtener cookies
    try:
        session.get(
            "https://trends.google.com/trending?geo=AR&hl=es",
            headers={
                "User-Agent": ua,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "es-AR,es;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
            },
            timeout=15
        )
        time.sleep(random.uniform(1.5, 3.0))
    except Exception:
        pass  # Si falla la visita inicial, igual intentamos el RSS

    # Ahora pedir el RSS con las cookies obtenidas
    resp = session.get(
        RSS_URL,
        headers={
            "User-Agent": ua,
            "Accept": "application/rss+xml, application/xml, text/xml, */*",
            "Accept-Language": "es-AR,es;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://trends.google.com/trending?geo=AR",
            "Cache-Control": "no-cache",
        },
        timeout=20
    )
    resp.raise_for_status()
    return resp.content

def parse_rss(content):
    root = ET.fromstring(content)
    trends = []
    for item in root.findall(".//item"):
        title_el = item.find("title")
        if title_el is None or not title_el.text:
            continue
        traffic_el = item.find("ht:approx_traffic", NS)
        traffic = traffic_el.text.strip() if traffic_el is not None else ""
        trends.append({
            "name": title_el.text.strip(),
            "traffic": traffic,
            "rank": len(trends) + 1,
        })
        if len(trends) >= 10:
            break
    return trends

def main():
    trends = None
    
    for attempt in range(4):
        try:
            print(f"→ Intento {attempt + 1}...", file=sys.stderr)
            content = fetch_rss(attempt)
            trends = parse_rss(content)
            if trends:
                print(f"✓ OK: {len(trends)} tendencias", file=sys.stderr)
                break
            else:
                print(f"✗ RSS vacío", file=sys.stderr)
        except Exception as e:
            print(f"✗ Error: {e}", file=sys.stderr)
        
        if attempt < 3:
            wait = (attempt + 1) * random.uniform(4, 8)
            print(f"  Esperando {wait:.1f}s...", file=sys.stderr)
            time.sleep(wait)

    if not trends:
        print("ERROR FATAL: no se pudieron obtener tendencias", file=sys.stderr)
        sys.exit(1)

    for t in trends:
        print(f"  {t['rank']:2}. {t['name']} [{t['traffic']}]", file=sys.stderr)

    output = {
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "Google Trends Argentina",
        "geo": "AR",
        "trends": trends,
    }

    with open("trends.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"OK — trends.json actualizado")

if __name__ == "__main__":
    main()

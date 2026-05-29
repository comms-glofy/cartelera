#!/usr/bin/env python3
"""
Scraper de Google Trends Argentina via pytrends
Genera trends.json — ejecutado por GitHub Actions cada 30 minutos.

pytrends usa la API no-oficial de Google Trends con sesión/cookies,
diseñada específicamente para funcionar desde servidores.
"""

import json
import sys
import time
from datetime import datetime, timezone


def scrape_via_pytrends():
    """Método principal: pytrends (trending_searches)"""
    from pytrends.request import TrendReq

    # Reintentos con backoff por si Google devuelve 429
    for attempt in range(3):
        try:
            pytrends = TrendReq(
                hl="es-AR",
                tz=-180,        # UTC-3 Argentina
                timeout=(10, 25),
                retries=2,
                backoff_factor=0.5,
            )
            df = pytrends.trending_searches(pn="argentina")
            terms = df[0].dropna().tolist()
            if not terms:
                raise ValueError("Lista vacía")

            trends = []
            for i, term in enumerate(terms[:10]):
                trends.append({
                    "name": str(term).strip(),
                    "traffic": "",
                    "rank": i + 1,
                })
            return trends

        except Exception as e:
            print(f"Intento {attempt+1} fallido: {e}", file=sys.stderr)
            if attempt < 2:
                time.sleep(5 * (attempt + 1))

    return None


def scrape_via_rss():
    """Fallback: RSS oficial de Google Trends"""
    import urllib.request
    import xml.etree.ElementTree as ET

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
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }

    req = urllib.request.Request(RSS_URL, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        content = resp.read()

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

    return trends if trends else None



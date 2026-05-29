#!/usr/bin/env python3
"""
Scraper de Google Trends Argentina
Usa pytrends con múltiples métodos y validación estricta.
"""

import json, sys, time
from datetime import datetime, timezone


def method_trending_searches():
    """trending_searches() — top búsquedas del día en Argentina"""
    from pytrends.request import TrendReq
    pt = TrendReq(hl="es-AR", tz=-180, timeout=(10, 25), retries=2, backoff_factor=0.5)
    df = pt.trending_searches(pn="argentina")
    terms = [str(t).strip() for t in df[0].tolist() if str(t).strip()]
    if not terms:
        raise ValueError("trending_searches devolvió lista vacía")
    return [{"name": t, "traffic": "", "rank": i+1} for i, t in enumerate(terms[:10])]


def method_realtime_trending():
    """realtime_trending_searches() — tendencias en tiempo real"""
    from pytrends.request import TrendReq
    pt = TrendReq(hl="es-AR", tz=-180, timeout=(10, 25), retries=2, backoff_factor=0.5)
    df = pt.realtime_trending_searches(pn="AR")
    results = []
    for _, row in df.iterrows():
        title = str(row.get("title", "")).strip()
        if title and len(title) > 1:
            results.append({"name": title, "traffic": "", "rank": len(results)+1})
        if len(results) >= 10:
            break
    if not results:
        raise ValueError("realtime_trending_searches devolvió lista vacía")
    return results


def method_rss_direct():
    """RSS oficial de Google Trends — último recurso"""
    import urllib.request, xml.etree.ElementTree as ET
    NS = {"ht": "https://trends.google.com/trending/rss"}
    url = "https://trends.google.com/trending/rss?geo=AR"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
        "Accept-Language": "es-AR,es;q=0.9",
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        root = ET.fromstring(resp.read())
    results = []
    for item in root.findall(".//item"):
        title_el = item.find("title")
        if title_el is None or not title_el.text:
            continue
        traffic_el = item.find("ht:approx_traffic", NS)
        traffic = traffic_el.text.strip() if traffic_el is not None else ""
        results.append({"name": title_el.text.strip(), "traffic": traffic, "rank": len(results)+1})
        if len(results) >= 10:
            break
    if not results:
        raise ValueError("RSS devolvió lista vacía")
    return results


def main():
    methods = [
        ("trending_searches",    method_trending_searches),
        ("realtime_trending",    method_realtime_trending),
        ("rss_directo",          method_rss_direct),
    ]

    trends = None
    for name, fn in methods:
        print(f"→ Intentando {name}...", file=sys.stderr)
        try:
            trends = fn()
            print(f"✓ {name} OK: {len(trends)} tendencias", file=sys.stderr)
            break
        except Exception as e:
            print(f"✗ {name} falló: {e}", file=sys.stderr)
            time.sleep(3)

    if not trends:
        print("ERROR FATAL: todos los métodos fallaron", file=sys.stderr)
        sys.exit(1)

    # Imprimir resultado
    print(f"\nTendencias obtenidas:", file=sys.stderr)
    for t in trends:
        vol = f"  [{t['traffic']}]" if t.get("traffic") else ""
        print(f"  {t['rank']:2}. {t['name']}{vol}", file=sys.stderr)

    output = {
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "Google Trends Argentina",
        "geo": "AR",
        "trends": trends,
    }

    with open("trends.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nOK — trends.json actualizado con {len(trends)} tendencias")


if __name__ == "__main__":
    main()


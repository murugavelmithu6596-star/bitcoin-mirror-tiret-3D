#!/usr/bin/env python3
"""Fetch Swiss federal legislation metadata from Fedlex SPARQL (since 2000)."""
from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

ENDPOINT = "https://fedlex.data.admin.ch/sparqlendpoint"
OUT = Path(__file__).resolve().parents[1] / "data"
YEAR_START = 2000
YEAR_END = 2027
HTML_TAG = re.compile(r"<[^>]+>")


def sparql(query: str, retries: int = 4) -> dict:
    data = urllib.parse.urlencode({"query": query}).encode()
    req = urllib.request.Request(
        ENDPOINT,
        data=data,
        headers={
            "Accept": "application/sparql-results+json",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "lois-suisses-loader/1.0 (Cursor agent; educational reuse)",
        },
        method="POST",
    )
    last_err = None
    for i in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            last_err = e
            time.sleep(2 ** i)
    raise RuntimeError(f"SPARQL failed after retries: {last_err}")


def clean_title(t: str | None) -> str:
    if not t:
        return ""
    return HTML_TAG.sub("", t).replace("&nbsp;", " ").strip()


def year_query_oc(year: int) -> str:
    return f"""
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT ?uri ?dateDocument ?titleFr ?titleDe WHERE {{
  ?uri a jolux:Act ;
       jolux:dateDocument ?dateDocument .
  FILTER(STRSTARTS(STR(?uri), "https://fedlex.data.admin.ch/eli/oc/"))
  FILTER(?dateDocument >= "{year}-01-01"^^xsd:date && ?dateDocument <= "{year}-12-31"^^xsd:date)
  OPTIONAL {{
    ?uri jolux:isRealizedBy ?exprFr .
    ?exprFr jolux:language <http://publications.europa.eu/resource/authority/language/FRA> ;
            jolux:title ?titleFr .
  }}
  OPTIONAL {{
    ?uri jolux:isRealizedBy ?exprDe .
    ?exprDe jolux:language <http://publications.europa.eu/resource/authority/language/DEU> ;
            jolux:title ?titleDe .
  }}
}}
"""


def year_query_rs(year: int) -> str:
    return f"""
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT ?uri ?rsNr ?dateEntryInForce ?dateDocument ?titleFr ?titleDe WHERE {{
  ?uri a jolux:ConsolidationAbstract .
  OPTIONAL {{ ?uri jolux:classifiedByTaxonomyEntry / skos:notation ?rsNr . }}
  OPTIONAL {{ ?uri jolux:dateEntryInForce ?dateEntryInForce . }}
  OPTIONAL {{ ?uri jolux:dateDocument ?dateDocument . }}
  FILTER(
    (BOUND(?dateEntryInForce) && ?dateEntryInForce >= "{year}-01-01"^^xsd:date && ?dateEntryInForce <= "{year}-12-31"^^xsd:date)
    ||
    (!BOUND(?dateEntryInForce) && BOUND(?dateDocument) && ?dateDocument >= "{year}-01-01"^^xsd:date && ?dateDocument <= "{year}-12-31"^^xsd:date)
  )
  OPTIONAL {{
    ?uri jolux:isRealizedBy ?exprFr .
    ?exprFr jolux:language <http://publications.europa.eu/resource/authority/language/FRA> ;
            jolux:title ?titleFr .
  }}
  OPTIONAL {{
    ?uri jolux:isRealizedBy ?exprDe .
    ?exprDe jolux:language <http://publications.europa.eu/resource/authority/language/DEU> ;
            jolux:title ?titleDe .
  }}
}}
"""


def bind(b: dict, key: str) -> str | None:
    v = b.get(key)
    return v["value"] if v else None


def fetch_oc() -> list[dict]:
    by_uri: dict[str, dict] = {}
    for year in range(YEAR_START, YEAR_END + 1):
        print(f"OC {year}...", flush=True)
        res = sparql(year_query_oc(year))
        rows = res.get("results", {}).get("bindings", [])
        print(f"  {len(rows)} rows", flush=True)
        for b in rows:
            uri = bind(b, "uri")
            if not uri:
                continue
            title = clean_title(bind(b, "titleFr")) or clean_title(bind(b, "titleDe")) or uri.rsplit("/", 1)[-1]
            date = bind(b, "dateDocument") or ""
            y = int(date[:4]) if date[:4].isdigit() else year
            # fedlex human page
            fedlex = uri.replace("https://fedlex.data.admin.ch/", "https://www.fedlex.admin.ch/")
            by_uri[uri] = {
                "id": uri,
                "source": "federal_oc",
                "collection": "RO/AS (Recueil officiel)",
                "title": title,
                "year": y,
                "date": date,
                "rs": None,
                "url": fedlex,
            }
        time.sleep(0.3)
    return sorted(by_uri.values(), key=lambda x: (x["year"], x["title"]), reverse=True)


def fetch_rs() -> list[dict]:
    by_uri: dict[str, dict] = {}
    for year in range(YEAR_START, YEAR_END + 1):
        print(f"RS {year}...", flush=True)
        res = sparql(year_query_rs(year))
        rows = res.get("results", {}).get("bindings", [])
        print(f"  {len(rows)} rows", flush=True)
        for b in rows:
            uri = bind(b, "uri")
            if not uri:
                continue
            title = clean_title(bind(b, "titleFr")) or clean_title(bind(b, "titleDe")) or uri.rsplit("/", 1)[-1]
            date = bind(b, "dateEntryInForce") or bind(b, "dateDocument") or ""
            y = int(date[:4]) if date[:4].isdigit() else year
            fedlex = uri.replace("https://fedlex.data.admin.ch/", "https://www.fedlex.admin.ch/")
            by_uri[uri] = {
                "id": uri,
                "source": "federal_rs",
                "collection": "RS (Recueil systématique)",
                "title": title,
                "year": y,
                "date": date,
                "rs": bind(b, "rsNr"),
                "url": fedlex,
            }
        time.sleep(0.3)
    return sorted(by_uri.values(), key=lambda x: (x["year"], x["title"]), reverse=True)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    oc = fetch_oc()
    rs = fetch_rs()
    # Prefer RS entries in the browse list (consolidated laws), plus OC for enacted texts
    # Dedupe by title+year loosely for display index; keep both collections
    all_laws = oc + rs
    meta = {
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": "Fedlex SPARQL https://fedlex.data.admin.ch/sparqlendpoint",
        "scope": "Swiss federal legislation (RO/AS + RS) with document/entry date >= 2000",
        "limits": [
            "Fedlex covers federal law only; cantonal legislation is published on separate cantonal portals and is not included.",
            "Full-text bodies are not downloaded; metadata + Fedlex links only.",
            "Titles prefer French, fall back to German.",
        ],
        "counts": {
            "officialCompilationSince2000": len(oc),
            "classifiedCompilationSince2000": len(rs),
            "totalEntries": len(all_laws),
            "yearMin": min((x["year"] for x in all_laws), default=None),
            "yearMax": max((x["year"] for x in all_laws), default=None),
        },
    }
    (OUT / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "oc_since_2000.json").write_text(json.dumps(oc, ensure_ascii=False), encoding="utf-8")
    (OUT / "rs_since_2000.json").write_text(json.dumps(rs, ensure_ascii=False), encoding="utf-8")
    (OUT / "laws.json").write_text(json.dumps(all_laws, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(meta["counts"], indent=2))
    print("Wrote", OUT)


if __name__ == "__main__":
    main()

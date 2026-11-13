# Lois suisses (iPhone PWA)

Progressive Web App to browse Swiss **federal** legislation since 2000, sourced from [Fedlex](https://www.fedlex.admin.ch/) (Official Compilation RO/AS + Classified Compilation RS).

## Open on iPhone

1. Serve this folder (or open the published Cursor app URL).
2. In **Safari**: Share → **Add to Home Screen**.
3. Scroll the list, filter RO/AS vs RS, or search by title / RS number / year.
4. Tap a row to open the official Fedlex page.

## Run locally

```bash
cd lois-suisses
python3 -m http.server 4173 --bind 127.0.0.1
```

Open http://127.0.0.1:4173

## Data

- `data/years/*.json` — metadata by year (title, year, date, RS, Fedlex URL)
- `data/index.json` — counts and year index
- `data/laws.json` — full combined dump
- Refresh with: `python3 scripts/fetch_fedlex.py`

## Limits

- Federal law only (Fedlex). Cantonal statutes are not included.
- Metadata + links; full text stays on Fedlex.
- Not an official publication.

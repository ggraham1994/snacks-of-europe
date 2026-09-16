# Snacks of Europe

Static storefront preview with two stores built from one source file.

| Path | What it is |
| --- | --- |
| `src/site.html` | The only file to edit. One page holding both stores' copy, prices and box line-ups. |
| `index.html` | Landing page. Sends each visitor to the UK or US store by saved choice, language or time zone. Add `?choose` to see the picker. |
| `uk/index.html` | UK store: GBP, UK delivery copy, UK-only boxes. Generated. |
| `us/index.html` | US store: USD, US shipping copy, US-only boxes. Generated. |
| `images/` | Box, country, hero and product photos, shared by both stores. |
| `tools/` | Build and image scripts. `tools/products.json` is the product manifest. |

## Rebuilding after an edit

```bash
python3 tools/build_sites.py
```

The build wraps `src/site.html` with each store's metadata (title, description, canonical and `hreflang` links),
pins the store with `window.SITE`, and points asset paths one level up. Do not edit `index.html`, `uk/` or `us/`
directly: the next build replaces them. Store-specific copy lives in the `REGIONS` object inside `src/site.html`,
and the base URL for canonical links is `BASE_URL` at the top of the build script.

## Local preview

```bash
python3 -m http.server 8768
```

Then open http://localhost:8768/ for the landing page, or `/uk/` and `/us/` for a store.

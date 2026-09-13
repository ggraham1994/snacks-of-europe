# Image brief for Snacks of Europe

The storefront is one static page, `index.html`, plus the pictures under `images/`.
Every picture is referenced by an exact path, so any replacement must keep the same
file name, pixel size, format and (for hero cutouts) transparency. Replace the file and
the page picks it up; no HTML changes are needed.

## Brand look
- Box scenes use `eu-22.webp` as the fixed size reference: front panel x=110–1090,
  bottom y=850 on the 1200×900 canvas, rim y=605 at the sides dipping to y=650
  at the centre. Preserve product proportions when arranging the contents.
- Open cardboard box in the box's colour, front panel reading **<COUNTRY> EDITION** in
  large bold white uppercase on top, a thin white divider line, then **SNACKS OF EUROPE**
  in smaller white uppercase below (about half the top line's letter height). Keep a
  small red postage stamp on the panel's right, products standing inside and leaning outward.
  Apply the same lettering hierarchy to boxes appearing in lifestyle images.
- Background: the box colour mixed 86% towards white, with a soft radial highlight.
- Soft drop shadows under packs. No other text anywhere in the picture.
- Colours per box are in `tools/boxes.json` (`color`).

## Files
| Path | Size | Content |
|---|---|---|
| `images/<box>.webp` | 1200×900, opaque | Open box scene with the listed products. Boxes: `eu-22`, `pl-15`, `de-20`, `nl-18`, `be-16`, `it-16`, `fr-15`, `es-16`, `se-18`, `uk-classic`, `sub-italy` |
| `images/country-<xx>.webp` | 1200×900, opaque | Three listed products fanned on the tinted background. No box, no text |
| `images/coll-<name>.webp` | 1200×900, opaque | Same style as country tiles, grouped by collection |
| `images/hero/hero-<slug>.webp` | 720 px tall, transparent | One pack, straight on, cut out with no background or shadow |

The products in each picture, with a reference packshot URL for every one, are listed
in `tools/boxes.json`. Entries with `"style": "cluster"` are the country and collection
tiles; `"style": "cutouts"` is the hero set; everything else is a box scene.

## Rules
1. Reproduce the real packaging from the reference packshots. Do not invent products,
   logos, flavours or text. If a pack cannot be reproduced faithfully, leave that image
   unchanged rather than approximating it.
2. Generated lettering is limited to the two lines on the box panel. If the model cannot
   render them cleanly, generate the packs only and let `tools/build_box_images.py` draw
   the box, panel text and stamp: put your generated pack images in a folder, point the
   recipe entries' `image_url` at them (local paths work), and run
   `python3 tools/build_box_images.py --catalog tools/boxes.json --boxes tools/boxes.json --out images`.
   The script needs Pillow and numpy; `rembg` only if you use the `rembg` cutout method.
3. Keep every file under about 150 KB (WebP quality 84). Hero cutouts must keep alpha.
4. Verify by opening `index.html` in a browser: every image must load, fill its frame
   without letterboxing, and the hero packs must sit on the red background with no
   visible edges.
5. Commit to `main` with a message listing the images changed. GitHub Pages redeploys
   automatically within about a minute.

## Product cutouts (all-products page and build-a-box)
`tools/products.json` lists every product we stock: `id`, `ean`, `airtable` (record id in the EAN ID table),
display `name`, `country`, `cat`, and the exact `image` path the page loads, `images/products/<EAN>.webp`.
Produce one file per product at that path: the pack alone, straight on, transparent background, no shadow,
480 px on the longer side, WebP with alpha, under 60 KB. The page shows a placeholder until the file exists,
so partial batches are fine. Sources in order of preference: the product's Amazon listing main image
(the Airtable record's "AMZ URL" links to it), the Airtable "Product Image" attachment, or a new photo.
Never invent packaging: if no source exists, skip the product.

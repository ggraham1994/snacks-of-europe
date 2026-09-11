# Image brief for Snacks of Europe

The storefront is one static page, `index.html`, plus the pictures under `images/`.
Every picture is referenced by an exact path, so any replacement must keep the same
file name, pixel size, format and (for hero cutouts) transparency. Replace the file and
the page picks it up; no HTML changes are needed.

## Brand look
- Open cardboard box in the box's colour, front panel reading **SNACKS OF EUROPE** on the
  first line and **<COUNTRY> EDITION** on the second, a small red postage stamp on the
  panel's right, products standing inside and leaning outward.
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
